from pathlib import Path
from typing import Any

from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as DjangoMigrateCommand
from django.db import connections


class Command(DjangoMigrateCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        database = connections[options["database"]]
        if database.vendor == "sqlite" and not (options["plan"] or options["check_unapplied"]):
            path = Path(database.settings_dict["NAME"])
            if path.is_absolute():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as error:
                    raise CommandError(f"Cannot prepare SQLite directory {path.parent}: {error}") from error

        return super().handle(*args, **options)
