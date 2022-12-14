from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db import models

from baserow.core.models import Action, Application, Group

User = get_user_model()


@dataclass
class AuditableEvent:
    event_type: Optional[str] = None
    timestamp: Optional[models.DateTimeField] = None
    ip_address: Optional[str] = None
    user: Optional[User] = None
    group: Optional[Group] = None
    application: Optional[Application] = None
    action: Optional[Action] = None
    context: Optional[models.Model] = None
    target: Optional[models.Model] = None
    description: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    from_state: Optional[Dict[str, Any]] = None
    to_state: Optional[Dict[str, Any]] = None
