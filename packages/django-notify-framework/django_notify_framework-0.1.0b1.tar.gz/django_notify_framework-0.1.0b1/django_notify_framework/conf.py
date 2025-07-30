from django.conf import settings


class DjangoNotifySettings:
    def __init__(self):
        self._defaults = {
            "NOTIFY_WEBSOCKET_CHANNELS": "django-notify",
            "NOTIFY_REALTIME_ENABLED": True,
            "NOTIFY_DELIVERY_QUEUE_ENABLED": True,
            "NOTIFY_MAX_RETRIES": 3,
        }

    def __getattr__(self, name):
        if name in self._defaults:
            return getattr(settings, name, self._defaults[name])
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def get(self, name, default=None):
        return getattr(settings, name, self._defaults.get(name, default))


notify_settings = DjangoNotifySettings()
