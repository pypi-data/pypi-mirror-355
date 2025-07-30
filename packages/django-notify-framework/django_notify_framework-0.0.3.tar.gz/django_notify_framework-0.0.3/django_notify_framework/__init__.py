default_app_config = "django_notify.apps.DjangoNotifyConfig"

from .notify import urls,views

__all__ = [
    "urls",
    "views",
]