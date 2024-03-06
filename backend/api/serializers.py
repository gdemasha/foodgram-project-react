from django.contrib.auth.validators import UnicodeUsernameValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField, base64
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from recipes.constants import MAX_LENGTH_NAME, MAX_LENGTH_TITLE
from recipes.models import (
    Favorited,
    IngredientParameters,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import User, Follow


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    username = serializers.CharField(
        validators=[UnicodeUsernameValidator()],
        max_length=MAX_LENGTH_NAME,
        required=True,
    )

    class Meta:
        model = User
        fields = (
            'id', 'password',
            'username', 'email',
            'first_name', 'last_name',
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return (
            Follow.objects
            .filter(user=request.user, author=author)
            .exists()
        )


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    email = serializers.ReadOnlyField(source='author.email')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')

    class Meta:
        model = Follow
        fields = (
            'recipes_count', 'recipes',
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_subscribed',
        )

    def get_recipes(self, author):
        limit = self.context['request'].query_params.get('recipes_limit', None)
        recipes = Recipe.objects.filter(author=author)
        if limit:
            recipes = recipes[:int(limit)]
        return MiniRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user

        if (
            Follow.objects
            .filter(user=user, author=author)
            .exists()
        ):
            raise ValidationError(
                detail='Вы уже подписаны на данного автора.',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail='Невозможно подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


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
        return RecipeReadSerializer(instance).data

    def set_ingredients_and_tags(self, ingredients, recipe, tags):
        (
            IngredientParameters.objects
            .bulk_create(
                IngredientParameters(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            )
        )
        recipe.tags.set(tags)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.set_ingredients_and_tags(ingredients, recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.set_ingredients_and_tags(ingredients, instance, tags)
        return super().update(instance, validated_data)

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError('Необходимо выбрать тег.')

        tag_list = []
        for tag in tags:
            if tag in tag_list:
                raise ValidationError('Теги не должны повторяться.')
            tag_list.append(tag)

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

            id = ingredient['id']
            if id in ingredient_list:
                raise ValidationError('Ингредиенты не могут повторяться.')
            ingredient_list.append(id)

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


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в подписке."""

    image = base64

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'cooking_time',
            'image',
        )
