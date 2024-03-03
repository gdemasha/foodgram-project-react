from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from recipes.models import (
    Favorited,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.serializers import RecipeForFollowSerializer
from .download_cart import download
from .filters import GetRecipeFilterSet, NameIngredientSearch
from .pagination import RecipePagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeWriteSerializer,
    RecipeReadSerializer,
    TagSerializer,
)


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
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Метод для добавления и удаления избранных рецептов."""

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        obj = Favorited.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if obj.exists():
                raise ValidationError('Выбранный рецепт уже добавлен')
            Favorited.objects.create(user=user, recipe=recipe)
            serializer = RecipeForFollowSerializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
            )
        del_count, _ = obj.delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления в корзину и удаления рецептов из списка."""

        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        obj = ShoppingCart.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if obj.exists():
                raise ValidationError('Выбранный рецепт уже добавлен')
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeForFollowSerializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
            )

        del_count, _ = obj.delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""

        user = self.request.user
        if user.shopping_cart.exists():
            return download(user)
        return Response(status=status.HTTP_404_NOT_FOUND)
