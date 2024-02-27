from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_NAME


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        'email',
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
    )
    username = models.CharField(
        'Имя пользователя',
        unique=True,
        max_length=MAX_LENGTH_NAME,
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_NAME,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_NAME,
    )
    password = models.CharField(
        'Пароль',
        max_length=MAX_LENGTH_NAME,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')

    class Meta:
        ordering = ('id',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'username'],
                name='unique_user',
            )
        ]

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Отслеживаемый автор',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            )
        ]

    def __str__(self):
        f'{self.user.username} подписан на {self.author.username}'
