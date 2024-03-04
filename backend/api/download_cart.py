from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import IngredientParameters


def download_cart(user):
    """Метод для скачивания списка покупок."""

    ingredients_total = (
        IngredientParameters.objects
        .filter(recipe__shopping_cart__user=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total=Sum('amount'))
        .order_by('ingredient__name')
    )

    shopping_list = []
    shopping_list.append('     ヽ( `･ω･)人( ^ω^)人( ﾟДﾟ)人(´∀｀)人(・∀・ )人(^Д^ )ﾉ\n')
    shopping_list.append(f'Список покупок пользователя {user.username}:\n\n')

    for ingredient in ingredients_total:
        name = ingredient['ingredient__name']
        measurement_unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['total']
        shopping_list.append(
            f'(っ◕‿◕)っ   {name} ({measurement_unit}) --> {amount}'
        )

    shopping_list.append('\n\n      Foodgram  ◦°˚ヽ(*・_・)ノ˚°◦')
    shopping_list = '\n'.join(shopping_list)

    filename = 'shopping_list.txt'
    response = HttpResponse(
        shopping_list,
        content_type='text/plain,charset=utf8',
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
