from django.core.paginator import Paginator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import Post

QUANTITY_POSTS: int = 10
CACHE_TIME: int = 20


def paginator(request, post_list):
    """Создаём объект паджинатора для разбиения одной страницы со всеми постами
    на несколько с фиксированным количеством"""

    pagin = Paginator(post_list, QUANTITY_POSTS)
    # Извлечение запрошенной страницы из URL
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = pagin.get_page(page_number)
    return page_obj


@receiver(post_save, sender=Post)
def my_handler(sender, **kwargs):
    """Создаём хендлер, который перезаписывает кэш 1 страницы, когда объекты
    связанные с моделью Post обновляются"""

    post_list = (Post.objects.select_related('group', 'author')
                 .prefetch_related('comments').all())
    _paginator = Paginator(post_list, QUANTITY_POSTS)
    page = _paginator.get_page('1')
    cache.set('index_first_page', page, CACHE_TIME)


def cache_index_first_page(request, post_list):
    """Функция, которая позволяет закэшировать первую страницу главной
    страницы"""

    page = None

    page_number = request.GET.get('page', '1')
    if page_number == '1':
        cached_page = cache.get('index_first_page')
        if cached_page is not None:
            page = cached_page

    if page is None:
        _paginator = Paginator(post_list, QUANTITY_POSTS)
        page = _paginator.get_page(page_number)

        if page_number == '1':
            cache.set('index_first_page', page, CACHE_TIME)

    return page
