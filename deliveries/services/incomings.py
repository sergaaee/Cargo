from django.core.exceptions import ValidationError
from deliveries.models import Tracker, TrackerCode, InventoryNumber, Location, InventoryNumberTrackerCode, \
    InventoryNumberIncoming


def create_tracker_if_needed(tracker_codes, created_by=None):
    tracker = Tracker.objects.create(name="Трекер для " + ", ".join(tracker_codes), created_by=created_by)
    for code in tracker_codes:
        tracker_code, _ = TrackerCode.objects.get_or_create(code=code, defaults={'status': 'Active'})
        tracker_code.tracker = tracker
        tracker_code.save()
        tracker.tracking_codes.add(tracker_code)
    tracker.save()
    return tracker


def assign_locations_to_inventory(request_post):
    assignments = []
    for key in request_post:
        if key.startswith('inventory_numbers_'):
            index = key.split('_')[-1]
            location_id = request_post.get(f'location_{index}')
            if not location_id:
                raise ValidationError('Пожалуйста, выберите локации для всех инвентарных номеров.')
            location = Location.objects.get(id=location_id)
            inventory_numbers = [num.strip() for num in request_post[key].split(',') if num.strip()]
            for number in inventory_numbers:
                inv = InventoryNumber.objects.get(number=number)
                inv.location = location
                inv.save()
    return assignments


def assign_locations_to_inventory_in_editing(request_post, inventory_numbers_objs):
    assignments = []
    for key in request_post:
        if key.startswith('inventory_numbers_'):
            index = key.split('_')[-1]
            location_id = request_post.get(f'location_{index}')
            if not location_id:
                raise ValidationError('Пожалуйста, выберите локации для всех инвентарных номеров.')
            location = Location.objects.get(id=location_id)
            inventory_numbers = [num.strip() for num in request_post[key].split(',') if num.strip()]
            for number in inventory_numbers:
                inv = InventoryNumber.objects.get(number=number)
                assignments.append((inv, location))
    return assignments


def associate_tracker_inventory(incoming, tracker_inventory_map):
    for tracker_code, inventory_numbers in tracker_inventory_map.items():
        tracker_code_obj = TrackerCode.objects.get(code=tracker_code)
        for inventory_number in inventory_numbers:
            inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
            InventoryNumberTrackerCode.objects.create(tracker_code=tracker_code_obj,
                                                      inventory_number=inventory_number_obj)
            InventoryNumberIncoming.objects.create(incoming=incoming, inventory_number=inventory_number_obj)


def set_tracker_status(tracker):
    if tracker.tracking_codes.filter(status='Inactive').count() == 0:
        tracker.status = 'Completed'
        tracker.save()


def prepare_incoming_edit_data(incoming):
    # Обрабатываем инвентарные номера и трек-коды
    codes_nums_map = {}
    for code in incoming.tracker.values_list('tracking_codes__code', flat=True):
        inventory_numbers = list(incoming.tracker.get(tracking_codes__code=code)
                                 .tracking_codes.get(code=code)
                                 .inventory_numbers.values_list('number', flat=True))

        codes_nums_map[code] = inventory_numbers

    # Locations - inv numbers map
    locs_num_map = {}
    for loc_id in incoming.inventory_numbers.values_list('location__id', flat=True).distinct():
        inventory_numbers = incoming.inventory_numbers.filter(location__id=loc_id).values_list('number', flat=True)
        locs_num_map[str(loc_id)] = list(inventory_numbers)

    # Группировка для шаблона
    location_inventory_groups = []
    for loc_id in incoming.inventory_numbers.values_list('location__id', flat=True).distinct():
        inventory_numbers = incoming.inventory_numbers.filter(location__id=loc_id).values_list('number', flat=True)
        location_inventory_groups.append({
            'location_id': loc_id,
            'inventory_numbers': list(inventory_numbers)
        })

    available_inventory_numbers = InventoryNumber.objects.filter(is_occupied=False)
    locations = Location.objects.all()

    return dict(codes_nums_map=codes_nums_map, available_inventory_numbers=available_inventory_numbers, locations=locations, location_inventory_groups=location_inventory_groups, locs_num_map=locs_num_map)
