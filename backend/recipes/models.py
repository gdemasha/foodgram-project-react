from django.core.validators import MinValueValidator
from django.db import models

from users.models import User
from .constants import (
    COLOR,
    MAX_LENGTH_INGREDIENT,
    MAX_LENGTH_TAG,
    MAX_LENGTH_TITLE,
)


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        'Тег',
        max_length=MAX_LENGTH_TAG,
        unique=True,
    )
    color = models.CharField(
        'Цветовой код',
        max_length=MAX_LENGTH_TAG,
        unique=True,
        choices=COLOR,
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_LENGTH_TAG,
        unique=True,
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название ингредиента',
        max_length=MAX_LENGTH_INGREDIENT,
        unique=True,
        db_index=True,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_LENGTH_INGREDIENT,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        'Название рецепта',
        max_length=MAX_LENGTH_TITLE,
        db_index=True,
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images',
        default=None,
    )
    text = models.TextField('Текст рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientParameters',
        through_fields=('recipe', 'ingredient'),
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        default=1,
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe',
            )
        ]

    def __str__(self):
        return self.name


class IngredientParameters(models.Model):
    """Промежуточная таблица для ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество ингредиентов',
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'ингредиент с количеством'
        verbose_name_plural = 'Ингредиенты с количеством'
        default_related_name = 'ingredient_parameters'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.ingredient}, {self.amount}'


class Favorited(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        related_name='favorites',
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorited_by',
        verbose_name='Избранное',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            )
        ]

    def __str__(self):
        f'{self.user.username} добавил(а) в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        verbose_name='В корзине',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_purchase',
            )
        ]

    def __str__(self):
        f'{self.user.username} добавил(а) в список покупок {self.recipe}'
