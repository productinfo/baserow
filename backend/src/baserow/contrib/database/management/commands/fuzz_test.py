import csv
import os
import random
import string
import traceback
from decimal import Decimal
from hashlib import sha1
from random import randint
from typing import List, Optional, cast, Dict, Any

import pytz
import sys
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework.status import HTTP_200_OK
from tqdm import tqdm

from baserow.contrib.database.airtable.constants import AIRTABLE_BASEROW_COLOR_MAPPING
from baserow.contrib.database.api.rows.serializers import (
    get_row_serializer_class,
    RowSerializer,
)
from baserow.contrib.database.api.utils import get_include_exclude_field_ids
from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.field_types import (
    LookupFieldType,
    LinkRowFieldType,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.mixins import DATE_FORMAT
from baserow.contrib.database.fields.models import (
    RATING_STYLE_CHOICES,
    NUMBER_MAX_DECIMAL_PLACES,
    LinkRowField,
    Field,
)
from baserow.contrib.database.fields.registries import field_type_registry, FieldType
from baserow.contrib.database.management.commands.fill_table_rows import fill_table_rows
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.registries import row_metadata_registry
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import (
    FILTER_TYPES,
    GridView,
    View,
    ViewFilter,
)
from baserow.contrib.database.views.registries import (
    view_type_registry,
    view_aggregation_type_registry,
    ViewType,
    view_filter_type_registry,
    ViewFilterType,
)
from baserow.contrib.database.views.view_filters import (
    EqualViewFilterType,
    NotEqualViewFilterType,
    FilenameContainsViewFilterType,
    HasFileTypeViewFilterType,
    ContainsViewFilterType,
    ContainsNotViewFilterType,
    LengthIsLowerThanViewFilterType,
    HigherThanViewFilterType,
    LowerThanViewFilterType,
    DateEqualViewFilterType,
    DateBeforeViewFilterType,
    DateAfterViewFilterType,
    DateEqualsTodayViewFilterType,
    DateEqualsDaysAgoViewFilterType,
    DateEqualsCurrentMonthViewFilterType,
    DateNotEqualViewFilterType,
    DateEqualsDayOfMonthViewFilterType,
    SingleSelectEqualViewFilterType,
    BooleanViewFilterType,
    LinkRowHasViewFilterType,
    LinkRowHasNotViewFilterType,
    MultipleSelectHasViewFilterType,
    MultipleSelectHasNotViewFilterType,
)
from baserow.contrib.database.views.view_types import (
    GridViewType,
    GalleryViewType,
    FormViewType,
)
from baserow.core.handler import CoreHandler
from baserow.core.management.utils import (
    run_command_concurrently,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.handler import UserHandler
from baserow.core.user_files.models import UserFile
from baserow.core.utils import random_string
from baserow.test_utils.fixtures import UserFixtures

User = get_user_model()


class Command(BaseCommand):
    help = "Runs a fuzz test over Baserow."

    def add_arguments(self, parser):
        parser.add_argument(
            "num_runs",
            nargs="?",
            type=int,
            help="The number of individual fuzz runs to do per concurrent sub process",
            default=1,
        )
        parser.add_argument(
            "--reports-folder",
            type=str,
            help="The folder to write fuzz test reports into",
            default=None,
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            help="How many concurrent processes should be used to create tables.",
            default=1,
        )
        parser.add_argument(
            "--recreate-seed",
            type=int,
            help="If set the seed will be recreated in the provided user account",
            default=None,
        )
        parser.add_argument(
            "--user-email",
            type=str,
            help="The user account to recreate the email in",
            default=None,
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Whether to log debug lines",
            default=False,
        )

    def handle(self, *args, **options):
        num_runs = options["num_runs"]
        report_folder = options["reports_folder"]
        concurrency = options["concurrency"]
        recreate_seed = options["recreate_seed"]
        user_email = options["user_email"]
        debug = options["debug"]
        if recreate_seed:
            _recreate_seed(recreate_seed, user_email, debug)
        else:
            _run_fuzzer(concurrency, num_runs, report_folder, debug)
        self.stdout.write(
            self.style.SUCCESS(
                f"{num_runs} runs of fuzzing have been run with concurrency {concurrency}!."
            )
        )


def _run_fuzzer(concurrency: int, num_runs: int, report_folder_name: str, debug: bool):
    if not report_folder_name:
        now = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_folder_name = f"fuzz_reports_{now}"
    report_folder_path = os.path.join(os.getcwd(), report_folder_name)
    if not os.path.exists(report_folder_path):
        os.makedirs(report_folder_path)
    if concurrency == 1:
        run_many_fuzz_tests_and_report(report_folder_name, num_runs)
    else:
        command = [
            "./baserow",
            "fuzz_test",
            str(num_runs),
            "--reports-folder",
            str(report_folder_name),
            "--concurrency",
            str(1),
        ]
        if debug:
            command.append("--debug")
        run_command_concurrently(
            command,
            concurrency,
        )
    print(f"Successfully fuzzed! Check {report_folder_path} for results.")


def _recreate_seed(recreate_seed, user_email, debug):
    if not user_email:
        raise CommandError("--user-email must be set when using --recreate-seed")
    else:
        print(f"Recreating seed {recreate_seed} for {user_email}")
        user = User.objects.get(email=user_email)
        database = Fuzzer(seed=recreate_seed, user=user, debug=debug).fuzz(
            run_checks=True
        )

        # noinspection PyUnresolvedReferences
        print(
            f"Access the database at "
            f"{settings.PUBLIC_WEB_FRONTEND_URL}/database/"
            f"{database.id}/table/{database.table_set.first().id}"
        )


def pid():
    return os.getpid()


def run_many_fuzz_tests_and_report(report_folder: str, num_runs: int):
    print(f"Fuzzing into {report_folder} on pid: {pid()}")

    for i in tqdm(range(num_runs), desc=f"{pid()} running..."):
        unique_run_id = str(pid()) + "-run-" + str(i)
        process_name = report_folder + "-pid-" + unique_run_id

        chosen_seed = int(sha1(process_name.encode()).hexdigest(), 16)

        email = process_name + "@gmail.com"
        password = "fuzzpassword"
        user = UserHandler().create_user(process_name, email, password)
        print(
            f"Making a user called {email} with password "
            f"{password} to put all fuzz groups into"
        )
        with open(os.path.join(os.getcwd(), report_folder, "runs.txt"), "a") as file:
            file.write("run_user_email=" + email + " - seed=" + str(chosen_seed) + "\n")
        try:
            Fuzzer(chosen_seed, user).fuzz(delete_at_end=True)
        except Exception as e:
            with open(
                os.path.join(os.getcwd(), report_folder, "fails.csv"), "a"
            ) as file:
                exc = traceback.format_exc()
                wr = csv.writer(file, quoting=csv.QUOTE_ALL)
                wr.writerow([email, str(chosen_seed), exc])
                file.write(f'{email},{str(chosen_seed)},"{exc}"\n')
            if (
                isinstance(e, KeyboardInterrupt)
                or isinstance(e, SystemExit)
                or isinstance(e, SystemError)
            ):
                raise e


# noinspection PyMethodMayBeStatic
class Fuzzer:
    def __init__(self, seed: int, user: User, debug: bool):
        self.seed = seed
        self.user = user
        self.fake = Faker()
        self.debug = debug
        random.seed(seed)
        self.fake.seed_instance(seed)

    def fuzz(
        self,
        run_checks=True,
        delete_at_end=False,
    ):
        database = self._setup_database()
        try:
            tables = self._setup_tables(database)

            if run_checks:
                for table in tables:
                    for view in table.view_set.all():
                        self.check_can_serialize_all_rows(view.id)
        finally:
            if delete_at_end:
                trash_entry = TrashHandler().trash(
                    self.user, database.group, None, database.group
                )
                trash_entry.should_be_permanently_deleted = True
                trash_entry.save()
                TrashHandler().permanently_delete_marked_trash()
        return database

    def _create_view_options(self, fields: List[Field], views: List[View]):
        for view in tqdm(views, desc=f"{pid()}: Setting view options"):
            shuffled_fields = list(fields)
            random.shuffle(shuffled_fields)
            view_field_options = dict()
            view_type: ViewType = view_type_registry.get_by_model(view)
            for i, field in enumerate(shuffled_fields):
                random_field_options = {
                    "order": i,
                }
                if randint(0, 3) == 0 and view_type.can_aggregate_field:
                    valid_aggregations = []
                    agg_to_raw = {
                        "min": "min",
                        "max": "max",
                        "sum": "sum",
                        "average": "average",
                        "median": "median",
                        "std_dev": "std_dev",
                        "variance": "variance",
                        "min_date": "min",
                        "max_date": "max",
                        "empty_count": "empty_count",
                        "not_empty_count": "empty_count",
                        "checked_count": "empty_count",
                        "not_checked_count": "empty_count",
                        "empty_percentage": "empty_count",
                        "not_empty_percentage": "empty_count",
                        "checked_percentage": "empty_count",
                        "not_checked_percentage": "empty_count",
                        "unique_count": "unique_count",
                    }
                    for agg in view_aggregation_type_registry.get_all():
                        if agg.field_is_compatible(field) and agg.type in agg_to_raw:
                            valid_aggregations.append(agg)
                    if valid_aggregations:
                        random_agg_type = random.choice(valid_aggregations).type
                        random_field_options["aggregation_raw_type"] = random_agg_type
                        random_field_options["aggregation_type"] = agg_to_raw[
                            random_agg_type
                        ]
                view_field_options[field.id] = random_field_options
                if view_type.type == GridViewType.type:
                    if randint(0, 5) == 0:
                        random_field_options["hidden"] = True
                    else:
                        random_field_options["hidden"] = False
                elif view_type.type == FormViewType.type:
                    # TODO fuzz
                    pass
                elif view_type.type == GalleryViewType.type:
                    if randint(0, 5) == 0:
                        random_field_options["hidden"] = True
                    else:
                        random_field_options["hidden"] = False
                else:
                    pass
                ViewHandler().update_field_options(
                    view, field_options=view_field_options, user=self.user
                )

    def _create_random_view_filters(self, views: List[View], fields: List[Field]):
        view_filters = []
        for view in tqdm(views, desc=f"{pid()}: Creating random filters sorts"):
            view_type = view_type_registry.get_by_model(view)
            if view_type.can_filter:
                for field in self._shuffle_dupe_and_slice_fields_randomly(fields):
                    cache = {}
                    num_filters = randint(0, 4)
                    valid_view_filters = []
                    for view_filter_type in view_filter_type_registry.get_all():
                        if view_filter_type.field_is_compatible(field):
                            valid_view_filters.append(view_filter_type)
                    if not valid_view_filters:
                        continue
                    for i in range(num_filters):
                        random_type = random.choice(valid_view_filters)
                        view_filters.append(
                            self._make_random_view_filter(
                                cache,
                                field,
                                random_type,
                                view,
                            )
                        )
            return view_filters

    def _shuffle_dupe_and_slice_fields_randomly(
        self, fields: List[Field]
    ) -> List[Field]:
        max_filters = (
            randint(0, len(fields) * 2) if randint(0, 5) == 0 else randint(0, 5)
        )
        shuffled_fields = list(fields)
        random.shuffle(shuffled_fields)
        repeated_fields = []
        for field in shuffled_fields:
            for i in range(randint(0, 4)):
                repeated_fields.append(field)
        random.shuffle(repeated_fields)
        repeated_fields = repeated_fields[0:max_filters]
        return repeated_fields

    def _make_random_view_filter(
        self,
        cache: Dict[str, Any],
        field: Field,
        view_filter_type: ViewFilterType,
        view: View,
    ) -> ViewFilter:
        field_type = field_type_registry.get_by_model(field)
        table = field.table
        if randint(0, 5) == 0:
            random_value = ""
        elif view_filter_type.type in [
            EqualViewFilterType.type,
            NotEqualViewFilterType.type,
            ContainsViewFilterType.type,
            ContainsNotViewFilterType.type,
            SingleSelectEqualViewFilterType.type,
        ]:
            random_value = field_type.random_value(field, self.fake, cache)
            if isinstance(random_value, str):
                if randint(0, 2) == 0:
                    random_value = random_string(1)
                elif randint(0, 4) == 0:
                    random_value = self.random_substr(random_value)
        elif view_filter_type.type == FilenameContainsViewFilterType.type:
            if randint(0, 2) == 0:
                random_value = self.random_string(1)
            else:
                random_value = self.random_substr(
                    UserFile.objects.order("?").first().original_name
                )
        elif view_filter_type.type == HasFileTypeViewFilterType.type:
            if randint(0, 1) == 0:
                random_value = "image"
            else:
                random_value = "document"
        elif view_filter_type.type in [
            LengthIsLowerThanViewFilterType.type,
        ]:
            random_value = randint(0, sys.maxsize)
        elif view_filter_type.type in [DateEqualsDaysAgoViewFilterType.type]:
            random_value = (
                self.random_tz() + "?" + str(randint(-sys.maxsize, sys.maxsize))
            )
        elif view_filter_type.type in [
            HigherThanViewFilterType.type,
            LowerThanViewFilterType.type,
        ]:
            size = randint(1, 10)
            random_value = Decimal(random.randrange(0, sys.maxsize)) / size
        elif view_filter_type.type in [
            DateEqualsDayOfMonthViewFilterType.type,
        ]:
            random_value = randint(1, 31)
        elif view_filter_type.type in [
            DateEqualViewFilterType.type,
            DateNotEqualViewFilterType.type,
            DateBeforeViewFilterType.type,
            DateAfterViewFilterType.type,
        ]:
            random_value = self.fake.date_time()
        elif view_filter_type.type in [
            DateEqualsTodayViewFilterType.type,
            DateEqualsCurrentMonthViewFilterType.type,
        ]:
            random_value = ""
        elif view_filter_type.type in [BooleanViewFilterType.type]:
            if randint(0, 5) == 1:
                random_value = self.random_string(255)
            elif randint(0, 1) == 1:
                random_value = "t"
            else:
                random_value = "f"
        elif view_filter_type.type in [
            LinkRowHasViewFilterType.type,
            LinkRowHasNotViewFilterType.type,
            MultipleSelectHasViewFilterType.type,
            MultipleSelectHasNotViewFilterType.type,
        ]:
            model = table.get_model()
            random_value = random.choice(
                list(
                    model.objects.values_list(f"{field.db_column}__id", flat=True).all()
                )
            )

        else:
            random_value = ""
        return ViewHandler().create_filter(
            self.user, view, field, view_filter_type.type, value=str(random_value)
        )

    def random_substr(self, random_value):
        start = randint(0, len(random_value) - 1)
        length = randint(1, len(random_value) - start - 1)
        random_value = random_value[start : start + length]
        return random_value

    def _setup_tables(self, database: Database) -> List[Table]:
        num_tables = randint(1, 5)
        tables = []
        for _ in tqdm(range(num_tables), desc=f"{pid()}: Creating tables"):
            table = TableHandler().create_table(
                self.user,
                database,
                self.random_string(randint(1, 255)),
                fill_example=False,
            )
            fields = self._create_random_fields(table, tables)
            views = self._create_random_views(table)
            self._create_view_options(fields, views)
            tables.append(table)

            fill_table_rows(randint(0, 1000), table, fake=self.fake)
            self._create_random_view_filters(views, fields)
        return tables

    def _create_random_fields(self, table: Table, tables: List[Table]) -> List[Field]:
        num_fields = randint(1, 25)
        ran_field_types = []
        for i in range(num_fields):
            ran_field_types.append(random.choice(list(field_type_registry.get_all())))
        # 25% chance we always have a link row
        if randint(0, 4) == 0:
            ran_field_types.append(field_type_registry.get(LinkRowFieldType.type))
        primary_made = False
        fields = []
        for field_type in tqdm(
            ran_field_types, desc=f"{pid()}: Creating fields in table {table.id}"
        ):
            if not primary_made and field_type.can_be_primary_field:
                primary_made = True
                primary = True
            else:
                primary = False
            field = self.create_random_field(
                field_type,
                table,
                tables,
                fields,
                primary,
            )
            if field is not None:
                fields.append(field)
        return fields

    def _setup_database(self) -> Database:
        unique_run_id = str(self.seed)
        group_user = CoreHandler().create_group(self.user, unique_run_id)
        group = group_user.group
        return cast(
            Database,
            CoreHandler().create_application(
                self.user, group, "database", unique_run_id
            ),
        )

    def get_rows(self, table, user):
        from rest_framework.test import APIClient

        # Make an authenticated request to the view...
        client = APIClient()
        token = UserFixtures().generate_token(user)
        url = reverse(
            "api:database:views:grid:list",
            kwargs={"view_id": table.view_set.first().id},
        )
        response = client.get(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

        if response.status_code != HTTP_200_OK:
            print(response)
            raise Exception(response.json())

    def _create_random_views(self, table):
        views = []
        num_views = randint(1, 25)
        for _ in tqdm(range(num_views), desc=f"{pid()}: Creating views in {table.id}"):
            view_type = random.choice(
                list(view_type_registry.get_all())
                + [view_type_registry.get(GridViewType.type) for _ in range(6)]
            )
            kwargs = {
                "filter_type": random.choice([x for x, _ in FILTER_TYPES]),
                "filters_disabled": randint(0, 5) == 0,
                "public": self.randbool(),
                "public_view_password": self.random_string(randint(1, 128)),
            }
            if view_type.type == GridViewType.type:
                pass
            elif view_type.type == GalleryViewType.type:
                pass
            elif view_type.type == FormViewType.type:
                pass
            else:
                continue
            views.append(
                ViewHandler().create_view(
                    self.user,
                    table,
                    type_name=view_type.type,
                    name=self.random_string(randint(1, 255)),
                    **kwargs,
                )
            )
        return views

    def create_random_field(
        self,
        field_type: FieldType,
        table: Table,
        tables: List[Table],
        fields: List[Field],
        primary: bool,
    ) -> Optional[Field]:

        field_kwargs = construct_all_possible_field_kwargs(
            random.choice(tables or [None]), None, None
        )[field_type.type][0]
        new_field_kwargs = {}

        if len(tables) == 0 and field_type.type in [
            LookupFieldType.type,
            LinkRowFieldType.type,
        ]:
            # There are no tables to link to yet
            return None
        link_fields = [f for f in fields if isinstance(f, LinkRowField)]
        if len(link_fields) == 0 and field_type.type == LookupFieldType.type:
            return None
        if len(link_fields) > 0:
            random_link_field = random.choice(link_fields)
        else:
            random_link_field = None

        for key, value in field_kwargs.items():
            if key == "name":
                new_field_kwargs["name"] = self.random_string(randint(1, 255))
            elif key == "style":
                new_field_kwargs[key] = random.choice(
                    [x for x, _ in RATING_STYLE_CHOICES]
                )
            elif key == "number_decimal_places":
                new_field_kwargs[key] = randint(0, NUMBER_MAX_DECIMAL_PLACES)
            elif key == "max_value":
                new_field_kwargs[key] = randint(1, 10)
            elif key == "color":
                new_field_kwargs[key] = random.choice(
                    list(AIRTABLE_BASEROW_COLOR_MAPPING.values())
                )
            elif key == "date_format":
                new_field_kwargs[key] = random.choice(list(DATE_FORMAT.keys()))
            elif key == "timezone":
                new_field_kwargs[key] = self.random_tz()
            elif key == "formula":
                new_field_kwargs[key] = "1"
            elif key == "through_field_name":
                new_field_kwargs[key] = random_link_field.name
            elif key == "target_field_name":
                valid_targets = []
                for f in random_link_field.link_row_table.field_set.all():
                    specific = f.specific
                    t = field_type_registry.get_by_model(
                        specific
                    ).to_baserow_formula_type(specific)
                    if t.is_valid:
                        valid_targets.append(f.name)
                new_field_kwargs[key] = random.choice(valid_targets)

            elif key == "select_options":
                options = []
                for i in range(randint(0, 30)):
                    options.append(
                        {
                            "id": i,
                            "value": self.random_string(randint(1, 255)),
                            "color": random.choice(
                                list(AIRTABLE_BASEROW_COLOR_MAPPING.values())
                            ),
                        }
                    )
                new_field_kwargs[key] = options
            elif key == "link_row_table":
                new_field_kwargs[key] = random.choice(tables)
            else:
                new_field_kwargs[key] = self.randomize(key, field_type, value)
            new_field_kwargs["primary"] = primary

        if primary:
            return FieldHandler().update_field(
                self.user,
                table.field_set.get(primary=True).specific,
                new_type_name=field_type.type,
                **new_field_kwargs,
            )
        else:
            return FieldHandler().create_field(
                self.user, table, field_type.type, **new_field_kwargs
            )

    def random_tz(self):
        choice = random.choice(pytz.all_timezones)
        return choice

    def random_string(self, length: int):
        r = randint(0, 10)
        if r < 1:
            # Update this to include code point ranges to be sampled
            include_ranges = [
                (0x0021, 0x0021),
                (0x0023, 0x0026),
                (0x0028, 0x007E),
                (0x00A1, 0x00AC),
                (0x00AE, 0x00FF),
                (0x0100, 0x017F),
                (0x0180, 0x024F),
                (0x2C60, 0x2C7F),
                (0x16A0, 0x16F0),
                (0x0370, 0x0377),
                (0x037A, 0x037E),
                (0x0384, 0x038A),
                (0x038C, 0x038C),
            ]

            alphabet = [
                chr(code_point)
                for current_range in include_ranges
                for code_point in range(current_range[0], current_range[1] + 1)
            ]
            return "".join(random.choice(alphabet) for _ in range(length))
        elif r < 7:
            return self.fake.name()
        else:
            return "".join(
                random.choice(string.ascii_letters + string.digits)
                for _ in range(length)
            )

    def randomize(self, key, field_type, value):
        if type(value) is str:
            return self.random_string(randint(1, 255))
        elif type(value) is int:
            return randint(0, sys.maxsize)
        elif type(value) is bool:
            return self.randbool()
        else:
            raise Exception(
                f"Unknown key {key}, {field_type.type}, {value}, {type(value)}"
            )

    # noinspection SpellCheckingInspection
    def randbool(self):
        return bool(random.getrandbits(1))

    def check_can_serialize_all_rows(self, view_id: int):
        search = None
        include_fields = None
        exclude_fields = None
        view_handler = ViewHandler()
        try:
            view = view_handler.get_view(view_id, GridView)
        except ViewDoesNotExist:
            return

        if self.debug:
            print(
                f"checking can serialize all rows for view {view_id} in table "
                f"{view.table.id} called {view.name}"
            )
        print(
            f"Access the table at "
            f"{settings.PUBLIC_WEB_FRONTEND_URL}/database/"
            f"{view.table.database.id}/table/{view.table.id}"
        )

        # noinspection DuplicatedCode
        view_type = view_type_registry.get_by_model(view)

        view.table.database.group.has_user(
            self.user, raise_error=True, allow_if_template=True
        )
        field_ids = get_include_exclude_field_ids(
            view.table, include_fields, exclude_fields
        )

        model = view.table.get_model()
        queryset = view_handler.get_queryset(view, search, model)

        serializer_class = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            field_ids=field_ids,
        )
        response_data = self._scan_find(queryset, serializer_class)

        # print(f"serialized {len(response_data)} rows")
        response_dict = {"data": response_data}

        # noinspection PyProtectedMember
        context = {"fields": [o["field"] for o in model._field_objects.values()]}
        serializer_class = view_type.get_field_options_serializer_class(
            create_if_missing=True
        )
        response_dict.update(**serializer_class(view, context=context).data)

        row_metadata = row_metadata_registry.generate_and_merge_metadata_for_rows(
            view.table, (row.id for row in queryset)
        )
        response_dict.update(row_metadata=row_metadata)

        return response_dict

    def _scan_find(self, queryset, serializer_class):
        try:
            serializer = serializer_class(queryset, many=True)
            response_data = serializer.data
            return response_data
        except Exception as e:
            print(f"Scanning down {queryset.query} to find failed row due to {e}")
            if self.debug:
                for row in queryset.all():
                    print(f"Trying {row.id}")
                    serializer_class(row)
            else:
                raise e
