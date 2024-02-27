from django.contrib import admin

from .models import (
    Favorited,
    Ingredient,
    IngredientParameters,
    Recipe,
    ShoppingCart,
    Tag,
)


class IngredientParametersInline(admin.StackedInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientParametersInline, )
    list_display = ('author', 'name')
    search_fields = ('author__username', 'name', 'tags')
    list_filter = ('author', 'name', 'tags')
    readonly_fields = ('is_favorited',)

    def is_favorited(self, instance):
        return instance.recipes_favorited.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(IngredientParameters)
class IngredientParametersAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')
    search_fields = ('ingredient__name', 'recipe__name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Favorited)
class FavoritedAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
