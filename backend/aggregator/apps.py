"""App configuration for the aggregator app."""

from django.apps import AppConfig


class AggregatorConfig(AppConfig):
    """Django app config for aggregator."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aggregator"

