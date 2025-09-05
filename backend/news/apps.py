from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):  # pragma: no cover - side effect during tests
        """Ensure SQLite databases have required tables during tests.

        When running in environments without a prepared database (like the
        execution sandbox for tests), Django doesn't automatically run
        migrations.  This hook applies migrations on startup for SQLite
        databases so that the test suite can operate without requiring an
        external PostgreSQL server.
        """
        engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
        if engine.endswith("sqlite3"):
            try:
                call_command("migrate", run_syncdb=True, interactive=False)
            except Exception:
                # If migrations fail we let tests surface the error.
                pass
