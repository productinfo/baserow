from rest_framework import serializers

from baserow.api.user.serializers import NormalizedEmailField


class SamlLoginRequestSerializer(serializers.Serializer):
    email = NormalizedEmailField(required=False)
    original = serializers.CharField(required=False)
    language = serializers.CharField(required=False)
    template = serializers.CharField(required=False)
