from django.core.paginator import Paginator

QUANTITY_POSTS: int = 10


def paginator(request, post_list):
    '''Создаём объект паджинатора для разбиения одной страницы со всеми постами
    на несколько с фиксированным количеством'''

    pagin = Paginator(post_list, QUANTITY_POSTS)
    # Извлечение запрошенной страницы из URL
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = pagin.get_page(page_number)
    return page_obj
