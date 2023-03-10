import pytest

from django.shortcuts import reverse

from baserow.contrib.database.fields.models import Field, TextField, NumberField


@pytest.mark.django_db
def test_list_fields(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    field_1 = data_fixture.create_text_field(table=table_1, order=1, primary=True)
    field_2 = data_fixture.create_text_field(table=table_1, order=3)
    field_3 = data_fixture.create_number_field(table=table_1, order=2)
    data_fixture.create_boolean_field(table=table_2, order=1)

    response = api_client.get(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table_1.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == 200
    response_json = response.json()

    assert len(response_json) == 3

    assert response_json[0]['id'] == field_1.id
    assert response_json[0]['type'] == 'text'
    assert response_json[0]['primary']
    assert response_json[0]['text_default'] == field_1.text_default

    assert response_json[1]['id'] == field_3.id
    assert response_json[1]['type'] == 'number'
    assert not response_json[1]['primary']
    assert response_json[1]['number_type'] == field_3.number_type
    assert response_json[1]['number_decimal_places'] == field_3.number_decimal_places
    assert response_json[1]['number_negative'] == field_3.number_negative

    assert response_json[2]['id'] == field_2.id
    assert response_json[2]['type'] == 'text'
    assert not response_json[2]['primary']
    assert response_json[2]['text_default'] == field_2.text_default

    response = api_client.get(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table_2.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.get(
        reverse('api_v0:database:fields:list', kwargs={'table_id': 999999}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    response = api_client.post(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table.id}),
        {
            'name': 'Test 1',
            'type': 'NOT_EXISTING'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert response_json['detail']['type'][0]['code'] == 'invalid_choice'

    response = api_client.post(
        reverse('api_v0:database:fields:list', kwargs={'table_id': 99999}),
        {'name': 'Test 1', 'type': 'text'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    response = api_client.post(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table_2.id}),
        {'name': 'Test 1', 'type': 'text'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.post(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Test 1', 'type': 'text', 'text_default': 'default!'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['type'] == 'text'

    text = TextField.objects.filter()[0]
    assert response_json['id'] == text.id
    assert response_json['name'] == text.name
    assert response_json['order'] == text.order
    assert response_json['text_default'] == 'default!'


@pytest.mark.django_db
def test_get_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    text = data_fixture.create_text_field(table=table)
    number = data_fixture.create_number_field(table=table_2)

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': number.id})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': 99999})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['id'] == text.id
    assert response_json['name'] == text.name
    assert not response_json['text_default']


@pytest.mark.django_db
def test_update_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    text = data_fixture.create_text_field(table=table)
    text_2 = data_fixture.create_text_field(table=table_2)

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text_2.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': 999999})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {'UNKNOWN_FIELD': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 200

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1', 'text_default': 'Something'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['id'] == text.id
    assert response_json['name'] == 'Test 1'
    assert response_json['text_default'] == 'Something'

    text.refresh_from_db()
    assert text.name == 'Test 1'
    assert text.text_default == 'Something'

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1', 'type': 'text', 'text_default': 'Something'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['name'] == 'Test 1'
    assert response_json['type'] == 'text'

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {'type': 'number', 'number_negative': True},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['name'] == 'Test 1'
    assert response_json['type'] == 'number'
    assert response_json['number_type'] == 'INTEGER'
    assert response_json['number_decimal_places'] == 1
    assert response_json['number_negative']

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {
            'number_type': 'DECIMAL',
            'number_decimal_places': 2,
            'number_negative': False
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['name'] == 'Test 1'
    assert response_json['type'] == 'number'
    assert response_json['number_type'] == 'DECIMAL'
    assert response_json['number_decimal_places'] == 2
    assert not response_json['number_negative']

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.patch(
        url,
        {'type': 'boolean', 'name': 'Test 2'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_CANNOT_CHANGE_FIELD_TYPE'


@pytest.mark.django_db
def test_delete_field(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    text = data_fixture.create_text_field(table=table)
    number = data_fixture.create_number_field(table=table_2)

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': number.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 404

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': text.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204

    assert Field.objects.all().count() == 1
    assert TextField.objects.all().count() == 0
    assert NumberField.objects.all().count() == 1

    table_3 = data_fixture.create_database_table(user=user)
    primary = data_fixture.create_text_field(table=table_3, primary=True)

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': primary.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_CANNOT_DELETE_PRIMARY_FIELD'
