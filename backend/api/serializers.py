from drf_extra_fields.fields import Base64ImageField, base64
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from recipes.constants import MAX_LENGTH_TITLE
from recipes.models import (
    Favorited,
    IngredientParameters,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientParametersSerializer(serializers.ModelSerializer):
    """Сериализатор для промежуточной таблицы ингредиентов."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientParameters
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения запросов к рецептам."""

    author = CustomUserSerializer(read_only=True, many=False)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngredientParametersSerializer(
        read_only=True,
        many=True,
        source='ingredient_parameters',
    )
    image = base64
    name = serializers.CharField(max_length=MAX_LENGTH_TITLE)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'name', 'text',
            'image', 'cooking_time', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return (
            Favorited.objects
            .filter(user=request.user, recipe=obj)
            .exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return (
            ShoppingCart.objects
            .filter(user=request.user, recipe=obj)
            .exists()
        )


class WriteIngredientParametersSerializer(IngredientParametersSerializer):
    """Сериализатор для создания ингредиента."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = IngredientParameters
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для написания запросов к рецептам."""

    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = WriteIngredientParametersSerializer(
        write_only=True,
        many=True,
        required=True,
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'name', 'image', 'text',
            'cooking_time', 'ingredients',
        )

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(instance)
        return serializer.data

    def set_ingredients_tags(self, ingredients, recipe, tags):
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = ingredient['id']
            ingredients, created = (
                IngredientParameters.objects
                .update_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )
            )
        recipe.tags.set(tags)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.set_ingredients_tags(ingredients, recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if 'tags' in request.data and 'ingredients' in request.data:

            tags = validated_data.pop('tags')
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.set_ingredients_tags(ingredients, instance, tags)
            return super().update(instance, validated_data)

        raise ValidationError

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError('Необходимо выбрать тег.')

        tag_list = []
        for tag in tags:
            if tag in tag_list:
                raise ValidationError('Теги не должны повторяться.')
            tag_list.append(tag)

        if len(tag_list) <= 0:
            raise ValidationError('Список ингредиентов не может быть пустым.')

        return value

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError('Необходимо выбрать ингредиенты.')

        ingredient_list = []
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise ValidationError(
                    'Необходимо указать количество ингредиентов.'
                )

            name = ingredient['id']
            if name in ingredient_list:
                raise ValidationError('Ингредиенты не могут повторяться.')
            ingredient_list.append(name)

        if len(ingredient_list) <= 0:
            raise ValidationError('Список ингредиентов не может быть пустым.')

        return value

    def validate_cooking_time(self, value):
        if not value:
            raise ValidationError('Необходимо добавить время приготовления.')

        if value <= 0:
            raise ValidationError(
                'Время приготовления не может быть меньше 1 минуты.'
            )
        if not isinstance(value, int):
            raise ValidationError(
                'Укажите время приготовления целым числом в минутах.'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise ValidationError('Добавьте фотографию.')
        return value
