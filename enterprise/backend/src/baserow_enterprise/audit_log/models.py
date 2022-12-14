from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


User = get_user_model()


class AuditLog(models.Model):
    action = models.CharField(max_length=32, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    saved_user_id = models.PositiveIntegerField(db_index=True, null=True)
    saved_user_email = models.CharField(max_length=255, db_index=True)

    group = models.ForeignKey("core.Group", on_delete=models.SET_NULL, null=True)
    saved_group_id = models.PositiveIntegerField(db_index=True, null=True)
    saved_group_name = models.CharField(max_length=255, db_index=True)

    application = models.ForeignKey(
        "core.Application", on_delete=models.SET_NULL, null=True
    )
    saved_application_id = models.PositiveIntegerField(db_index=True, null=True)
    saved_application_name = models.CharField(max_length=255, db_index=True)

    context_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_log_context",
    )
    context_object_id = models.PositiveIntegerField(null=True)
    context = GenericForeignKey("context_content_type", "context_object_id")
    saved_context_repr = models.CharField(max_length=255)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_log_target",
    )
    target_object_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    saved_target_repr = models.CharField(max_length=255)

    ip_address = models.GenericIPAddressField(null=True)

    from_state = models.JSONField(null=True)
    to_state = models.JSONField(null=True)

    class Meta:
        ordering = ["-timestamp"]

    def populate_initial_repr(self):
        if self.user:
            self.saved_user_id = self.user.id
            self.saved_user_email = self.user.email

        if self.group:
            self.saved_group_id = self.group.id
            self.saved_group_name = self.group.name

        if self.application:
            self.saved_application_id = self.application.id
            self.saved_application_name = self.application.name

        if self.context:
            self.saved_context_repr = str(self.context)

        if self.target:
            self.saved_target_repr = str(self.target)

    def save(self, *args, **kwargs):
        self.populate_reprs()
        super().save(*args, **kwargs)
