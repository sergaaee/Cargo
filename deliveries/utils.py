from functools import wraps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator

from deliveries.models import InventoryNumber, Incoming, InventoryNumberIncoming, TrackerCode, \
    InventoryNumberTrackerCode


def staff_and_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return login_required(user_passes_test(lambda u: u.is_staff)(_wrapped_view))


def update_inventory_and_trackers(incoming, form, tracker_inventory_map):
    """Обновляет инвентарные номера и трек-коды у поступления с правильной привязкой"""
    new_inventory_numbers = set(num.number for num in form.cleaned_data["inventory_numbers"])
    tracker, tracker_codes = form.cleaned_data["tracker"]

    # 📌 Получаем текущие связанные объекты
    existing_trackers = set(incoming.tracker.all())  # Все связанные трекеры
    existing_tracker_codes = set(
        TrackerCode.objects.filter(tracker__in=existing_trackers).values_list("code", flat=True)
    )
    existing_inventory_numbers = set(incoming.inventory_numbers.values_list("number", flat=True))

    # Удаляем старые инвентарные номера и связи
    for inv_num in existing_inventory_numbers - new_inventory_numbers:
        inv_obj = InventoryNumber.objects.get(number=inv_num)
        InventoryNumberIncoming.objects.filter(incoming=incoming, inventory_number=inv_obj).delete()
        InventoryNumberTrackerCode.objects.filter(inventory_number=inv_obj).delete()
        inv_obj.is_occupied = False
        inv_obj.save()

    # Добавляем новые инвентарные номера и связываем их правильно
    for tracker_code, inventory_numbers in tracker_inventory_map.items():
        tracker_code_obj, _ = TrackerCode.objects.get_or_create(code=tracker_code, defaults={"status": "Active"})

        for inv_num in inventory_numbers:
            inv_obj, created = InventoryNumber.objects.get_or_create(number=inv_num)
            InventoryNumberIncoming.objects.get_or_create(incoming=incoming, inventory_number=inv_obj)
            inv_obj.is_occupied = True
            inv_obj.save()

            # Привязываем только к нужному tracker_code
            InventoryNumberTrackerCode.objects.get_or_create(
                inventory_number=inv_obj,
                tracker_code=tracker_code_obj
            )

    # Удаляем старые трек-коды
    for old_code in existing_tracker_codes - set(tracker_codes):
        TrackerCode.objects.filter(code=old_code, tracker__in=existing_trackers).delete()

    # Добавляем новые трек-коды
    for new_code in set(tracker_codes) - existing_tracker_codes:
        tracker_code, created = TrackerCode.objects.get_or_create(code=new_code, defaults={"status": "Active"})
        tracker.tracking_codes.add(tracker_code)

    # ✅ Обновляем связь incoming ↔ tracker
    incoming.tracker.set([tracker])  # Полностью заменяем все трекеры

    # ✅ Сохраняем изменения
    incoming.save()
    form.save_m2m()


def update_inventory_numbers(inventory_numbers, incoming, occupied=True):
    for number in inventory_numbers:
        inventory_number_obj = InventoryNumber.objects.get(number=number)
        inventory_number_obj.is_occupied = occupied
        inventory_number_obj.save()
        if occupied:
            incoming.inventory_numbers.add(inventory_number_obj)
        else:
            incoming.inventory_numbers.remove(inventory_number_obj)


# Подготовка данных для JavaScript
def prepare_incoming_data(incoming_queryset):
    return [
        {
            "id": incoming.id,
            "places_count": incoming.places_count,
            "arrival_date": incoming.arrival_date.isoformat() if incoming.arrival_date else None,
            "inventory_numbers": [inv.number for inv in incoming.inventory_numbers.all()],
            "package_type": incoming.package_type,
            "size": incoming.size,
            "status": incoming.status,
            "weight": incoming.weight,
            "tracking_codes": [
                track_code.code
                for tracker in incoming.tracker.all()
                for track_code in tracker.tracking_codes.all()
            ],
            "track_inv_map": [
                {
                    "code": track_code.code,
                    "inventory_numbers": [
                        inv.number for inv in track_code.inventory_numbers.all()
                    ]
                }
                for tracker in incoming.tracker.all()
                for track_code in tracker.tracking_codes.all()
            ],
            "tag": incoming.tag.name if incoming.tag else None,
            "client_phone": incoming.client.profile.phone_number if incoming.client and incoming.client.profile else None,
        }
        for incoming in incoming_queryset
    ]


def paginated_query_incoming_list(request, incomings):
    sort_by = request.GET.get('sort_by', 'arrival_date')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    incomings = incomings.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(incomings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj, sort_by, sort_order


def paginated_query_consolidation_list(request, consolidations):
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    consolidations = consolidations.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(consolidations, 10)
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


def consolidation_columns():
    return [
        ('track_code__code', 'Трек-код'),
        ('created_at', 'Дата'),
        ('client', 'Клиент'),
        ('delivery_type', 'Доставка'),
        ('status', 'Статус')
    ]


def packaged_columns():
    return [
        ('created_at', 'Дата отправки'),
        ('client', 'Клиент'),
        ('places__count', 'Мест'),
        ('places__weight__sum', 'Вес'),
        ('price', 'Цена'),
        ('delivery_type', 'Доставка'),
        ('status', 'Статус')
    ]
