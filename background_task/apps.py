try:
    from django.apps import AppConfig
except ImportError:
    pass  # Django < 1.7
else:

    class BackgroundTasksAppConfig(AppConfig):
        name = 'background_task'
        from background_task import __version__ as version_info
        verbose_name = 'Background Tasks ({})'.format(version_info)

        def ready(self):
            import background_task.signals  # noqa
