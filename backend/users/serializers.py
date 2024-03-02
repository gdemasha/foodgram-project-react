from django.contrib.auth.validators import UnicodeUsernameValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import base64
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from recipes.constants import MAX_LENGTH_NAME
from recipes.models import Recipe
from .models import User, Follow


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


class RecipeForFollowSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов в подписке."""

    image = base64

    class Meta:
        model = Recipe
        fields = (
            'id', 'name',
            'cooking_time',
            'image',
        )


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id', 'username',
            'is_subscribed',
            'first_name',
            'last_name',
            'email',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if not request.user.is_anonymous:
            return (
                Follow.objects
                .filter(user=request.user, author=author)
                .exists()
            )
        return False

    def get_recipes(self, author):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=author)
        if limit:
            recipes = recipes[:int(limit)]

        serializer = RecipeForFollowSerializer(
            recipes,
            many=True,
            read_only=True,
        )
        return serializer.data

    def get_id(self, author):
        return author.id

    def get_username(self, author):
        return author.username

    def get_first_name(self, author):
        return author.first_name

    def get_last_name(self, author):
        return author.last_name

    def get_email(self, author):
        return author.email

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
