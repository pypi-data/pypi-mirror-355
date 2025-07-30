from django.apps import AppConfig


class DjangoNotifyAppConfig(AppConfig):
    name = 'django_notify_framework'
    verbose_name = 'Django Notify'

    def ready(self):
        default_auto_field = 'django.db.models.AutoField'
        name = 'django_notify_framework'
        verbose_name = 'Django Notify Framework'