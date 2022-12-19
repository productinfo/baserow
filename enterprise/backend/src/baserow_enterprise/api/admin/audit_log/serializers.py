from rest_framework import serializers

from baserow_enterprise.audit_log.models import AuditLogEntry


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_user(self, obj):
        return f"{obj.user_email} ({obj.user_id})"

    def get_group(self, obj):
        return f"{obj.group_name} ({obj.group_id})"

    def get_type(self, obj):
        return obj.get_type_description()

    def get_description(self, obj):
        return obj.get_event_description()

    class Meta:
        model = AuditLogEntry
        fields = (
            "id",
            "user",
            "group",
            "type",
            "timestamp",
            "description",
            "ip_address",
        )


class AuditLogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = ("user_email",)

    def to_representation(self, instance):
        return {"id": instance.user_email, "value": instance.user_email}


class AuditLogGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = ("group_name",)

    def to_representation(self, instance):
        return {"id": instance.group_name, "value": instance.group_name}


class AuditLogEventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = ("event_type",)

    def to_representation(self, instance):
        return {"id": instance.event_type, "value": instance.get_type_description()}
