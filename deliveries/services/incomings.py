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
