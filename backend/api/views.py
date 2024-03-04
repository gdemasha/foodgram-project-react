from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS,
)
from rest_framework.response import Response

from recipes.models import (
    Favorited,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Follow, User
from .download_cart import download_cart
from .filters import GetRecipeFilterSet, NameIngredientSearch
from .pagination import RecipePagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    CustomUserSerializer,
    FollowSerializer,
    IngredientSerializer,
    MiniRecipeSerializer,
    RecipeWriteSerializer,
    RecipeReadSerializer,
    TagSerializer,
)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователя."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = RecipePagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Метода для получения профиля пользователя."""

        user = self.request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        pagination_class=RecipePagination,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Метод для получения всех подписок."""

        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        """Метод для создания и удаления подписки."""

        author = get_object_or_404(User, id=self.kwargs.get('id'))
        user = self.request.user

        if request.method == 'POST':
            serializer = FollowSerializer(
                author,
                data=request.data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, author=author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        del_count, _ = Follow.objects.filter(user=user, author=author).delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NameIngredientSearch
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = (
        Recipe.objects
        .select_related('author')
        .prefetch_related('ingredients', 'tags')
        .order_by('-pub_date')
    )
    pagination_class = RecipePagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = GetRecipeFilterSet
    permission_classes = (IsOwnerOrAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_to(self, model, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'detail': 'Выбранный рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = MiniRecipeSerializer(recipe)
        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def delete_from(self, model, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        del_count, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Метод для добавления и удаления избранных рецептов."""

        if request.method == 'POST':
            return self.add_to(Favorited, request, pk)
        return self.delete_from(Favorited, request, pk)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления в корзину и удаления рецептов из списка."""

        if request.method == 'POST':
            return self.add_to(ShoppingCart, request, pk)
        return self.delete_from(ShoppingCart, request, pk)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""

        user = self.request.user
        if user.shopping_cart.exists():
            return download_cart(user)
        return Response(status=status.HTTP_404_NOT_FOUND)
