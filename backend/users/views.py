from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.pagination import RecipePagination
from .models import Follow, User
from .serializers import CustomUserSerializer, FollowSerializer


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
            if serializer.is_valid(raise_exception=True):
                Follow.objects.create(user=user, author=author)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                )
            return Response(status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            obj = Follow.objects.filter(user=user, author=author)
            del_count, _ = obj.delete()
            if del_count:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
