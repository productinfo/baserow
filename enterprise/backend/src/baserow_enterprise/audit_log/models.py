from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class AuditLog(models.Model):
    event_type = models.CharField(max_length=32, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    initial_user_id = models.PositiveIntegerField(db_index=True, null=True)
    initial_user_email = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )

    group = models.ForeignKey("core.Group", on_delete=models.SET_NULL, null=True)
    initial_group_id = models.PositiveIntegerField(db_index=True, null=True)
    initial_group_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )

    application = models.ForeignKey(
        "core.Application", on_delete=models.SET_NULL, null=True
    )
    initial_application_id = models.PositiveIntegerField(db_index=True, null=True)
    initial_application_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )

    context_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_log_context",
    )
    context_object_id = models.PositiveIntegerField(null=True)
    context = GenericForeignKey("context_content_type", "context_object_id")
    initial_context_repr = models.CharField(max_length=255)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_log_target",
    )
    target_object_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    description = models.CharField(max_length=255)

    action = models.ForeignKey(
        "core.Action", on_delete=models.SET_NULL, null=True, db_index=True
    )
    undone_at = models.DateTimeField(null=True)
    redone_at = models.DateTimeField(null=True)

    additional_data = models.JSONField(null=True)
    from_state = models.JSONField(null=True)
    to_state = models.JSONField(null=True)

    def render_user(self):
        if self.initial_user_email:
            return f"{self.initial_user_email}({self.initial_user_id})"
        return "Anonymous"

    def render_group(self):
        if self.initial_group_name:
            return f"{self.initial_group_name}({self.initial_group_id})"
        return ""

    def render_target(self):
        if self.target:
            return str(self.target)
        return ""

    def render_context(self):
        if self.context:
            return f"in {self.context}"
        return ""

    def render_event_type(self):
        return self.event_type

    class Meta:
        ordering = ["-timestamp"]

    def populate_initial_repr(self):
        if self.user:
            self.initial_user_id = self.user.id
            self.initial_user_email = self.user.email

        if self.group:
            self.initial_group_id = self.group.id
            self.initial_group_name = self.group.name

        if self.application:
            self.initial_application_id = self.application.id
            self.initial_application_name = self.application.name

        if self.context:
            self.initial_context_repr = str(self.context)

        if self.target and not self.description:
            self.description = f"{self.render_user()} {self.render_event_type()} {self.render_target()}"
            if self.context:
                self.description += f" in {self.render_context()}"

        if not self.description:
            if self.from_state or self.to_state:
                self.description = f"{self.render_user()} {self.render_event_type()} from {self.from_state} to {self.to_state}"
            else:
                self.description = f"{self.render_user()} {self.render_event_type()} {self.additional_data}"

    def save(self, *args, **kwargs):
        self.populate_initial_repr()
        super().save(*args, **kwargs)
