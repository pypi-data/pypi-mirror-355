default_app_config = "django_notify_framework.apps.DjangoNotifyConfig"

from .notify import urls,views

__all__ = [
    "urls",
    "views",
]