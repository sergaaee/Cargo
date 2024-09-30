from functools import wraps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models.functions import Cast
from django.db.models import CharField, Q

from deliveries.models import InventoryNumber, Incoming


def staff_and_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return login_required(user_passes_test(lambda u: u.is_staff)(_wrapped_view))


def update_inventory_numbers(inventory_numbers, incoming, occupied=True):
    for number in inventory_numbers:
        inventory_number_obj = InventoryNumber.objects.get(number=number)
        inventory_number_obj.is_occupied = occupied
        inventory_number_obj.save()
        if occupied:
            incoming.inventory_numbers.add(inventory_number_obj)
        else:
            incoming.inventory_numbers.remove(inventory_number_obj)


def paginated_query_incoming_list(request, query, incomings):
    sort_by = request.GET.get('sort_by', 'arrival_date')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    if query:
        incomings = incomings.annotate(
            codes_str=Cast('tracker__tracking_codes', CharField())  # Преобразуем массив codes в строку
        ).filter(
            Q(codes_str__icontains=query) | Q(inventory_numbers__number__icontains=query)
        )

    incomings = incomings.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(incomings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj, sort_by, sort_order


def incoming_columns():
    return [
        ('tracker', 'Трек-номер'),
        ('tag__name', 'Тег'),
        ('arrival_date', 'Дата прибытия'),
        ('inventory_numbers', 'Инвентарные номера'),
        ('places_count', 'Количество мест'),
        ('client', 'Клиент'),
        ('status', 'Статус'),
    ]
