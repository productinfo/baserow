from rest_framework import serializers

from baserow_enterprise.audit_log.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    rendered_user = serializers.SerializerMethodField()
    rendered_group = serializers.SerializerMethodField()

    def get_rendered_user(self, obj):
        return obj.render_user()

    def get_rendered_group(self, obj):
        return obj.render_group()

    class Meta:
        model = AuditLog
        fields = "__all__"
