from rest_framework import status
from rest_framework.exceptions import APIException

from .utils import get_request, validate_data, validate_data_custom_fields
from .exceptions import RequestBodyValidationException


def map_exceptions(exceptions):
    """
    This decorator simplifies mapping specific exceptions to a standard api response.

    Example:
      @map_exceptions({ SomeException: 'ERROR_1' })
      def get(self, request):
           raise SomeException('This is a test')

      HTTP/1.1 400
      {
        "error": "ERROR_1",
        "detail": "This is a test"
      }

    Example 2:
      @map_exceptions({ SomeException: ('ERROR_1', 404, 'Other message') })
      def get(self, request):
           raise SomeException('This is a test')

      HTTP/1.1 404
      {
        "error": "ERROR_1",
        "detail": "Other message"
      }
    """

    def map_exceptions_decorator(func):
        def func_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exceptions.keys()) as e:
                value = exceptions.get(e.__class__)
                status_code = status.HTTP_400_BAD_REQUEST
                detail = ''

                if isinstance(value, str):
                    error = value
                if isinstance(value, tuple):
                    error = value[0]
                    if len(value) > 1 and value[1] is not None:
                        status_code = value[1]
                    if len(value) > 2 and value[2] is not None:
                        detail = value[2]

                exc = APIException({
                    'error': error,
                    'detail': detail
                })
                exc.status_code = status_code

                raise exc
        return func_wrapper
    return map_exceptions_decorator


def validate_body(serializer_class):
    """
    This decorator can validate the request body using a serializer. If the body is
    valid it will add the data to the kwargs. If not it will raise an APIException with
    structured details about what is wrong.

    Example:
        class LoginSerializer(serializers.Serializer):
            username = serializers.EmailField()
            password = serializers.CharField()

        @validate_body(LoginSerializer)
        def post(self, request):
           raise SomeException('This is a test')

        HTTP/1.1 400
        {
          "error": "ERROR_REQUEST_BODY_VALIDATION",
          "detail": {
            "username": [
              {
                "error": "This field is required.",
                "code": "required"
              }
            ]
          }
        }

    :param serializer_class: The serializer that must be used for validating.
    :type serializer_class: Serializer
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)

            if 'data' in kwargs:
                raise ValueError('The data attribute is already in the kwargs.')

            kwargs['data'] = validate_data(serializer_class, request.data)
            return func(*args, **kwargs)
        return func_wrapper
    return validate_decorator


def validate_body_custom_fields(registry, base_serializer_class=None,
                                type_attribute_name='type'):
    """
    This decorator can validate the request data dynamically using the generated
    serializer that belongs to the type instance. Based on a provided
    type_attribute_name it will check the request data for a type identifier and based
    on that value it will load the type instance from the registry. With that type
    instance we know with which fields to build a serializer with that will be used.

    :param registry: The registry object where to get the type instance from.
    :type registry: Registry
    :param base_serializer_class: The base serializer class that will be used when
                                  generating the serializer.
    :type base_serializer_class: ModelSerializer
    :param type_attribute_name: The attribute name containing the type value in the
                                request data.
    :type type_attribute_name: str
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)
            type_name = request.data.get(type_attribute_name)

            if not type_name:
                # If the type name isn't provided in the data we will raise a machine
                # readable validation error.
                raise RequestBodyValidationException({
                    type_attribute_name: [
                        {
                            "error": "This field is required.",
                            "code": "required"
                        }
                    ]
                })

            if 'data' in kwargs:
                raise ValueError('The data attribute is already in the kwargs.')

            kwargs['data'] = validate_data_custom_fields(
                type_name, registry, request.data,
                base_serializer_class=base_serializer_class,
                type_attribute_name=type_attribute_name
            )
            return func(*args, **kwargs)
        return func_wrapper
    return validate_decorator
