from django.utils import timezone as tz


def year(request):
    """Добавляет текущий год по локальному времени"""

    years = tz.now().year
    return {
        'year': years,
    }
