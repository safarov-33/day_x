import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создать согласованную резервную копию SQLite без перезаписи существующего файла."

    def add_arguments(self, parser):
        parser.add_argument("destination", type=Path)

    def handle(self, *args, **options):
        destination = options["destination"]
        config = settings.DATABASES["default"]
        if config["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Команда предназначена для SQLite.")
        source_path = Path(config["NAME"]).resolve()
        if not source_path.is_file():
            raise CommandError("Исходная база не найдена.")
        if destination.exists():
            raise CommandError("Файл назначения уже существует.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("xb"):
                pass
            destination.chmod(0o600)
            with sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True) as source:
                with sqlite3.connect(destination) as target:
                    source.backup(target)
        except (OSError, sqlite3.Error) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Резервная копия: {destination}"))
