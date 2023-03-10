import pytest

from rest_framework import status, serializers
from rest_framework.exceptions import APIException
from rest_framework.serializers import CharField

from baserow.core.models import Group
from baserow.core.registry import (
    Instance, Registry, CustomFieldsInstanceMixin, ModelInstanceMixin
)
from baserow.api.v0.utils import (
    validate_data, validate_data_custom_fields, get_serializer_class
)


class TemporaryException(Exception):
    pass


class TemporarySerializer(serializers.Serializer):
    field_1 = serializers.CharField()
    field_2 = serializers.ChoiceField(choices=('choice_1', 'choice_2'))


class TemporaryInstance(CustomFieldsInstanceMixin, ModelInstanceMixin, Instance):
    pass


class TemporaryInstanceType1(TemporaryInstance):
    type = 'temporary_1'
    model_class = Group


class TemporaryInstanceType2(TemporaryInstance):
    type = 'temporary_2'
    model_class = Group
    serializer_field_names = ['name']
    serializer_field_overrides = {
        'name': serializers.IntegerField()
    }


class TemporaryTypeRegistry(Registry):
    name = 'temporary'


def test_validate_data():
    with pytest.raises(APIException) as api_exception_1:
        validate_data(TemporarySerializer, {'field_1': 'test'})

    assert api_exception_1.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_1.value.detail['detail']['field_2'][0]['error'] == \
           'This field is required.'
    assert api_exception_1.value.detail['detail']['field_2'][0]['code'] == 'required'
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_2:
        validate_data(
            TemporarySerializer,
            {'field_1': 'test', 'field_2': 'wrong'}
        )

    assert api_exception_2.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_2.value.detail['detail']['field_2'][0]['error'] == \
           '"wrong" is not a valid choice.'
    assert api_exception_2.value.detail['detail']['field_2'][0]['code'] == \
           'invalid_choice'
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    validated_data = validate_data(
        TemporarySerializer,
        {'field_1': 'test', 'field_2': 'choice_1'}
    )
    assert validated_data['field_1'] == 'test'
    assert validated_data['field_2'] == 'choice_1'
    assert len(validated_data.items()) == 2


def test_validate_data_custom_fields():
    registry = TemporaryTypeRegistry()
    registry.register(TemporaryInstanceType1())
    registry.register(TemporaryInstanceType2())

    with pytest.raises(APIException) as api_exception:
        validate_data_custom_fields('NOT_EXISTING', registry, {})

    assert api_exception.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception.value.detail['detail']['type'][0]['error'] == \
           '"NOT_EXISTING" is not a valid choice.'
    assert api_exception.value.detail['detail']['type'][0]['code'] == 'invalid_choice'
    assert api_exception.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_2:
        validate_data_custom_fields('temporary_2', registry, {})

    assert api_exception_2.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_2.value.detail['detail']['name'][0]['error'] == \
           'This field is required.'
    assert api_exception_2.value.detail['detail']['name'][0]['code'] == 'required'
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_3:
        validate_data_custom_fields('temporary_2', registry, {'name': 'test1'})

    assert api_exception_3.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_3.value.detail['detail']['name'][0]['error'] == \
           'A valid integer is required.'
    assert api_exception_3.value.detail['detail']['name'][0]['code'] == 'invalid'
    assert api_exception_3.value.status_code == status.HTTP_400_BAD_REQUEST

    data = validate_data_custom_fields('temporary_2', registry, {'name': 123})
    assert data['name'] == 123


@pytest.mark.django_db
def test_get_serializer_class(data_fixture):
    group = data_fixture.create_group(name='Group 1')

    group_serializer = get_serializer_class(Group, ['name'])(group)
    assert group_serializer.data == {'name': 'Group 1'}
    assert group_serializer.__class__.__name__ == 'GroupSerializer'

    group_serializer_2 = get_serializer_class(Group, ['id', 'name'], {
        'id': CharField()
    })(group)
    assert group_serializer_2.data == {'id': str(group.id), 'name': 'Group 1'}
