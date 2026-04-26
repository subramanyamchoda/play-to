import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

# Create celery app
app = Celery("config")

# Load settings from Django settings.py
# Example: CELERY_BROKER_URL, CELERY_RESULT_BACKEND
app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

# Auto discover tasks.py from installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Useful for testing celery worker.
    Run manually if needed.
    """
    print(f"Request: {self.request!r}")