import csv

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class CSVBaseCommand(BaseCommand):
    """Базовая команда для импорта данных из csv."""

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        try:
            with open(options['csv_file'], newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.process_row(row)
        except FileNotFoundError:
            raise CommandError(f'Файл не найден:{options["csv_file"]}')
        except Exception as error:
            raise CommandError(f'Ошибка обработки файла:{str(error)}')

    def process_row(self, row):
        raise NotImplementedError()


class Command(CSVBaseCommand):
    """Импорт ингредиентов из csv-файла."""

    def process_row(self, row):
        Ingredient.objects.update_or_create(
            name=row['name'],
            defaults={'measurement_unit': row['measurement_unit']},
        )
