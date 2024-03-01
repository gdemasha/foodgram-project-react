from recipes.models import Ingredient
from .base_command import CSVBaseCommand


class Command(CSVBaseCommand):
    """Импорт ингредиентов из csv-файла."""

    def process_row(self, row):
        Ingredient.objects.update_or_create(
            name=row['name'],
            defaults={'measurement_unit': row['measurement_unit']},
        )
