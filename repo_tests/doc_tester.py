import sys
from collections import defaultdict
from pathlib import Path
from typing import Set

from regex import regex

PYTHON_PATH_EXCLUDES = ["node_modules", "out"]
JS_PATH_EXCLUDES = ["node_modules", "venv", "out"]
PYTHON_ENV_VAR_REGEXES = [
    r"environ\.get\(['\"]([^'\",)]+)['\"]",
    r"environ\[\(['\"]([^'\",)]+)['\"]",
    r"os\.getenv\(['\"]([^'\",)]+)['\"]",
]
JS_ENV_VAR_REGEXES = [
    r"process\.env\.([A-Z0-9a-z_]+)",
    r"process\.env[['\"]([A-Z0-9a-z_]+)",
    r"key: '([A-Z0-9a-z_]+)",
]
IGNORED_JS_ENV_VARS = {
    "envVariableName",
    "DEBUG",
    "NODE_ENV",
    "column1Key",
    "MJML_FILE_SEARCH_ROOT",
    "JEST_JUNIT_OUTPUT_DIR",
}

ENV_VARS_NOT_WANTED_IN_ENV_EXAMPLE = {
    "EMAIL_SMPT_USE_TLS",  # A typo old backwards compat variable used in base.py
    "CELERY_BEAT_MAX_LOOP_INTERVAL",  # Very internal value, not for users
    "RUN_MAIN",  # Shouldn't be set by users
    "BASEROW_BACKEND_DEBUGGER_ENABLED",  # .dev.yml only
    "BASEROW_BACKEND_DEBUGGER_PORT",  # .dev.yml only
}
ENV_VARS_NOT_WANTED_IN_CONFIGURATION_MD = {
    "EMAIL_SMPT_USE_TLS",  # A typo old backwards compat variable used in base.py
    "CELERY_BEAT_MAX_LOOP_INTERVAL",  # Very internal value, not for users
    "RUN_MAIN",  # Shouldn't be set by users
    "BASEROW_BACKEND_DEBUGGER_ENABLED",  # .dev.yml only
    "BASEROW_BACKEND_DEBUGGER_PORT",  # .dev.yml only
    "FEATURE_FLAGS",  # devs only
    "BASEROW_GROUP_STORAGE_USAGE_ENABLED",  # saas only
    "BASEROW_COUNT_ROWS_ENABLED",  # saas only
}
LEGACY_ENV_VARS_WITHOUT_PREFIX = {
    "REDIS_PORT",
    "AWS_S3_CUSTOM_DOMAIN",
    "PUBLIC_BACKEND_URL",
    "EMAIL_SMTP_HOST",
    "FEATURE_FLAGS",
    "EMAIL_SMTP_USER",
    "AWS_S3_ENDPOINT_URL",
    "SECRET_KEY",
    "AWS_S3_REGION_NAME",
    "AWS_STORAGE_BUCKET_NAME",
    "EMAIL_SMTP_USE_TLS",
    "DONT_UPDATE_FORMULAS_AFTER_MIGRATION",
    "PRIVATE_BACKEND_URL",
    "REDIS_HOST",
    "INITIAL_TABLE_DATA_LIMIT",
    "REDIS_PASSWORD",
    "MEDIA_ROOT",
    "EMAIL_SMTP_PORT",
    "DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS",
    "SYNC_TEMPLATES_ON_STARTUP",
    "DATABASE_HOST",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "MEDIA_URL",
    "REDIS_USER",
    "EMAIL_SMTP_PASSWORD",
    "REDIS_PROTOCOL",
    "EMAIL_SMTP",
    "AWS_ACCESS_KEY_ID",
    "ADDITIONAL_APPS",
    "DATABASE_NAME",
    "BATCH_ROWS_SIZE_LIMIT",
    "AWS_SECRET_ACCESS_KEY",
    "DATABASE_PORT",
    "MINUTES_UNTIL_ACTION_CLEANED_UP",
    "FROM_EMAIL",
    "DATABASE_URL",
    "DOWNLOAD_FILE_VIA_XHR",
    "PUBLIC_WEB_FRONTEND_URL",
    "HOURS_UNTIL_TRASH_PERMANENTLY_DELETED",
    "ADDITIONAL_MODULES",
}


def run():
    failures = []
    run_env_var_checks(failures)
    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        sys.exit(1)
    else:
        print("Success! No docs problems found")


def run_env_var_checks(failures):
    """
    Runs various crude regex based checks making sure if new environment variables are
    introduced we reference them in the right places.
    """

    _check_python_env_vars(failures)
    _check_javascript_env_vars(failures)


def _check_javascript_env_vars(failures):
    js_env_vars = process_js_env_vars()

    env_example_vars = process_env_example_file()
    _check_vs_env_example(env_example_vars, failures, js_env_vars, "javascript")

    check_compose_vars(
        failures, js_env_vars, "docker-compose.yml", "javascript", "web-frontend"
    )
    check_compose_vars(
        failures,
        js_env_vars,
        "docker-compose.local-build.yml",
        "javascript",
        "web-frontend",
    )

    check_vars_against_configuration_md_config(
        failures,
        js_env_vars,
        "javascript",
    )


def _check_python_env_vars(failures):
    python_env_vars = process_python_env_vars()

    env_example_vars = process_env_example_file()
    _check_vs_env_example(env_example_vars, failures, python_env_vars, "python")

    _check_compose_files(failures, python_env_vars, "python", "backend")

    check_vars_against_configuration_md_config(
        failures,
        python_env_vars,
        "python",
    )


def _check_compose_files(failures, python_env_vars, name, service):
    check_compose_vars(failures, python_env_vars, "docker-compose.yml", name, service)
    check_compose_vars(
        failures, python_env_vars, "docker-compose.no-caddy.yml", name, service
    )
    check_compose_vars(
        failures, python_env_vars, "docker-compose.local-build.yml", name, service
    )


def _check_vs_env_example(env_example_vars, failures, found_vars, name):
    missing_vars = []
    no_prefix_vars = []
    for var in found_vars - ENV_VARS_NOT_WANTED_IN_ENV_EXAMPLE:
        if not var.startswith("BASEROW_") and var not in LEGACY_ENV_VARS_WITHOUT_PREFIX:
            no_prefix_vars.append(var)
        if var not in env_example_vars:
            missing_vars.append(var)
    if missing_vars:
        failures.append(
            f"ERROR: You have added the following env vars as {name} env vars "
            f"but have not added them to the `.env.example` in the root of the repo. "
            f"Please add them to this file "
            f"in the group of env variables that makes the most sense "
            f"so docker-compose users can see all the "
            f"available env vars. If you think a variable should never be set by a"
            f"user instead add it to the `ENV_VARS_NOT_WANTED_IN_ENV_EXAMPLE` variable "
            f"found in `repo_tests/doc_tester.py`. The missing env vars are:\n# "
            + "=\n# ".join(missing_vars)
            + "="
        )
    if no_prefix_vars:
        failures.append(
            f"ERROR: You have added the following env vars as {name} env vars "
            f"but they are not prefixed with BASEROW_. All new Baserow env vars should "
            f"be prefixed with BASEROW_ to reduce collision chance with a users other "
            f"env vars and for consistency sake. Please rename them to start with "
            f"BASEROW_\n" + "\n".join([f"'{v}'," for v in no_prefix_vars])
        )


def check_compose_vars(failures, found_vars, filename, name, service):
    missing_docker_compose_vars = []
    docker_compose_env_vars = process_docker_compose_file(filename)
    for var in found_vars - ENV_VARS_NOT_WANTED_IN_ENV_EXAMPLE:
        if var not in docker_compose_env_vars:
            missing_docker_compose_vars.append(var)
    if missing_docker_compose_vars:
        failures.append(
            f"ERROR: You have added the following env vars as {name} env vars "
            f"but have not added them to the `{filename}` in the root of the repo. "
            f"Please add them to this file "
            f"in backend-vars section "
            f"so this variable can be set and passed through to the {service} service "
            f"If you think a variable should never be set by a "
            f"user instead add it to the `ENV_VARS_NOT_WANTED_IN_ENV_EXAMPLE` variable "
            f"found in `repo_tests/doc_tester.py`. The missing env vars are:\n"
            + ":\n".join(missing_docker_compose_vars)
            + ":"
        )


def check_vars_against_configuration_md_config(failures, found_vars, name):
    missing_vars = []
    vars_found_in_configuration_md = process_configuration_md()
    for var in found_vars - ENV_VARS_NOT_WANTED_IN_CONFIGURATION_MD:
        if var not in vars_found_in_configuration_md:
            escaped_for_md = var.replace("_", "\\_")
            missing_vars.append(
                f"| {escaped_for_md} | TODO description | TODO default |"
            )
    if missing_vars:
        failures.append(
            f"ERROR: You have added the following env vars as {name} env vars "
            f"but have not added them to the 'docs/installation/configuration.md' doc "
            f"file."
            f"Please add them to this file in the correct section making sure to escape"
            f" underscores with a \\."
            f"If you think a variable doesnt need to be in docs then "
            f"instead add it to the `ENV_VARS_NOT_WANTED_IN_CONFIGURATION_MD` variable "
            f"found in `repo_tests/doc_tester.py`. The missing env vars are (they "
            f"are formatted and escaped so you can paste straight into the md "
            f"files table!):\n" + "\n".join(missing_vars)
        )


def process_python_env_vars() -> Set[str]:
    python_env_vars = defaultdict(lambda: 0)
    for path in Path(".").rglob("*.py"):
        if all(exclude not in path.parts for exclude in PYTHON_PATH_EXCLUDES):
            with open(path, "r") as python_file:
                python_contents = python_file.read()
                for r in PYTHON_ENV_VAR_REGEXES:
                    for m in regex.findall(r, python_contents):
                        python_env_vars[m] += 1
    return set(python_env_vars.keys())


def process_js_env_vars() -> Set[str]:
    js_env_vars = defaultdict(lambda: 0)
    for path in list(Path(".").rglob("*.js")) + list(Path(".").rglob("*.vue")):
        if all(exclude not in path.parts for exclude in JS_PATH_EXCLUDES):
            with open(path, "r") as js_file:
                js_contents = js_file.read()
                for r in JS_ENV_VAR_REGEXES:
                    for m in regex.findall(r, js_contents):
                        js_env_vars[m] += 1
    return set(js_env_vars.keys()) - IGNORED_JS_ENV_VARS


def process_env_example_file():
    with open(".env.example", "r") as env_example_file:
        env_example_contents = env_example_file.read()
        return set(
            [
                x.strip()
                for x in regex.findall(r"#?\s*([A-Z0-9_]+)\=", env_example_contents)
            ]
        )


def process_docker_compose_file(file_name):
    with open(file_name, "r") as file:
        return set(
            [x.strip()[:-1] for x in regex.findall(r"[A-Z0-9_]+\:", file.read())]
        )


def process_configuration_md():
    with open("docs/installation/configuration.md", "r") as config_md_file:
        config_md_contents = config_md_file.read()
        matches = regex.findall(r"\|\s*([A-Z0-9_\\]+)\s*\|", config_md_contents)
        return set([x.replace("\\_", "_") for x in matches])


if __name__ == "__main__":
    run()
