import json

from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum

from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404

from user_profile.models import ClientManagerRelation, UserProfile
from .choices import PackagedStatuses
from .utils import staff_and_login_required, login_required, update_inventory_numbers, incoming_columns, \
    paginated_query_incoming_list, prepare_incoming_data, consolidation_columns, paginated_query_consolidation_list, \
    update_inventory_and_trackers, packaged_columns, paginated_query_trackers_list, trackers_list_columns, \
    handle_incoming_status_and_redirect

from .forms import IncomingForm, PhotoFormSet, TagForm, TrackerForm, ConsolidationForm, PackageForm, IncomingEditForm, \
    GenerateInventoryNumbersForm, LocationForm, DeliveryTypeForm, PackageTypeForm, DeliveryPriceRangeFormSet
from .models import Tag, Photo, Incoming, InventoryNumber, Tracker, TrackerCode, InventoryNumberTrackerCode, \
    ConsolidationCode, Consolidation, ConsolidationIncoming, InventoryNumberIncoming, ConsolidationInventory, Place, \
    Location, PackageType, DeliveryType, DeliveryPriceRange
import re
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128


@staff_and_login_required
def delete_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'DELETE':
        photo.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@staff_and_login_required
def incoming_new(request):
    if request.method == 'POST':
        form = IncomingForm(request.POST, request.FILES)
        client_phone = request.POST.get("client", "").strip()

        if form.is_valid():
            incoming = form.save(commit=False)
            incoming.manager = request.user
            incoming.tag = form.cleaned_data['tag']
            tracker, tracker_codes = form.cleaned_data.get('tracker')

            # Если трекер не найден, создаем новый
            if not tracker:
                tracker = Tracker.objects.create(name="Трекер для " + ", ".join(tracker_codes), )

                # Привязываем коды к новому трекеру
                for code in tracker_codes:
                    tracker_code, created = TrackerCode.objects.get_or_create(code=code,
                                                                              defaults={'status': 'Active', })
                    tracker_code.tracker = tracker
                    tracker.tracking_codes.add(tracker_code)
                    tracker_code.save()
                tracker.save()

            # Client logic
            if client_phone:
                try:
                    client_profile = UserProfile.objects.get(phone_number=client_phone)
                    incoming.client = client_profile.user
                except UserProfile.DoesNotExist:
                    return JsonResponse({'success': False, 'errors': [f'❌ Клиент с номером {client_phone} не найден!']})
            else:
                if tracker.created_by:
                    incoming.client = tracker.created_by
                elif incoming.tag and incoming.tag.created_by:
                    incoming.client = incoming.tag.created_by

            # Проверка все ли инвентарные номера имеют локации, если да - сохранить для привязки в будущем
            location_assignments = []
            for key in request.POST:
                if key.startswith('inventory_numbers_'):
                    index = key.split('_')[-1]
                    if not (location_id := request.POST.get(f'location_{index}')):
                        return JsonResponse({
                            'success': False,
                            'errors': ['Пожалуйста, выберите локации для всех инвентарных номеров.']
                        })
                    location = Location.objects.get(id=location_id)

                    inventory_numbers = [num.strip() for num in request.POST[key].split(',') if num.strip()]
                    for number in inventory_numbers:
                        inventory_obj = InventoryNumber.objects.get(number=number)
                        location_assignments.append((inventory_obj, location))

            # Save locations for inventory numbers
            for inventory_obj, location in location_assignments:
                inventory_obj.location = location
                inventory_obj.save()

            # All validations passed, now proceed with saving
            incoming.save()

            # Associate tracker codes and inventory numbers
            tracker_inventory_map = json.loads(request.POST.get('tracker_inventory_map'))
            for tracker_code, inventory_numbers in tracker_inventory_map.items():
                tracker_code_obj = TrackerCode.objects.get(code=tracker_code)
                for inventory_number in inventory_numbers:
                    inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
                    InventoryNumberTrackerCode.objects.create(
                        tracker_code=tracker_code_obj,
                        inventory_number=inventory_number_obj
                    )
                    InventoryNumberIncoming.objects.create(
                        incoming=incoming,
                        inventory_number=inventory_number_obj
                    )

            # Activate tracker codes
            for tracker_code in tracker_codes:
                tracker_code_obj, created = TrackerCode.objects.get_or_create(
                    code=tracker_code,
                    defaults={'status': 'Active'}
                )
                tracker_code_obj.status = 'Active'
                tracker_code_obj.save()

            # Update tracker status
            if tracker.tracking_codes.filter(status='Inactive').count() == 0:
                tracker.status = 'Completed'
                tracker.save()

            incoming.tracker.add(tracker)
            update_inventory_numbers(form.cleaned_data['inventory_numbers'], incoming, occupied=True)

            # Save photos
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            return handle_incoming_status_and_redirect(incoming=incoming, request=request)
        else:
            errors = []
            for field, error_list in form.errors.items():
                for error in error_list:
                    errors.append(f'{field}: {error}')
            return JsonResponse({'success': False, 'errors': errors})
    else:
        form = IncomingForm()
        formset = PhotoFormSet()
        trackers = Tracker.objects.exclude(status="Completed")
        tags = Tag.objects.all()
        available_inventory_numbers = InventoryNumber.objects.filter(is_occupied=False)
        locations = Location.objects.all()

        return render(request, 'deliveries/incomings/incoming-new.html', {
            'form': form,
            'formset': formset,
            'tags': tags,
            'trackers': trackers,
            'available_inventory_numbers': available_inventory_numbers,
            'locations': locations,
        })


@staff_and_login_required
def incoming_edit(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    if request.method == 'POST':
        form = IncomingEditForm(request.POST, instance=incoming)
        tracker_inventory_map_raw = request.POST.getlist('tracker_inventory_map')
        tracker_inventory_map = next((json.loads(x) for x in tracker_inventory_map_raw if x.strip()), {})

        if form.is_valid():
            incoming = form.save(commit=False)
            incoming.manager = request.user
            incoming.tag = form.cleaned_data['tag']

            tracker, tracker_codes = form.cleaned_data.get('tracker')
            if not tracker:
                tracker = Tracker.objects.create(name="Трекер для " + ", ".join(tracker_codes), )

                # Привязываем коды к новому трекеру
                for code in tracker_codes:
                    tracker_code, created = TrackerCode.objects.get_or_create(code=code,
                                                                              defaults={'status': 'Active', })
                    tracker_code.tracker = tracker
                    tracker.tracking_codes.add(tracker_code)
                    tracker_code.save()
                tracker.save()

            update_inventory_and_trackers(incoming, form, tracker_inventory_map)

            new_client_phone = request.POST.get("client", "").strip()
            if new_client_phone:
                try:
                    new_client_profile = UserProfile.objects.get(phone_number=new_client_phone)
                    incoming.client = new_client_profile.user
                    if incoming.status == 'Unidentified':
                        incoming.status = 'Received'
                except UserProfile.DoesNotExist:
                    response_data = {'success': False, 'errors': [f'❌ Клиент с номером {new_client_phone} не найден!']}
                    return JsonResponse(response_data) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
                        else render(request, 'deliveries/incomings/incoming-edit.html',
                                    {'form': form, 'incoming': incoming, 'errors': response_data['errors']})

            incoming.save()
            form.save_m2m()

            # Сохраняем фото
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            # Внутри POST-обработки
            for key in request.POST:
                if key.startswith('inventory_numbers_'):
                    index = key.split('_')[-1]
                    inventory_numbers_str = request.POST[key]
                    location_id = request.POST.get(f'location_{index}')
                    if location_id:
                        location = Location.objects.get(id=location_id)
                        inventory_numbers = [num.strip() for num in inventory_numbers_str.split(',') if num.strip()]
                        for number in inventory_numbers:
                            try:
                                inventory_obj = InventoryNumber.objects.get(number=number)
                                inventory_obj.location = location
                                inventory_obj.save()
                            except InventoryNumber.DoesNotExist:
                                pass
                    else:
                        return JsonResponse(
                            {'success': False,
                             'errors': ['Пожалуйста, выберите локацию для следующих инвентарных номеров {numbers}.']})

            return handle_incoming_status_and_redirect(incoming=incoming, request=request)
        else:
            errors = []
            for field, error_list in form.errors.items():
                if field == "__all__":
                    for error in error_list:
                        errors.append(f"❌ Ошибка формы: {error}")
                else:
                    field_label = form.fields.get(field, field)
                    field_label = field_label.label if hasattr(field_label, "label") else field
                    for error in error_list:
                        errors.append(f"❌ {field_label}: {error}")

            return JsonResponse({'success': False, 'errors': errors})

    else:
        form = IncomingEditForm(instance=incoming)

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

    # ✅ Если НЕ AJAX, рендерим HTML
    return render(request, 'deliveries/incomings/incoming-edit.html', {
        'form': form,
        'incoming': incoming,
        'available_inventory_numbers': available_inventory_numbers,
        'codes_nums_map': json.dumps(codes_nums_map),
        'locs_num_map': json.dumps(locs_num_map),
        'locations': locations,
        'location_inventory_groups': location_inventory_groups,
    })


@staff_and_login_required
def incoming_list(request):
    query = request.GET.get('q', '').strip()
    incomings = Incoming.objects.exclude(
        Q(status="Unidentified") | Q(status="Template") | Q(status="Consolidated")).order_by('-arrival_date')

    if query:
        incomings = incomings.filter(
            Q(tracker__tracking_codes__code__icontains=query) |  # поиск по трек-коду
            Q(tag__name__icontains=query) |  # поиск по тегу
            Q(arrival_date__icontains=query) |  # поиск по дате прибытия
            Q(inventory_numbers__number__icontains=query) |  # поиск по инвентарным номерам
            Q(client__profile__phone_number__icontains=query) |  # поиск по номеру клиента
            Q(status__icontains=query)  # поиск по статусу
        ).distinct()

    page_obj, sort_by, sort_order = paginated_query_incoming_list(request, incomings)

    columns = incoming_columns()

    return render(request, 'deliveries/incomings/incoming-list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns
    })


@login_required
def goods_list(request):
    sort_by = request.GET.get('sort_by', 'arrival_date')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    incomings = Incoming.objects.filter(client=request.user).exclude(status="Template")

    if request.user.groups.filter(name='Clients').exists():
        try:
            relation = ClientManagerRelation.objects.get(client=request.user)
            manager = relation.manager
        except ClientManagerRelation.DoesNotExist:
            manager = None
    else:
        manager = None

    incomings = incomings.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(incomings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    columns = [
        ('tracker', 'Трек-номер'),
        ('tag__name', 'Тег'),
        ('arrival_date', 'Дата прибытия'),
        ('inventory_numbers', 'Инвентарные номера'),
        ('places_count', 'Количество мест'),
        ('manager', 'Менеджер'),
        ('status', 'Статус'),
    ]

    return render(request, 'deliveries/client-side/goods/goods-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns,
        'manager': manager,  # Передаем колонки в шаблон
    })


@login_required
def tag_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    tags = Tag.objects.all().filter(created_by=request.user)

    tags = tags.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(tags, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'deliveries/client-side/tag/tag-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': [
            ('name', 'Название'),
        ]
    })


@login_required
def tag_new(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.created_by = request.user
            tag.save()
            messages.success(request, 'Новый тег успешно создан!')
            return redirect('deliveries:list-tag')
    else:
        form = TagForm()

    return render(request, 'deliveries/client-side/tag/tag-new.html', {'form': form})


@login_required
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)

    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()

            return redirect('deliveries:list-tag')
    else:
        form = TagForm(instance=tag)

    return render(request, 'deliveries/client-side/tag/tag-edit.html', {'form': form, 'tag': tag})


@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        return redirect('deliveries:list-tag')
    return render(request, 'deliveries/client-side/tag/tag-delete.html', {'tag': tag})


@staff_and_login_required
def incoming_unidentified(request):
    query = request.GET.get('q')
    incomings = Incoming.objects.filter(status="Unidentified")
    page_obj, sort_by, sort_order = paginated_query_incoming_list(request, incomings)

    columns = incoming_columns()

    return render(request, 'deliveries/incomings/incoming-unidentified.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def incoming_templates(request):
    query = request.GET.get('q')
    incomings = Incoming.objects.filter(status="Template")
    page_obj, sort_by, sort_order = paginated_query_incoming_list(request, incomings)

    columns = incoming_columns()

    return render(request, 'deliveries/incomings/incoming-templates.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def incoming_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)
    active_tracker_codes = TrackerCode.objects.filter(tracker__incoming=incoming, status='Active')

    return render(request, 'deliveries/incomings/incoming-detail.html', {
        'incoming': incoming,
        'active_tracker_codes': active_tracker_codes
    })


@login_required
def goods_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)
    active_tracker_codes = TrackerCode.objects.filter(tracker__incoming=incoming, status='Active')

    if request.user == incoming.client:
        return render(request, 'deliveries/incomings/incoming-detail.html', {
            'incoming': incoming,
            'active_tracker_codes': active_tracker_codes
        })
    else:
        return redirect('web:profile')


@login_required
def tracker_list(request):
    page_obj, sort_by, sort_order, hide_completed = paginated_query_trackers_list(request)

    columns = trackers_list_columns()

    return render(request, 'deliveries/client-side/tracker/tracker-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns,
        'hide_completed': hide_completed,
    })


@login_required
def tracker_new(request):
    if request.method == 'POST':
        form = TrackerForm(request.POST)
        if form.is_valid():
            tracker = form.save(commit=False)
            tracker.created_by = request.user
            tracker.save()

            # Получаем список кодов из формы
            code_list = form.cleaned_data['tracking_codes']
            tracking_codes = []
            for code in code_list:
                tracker_code, created = TrackerCode.objects.get_or_create(code=code, status="Inactive")
                tracking_codes.append(tracker_code)

            # Создаем объекты TrackerCode и привязываем к трекеру
            for code in tracking_codes:
                tracker_code = TrackerCode.objects.get(code=code)
                tracker_code.created_by = request.user
                tracker_code.save()
                tracker.tracking_codes.add(tracker_code)

            tracker.save()
            messages.success(request, 'Новый трекер успешно создан!')
            return redirect('deliveries:list-tracker')
    else:
        form = TrackerForm()

    return render(request, 'deliveries/client-side/tracker/tracker-new.html', {'form': form})


@staff_and_login_required
@transaction.atomic
def new_consolidation(request):
    if request.method == 'POST':
        if 'in_work' in request.POST:
            selected_incomings_ids = request.POST.getlist('selected_incomings')[0].split(",")
        else:
            selected_incomings_ids = request.POST.getlist('selected_incomings')
        selected_incomings = []
        if selected_incomings_ids and selected_incomings_ids[0] != '':
            for incoming_id in selected_incomings_ids:
                incoming = get_object_or_404(Incoming, pk=incoming_id)
                selected_incomings.append(incoming)

        form = ConsolidationForm(request.POST)

        if form.is_valid():
            consolidation = form.save(commit=False)
            consolidation.manager = request.user
            consolidation.client = form.cleaned_data['client']
            consolidation.track_code = form.cleaned_data['track_code']

            if 'in_work' in request.POST:
                consolidation.status = 'Packaging'
            else:
                consolidation.status = 'Error'

            consolidation.save()
            form.save_m2m()

            if consolidation.status != 'Template':
                for incoming in selected_incomings:
                    incoming_id = str(incoming.pk)
                    consolidation_incoming = ConsolidationIncoming.objects.create(
                        consolidation=consolidation,
                        incoming=incoming,
                        places_consolidated=incoming.places_count
                    )
                    incoming.status = "Consolidated"

                    inventory_data = json.loads(request.POST.get("selected_inventory", "{}"))
                    inventory_numbers = inventory_data.get(incoming_id, [])
                    for inventory_number in inventory_numbers:
                        inventory_obj = InventoryNumber.objects.get(number=inventory_number)
                        ConsolidationInventory.objects.create(
                            consolidation_incoming=consolidation_incoming,
                            inventory_number=inventory_obj
                        )
                    incoming.save()

                # Обработка мест
                places_data = {}
                for key, value in request.POST.items():
                    if key.startswith('inventory_numbers_'):
                        place_index = key.split('_')[-1]
                        inventory_numbers = [num.strip() for num in value.split(',') if num.strip()]
                        weight = request.POST.get(f'weight_consolidated_{place_index}', 0)
                        volume = request.POST.get(f'volume_consolidated_{place_index}', 0)
                        place_code = request.POST.get(f'place_consolidated_{place_index}', '')
                        package_type = request.POST.get(f'package_type_{place_index}', '')
                        places_data[place_index] = {
                            'inventory_numbers': inventory_numbers,
                            'weight': float(weight) if weight else 0,
                            'volume': float(volume) if volume else 0,
                            'place_code': place_code,
                            'package_type': package_type,
                        }

                consolidation_price = 0
                for place_data in places_data.values():
                    package_type = PackageType.objects.get(name=place_data['package_type'])
                    consolidation_price += package_type.price
                    place = Place.objects.create(
                        consolidation=consolidation,
                        place_code=place_data['place_code'],
                        package_type=package_type,
                    )
                    inventory_objs = InventoryNumber.objects.filter(number__in=place_data['inventory_numbers'])
                    place.inventory_numbers.set(inventory_objs)

                consolidation.price = consolidation_price
                consolidation.save()
                consolidation.incomings.set(selected_incomings)

            return redirect('deliveries:list-consolidation')

        else:
            messages.error(request, form.errors)

    else:
        form = ConsolidationForm()

    # Получаем все инкаминги, которые не были выбраны
    try:
        incomings = Incoming.objects.exclude(
            Q(id__in=selected_incomings_ids) |
            Q(status='Unidentified') |
            Q(status='Template') |
            Q(status='Consolidated')
        )
    except UnboundLocalError:
        incomings = Incoming.objects.exclude(
            Q(status='Unidentified') |
            Q(status='Template') |
            Q(status='Consolidated')
        )

    try:
        selected_incomings = Incoming.objects.filter(id__in=selected_incomings_ids)
    except UnboundLocalError:
        selected_incomings = []

    incomings_data = prepare_incoming_data(incomings)
    initial_incomings_data = prepare_incoming_data(selected_incomings)
    package_types = list(PackageType.objects.values_list('name', flat=True))

    return render(request, 'deliveries/outcomings/consolidation-new.html', {
        'form': form,
        'incomings': incomings,
        'selected_incomings': selected_incomings,
        'consolidation_code': ConsolidationCode.generate_code(),
        'incomings_data': incomings_data,
        'initial_incomings_data': initial_incomings_data,
        'package_types': package_types,
    })


@login_required
def tracker_detail(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk)  # Получаем объект по первичному ключу (id)
    return render(request, 'deliveries/client-side/tracker/tracker-detail.html', {'tracker': tracker})


@login_required
def tracker_delete(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk)
    if request.method == 'POST':
        tracker.delete()
        return redirect('deliveries:list-tracker')
    return render(request, 'deliveries/client-side/tracker/tracker-delete.html', {'tracker': tracker})


@login_required
def tracker_edit(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk)

    if request.method == 'POST':
        form = TrackerForm(request.POST, instance=tracker)
        if form.is_valid():
            tracker = form.save(commit=False)

            tracking_codes = form.cleaned_data['tracking_codes']

            # Создаем объекты TrackerCode и привязываем к трекеру
            for code in tracking_codes:
                tracker_code = TrackerCode.objects.get(code=code)
                tracker_code.created_by = request.user
                tracker_code.save()
                tracker.tracking_codes.add(tracker_code)

            tracker.save()

            return redirect('deliveries:list-tracker')
    else:
        form = TrackerForm(instance=tracker)

    return render(request, 'deliveries/client-side/tracker/tracker-edit.html', {'form': form, 'tracker': tracker})


@staff_and_login_required
def incoming_delete(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    inventory_numbers = incoming.inventory_numbers.all()
    update_inventory_numbers(inventory_numbers, incoming, occupied=False)

    if request.method == 'POST':
        incoming.delete()
        return redirect('deliveries:list-incoming')
    return render(request, 'deliveries/incomings/incoming-delete.html', )


@staff_and_login_required
def consolidation_list(request):
    page_obj, sort_by, sort_order = paginated_query_consolidation_list(request,
                                                                       consolidations=Consolidation.objects.all())

    columns = consolidation_columns()

    return render(request, 'deliveries/outcomings/consolidation-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


def packaged_list(request):
    consolidations = Consolidation.objects.filter(
        Q(status='Packaged') | Q(status="Sent") | Q(status="Delivered")).annotate(
        total_weight=Sum('places__weight')
    )
    statuses = PackagedStatuses.choices

    page_obj, sort_by, sort_order = paginated_query_consolidation_list(request, consolidations)

    columns = packaged_columns()

    return render(request, 'deliveries/outcomings/packaged-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns,
        'statuses': statuses,
    })


@staff_and_login_required
def update_consolidation_status(request, pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')

            if new_status not in dict(PackagedStatuses.choices).keys():
                return JsonResponse({'error': 'Invalid status'}, status=400)

            consolidation = get_object_or_404(Consolidation, pk=pk)
            consolidation.status = new_status
            consolidation.save()

            return JsonResponse({'status': consolidation.status})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)


@staff_and_login_required
def package_new(request, pk):
    consolidation = get_object_or_404(Consolidation, pk=pk)

    if request.method == 'POST':
        form = PackageForm(request.POST, instance=consolidation)

        if form.is_valid():
            consolidation = form.save(commit=False)

            # Получаем данные о местах из формы
            places_data = {}
            total_volume = 0
            total_weight = 0
            for key, value in request.POST.items():
                if key.startswith('inventory_numbers_'):
                    place_index = key.split('_')[-1]
                    inventory_numbers = [num.strip() for num in value.split(',') if num.strip()]
                    weight = request.POST.get(f'weight_consolidated_{place_index}', 0)
                    volume = request.POST.get(f'volume_consolidated_{place_index}', 0)
                    place_code = request.POST.get(f'place_consolidated_{place_index}', '')
                    package_type = request.POST.get(f'package_type_{place_index}', '')
                    places_data[place_index] = {
                        'inventory_numbers': inventory_numbers,
                        'weight': float(weight) if weight else 0,
                        'volume': float(volume) if volume else 0,
                        'place_code': place_code,
                        'package_type': package_type,
                    }
                    total_volume += float(volume)
                    total_weight += float(weight)

            total_density = total_weight / total_volume
            tariff = DeliveryPriceRange.objects.filter(
                delivery_type=consolidation.delivery_type,
                min_density__lte=total_density,
                max_density__gte=total_density
            ).first()

            consolidation.price += float(tariff.price_per_kg) * total_weight

            # Сохраняем места
            with transaction.atomic():
                # Удаляем существующие места
                consolidation.places.all().delete()

                # Создаём новые места
                for place_index, place_data in places_data.items():
                    package_type = PackageType.objects.get(name=place_data['package_type'])
                    place = Place.objects.create(
                        consolidation=consolidation,
                        place_code=place_data['place_code'],
                        weight=place_data['weight'],
                        volume=place_data['volume'],
                        package_type=package_type,
                    )
                    # Привязываем инвентарные номера
                    inventory_objs = InventoryNumber.objects.filter(number__in=place_data['inventory_numbers'])
                    place.inventory_numbers.set(inventory_objs)

                    # Обработка загруженных фотографий для этого места
                    photo_files = request.FILES.getlist(f'photos_{place_index}')
                    for photo_file in photo_files:
                        photo = Photo(photo=photo_file, place=place)
                        photo.save()

            # Обновляем статус консолидации
            if 'in_work' in request.POST:
                consolidation.status = "Packaged"
            else:
                consolidation.status = "Draft"

            consolidation.save()
            return redirect('deliveries:list-consolidation')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PackageForm(instance=consolidation)

    # Получаем допустимые инвентарные номера для отображения в шаблоне
    valid_numbers = list(ConsolidationInventory.objects.filter(
        consolidation_incoming__consolidation=consolidation
    ).values_list('inventory_number__number', flat=True).distinct())

    # Получаем существующие места для автозаполнения
    places = consolidation.places.all()
    places_data = []
    for place in places:
        inventory_numbers = list(place.inventory_numbers.values_list('number', flat=True))
        photos = list(place.images_set_place.all())  # Получаем фотографии для места
        places_data.append({
            'place_code': place.place_code,
            'weight': place.weight,
            'volume': place.volume,
            'package_type': place.package_type.name,
            'inventory_numbers': inventory_numbers,
            'photos': photos,
        })

    package_types = list(PackageType.objects.values_list('name', flat=True))

    return render(request, 'deliveries/outcomings/package.html', {
        'form': form,
        'consolidation': consolidation,
        'consolidation_inventory_numbers': valid_numbers,
        'places_data': places_data,
        'package_types': package_types,
    })


@staff_and_login_required
@transaction.atomic
def consolidation_edit(request, pk):
    consolidation = get_object_or_404(Consolidation, pk=pk)
    if request.method == 'POST':
        form = ConsolidationForm(request.POST, instance=consolidation)
        if form.is_valid():
            consolidation = form.save(commit=False)
            consolidation.manager = request.user

            # Обработка выбранных поступлений
            selected_incomings_ids = request.POST.get('selected_incomings', '').split(',')
            selected_incomings_ids = [id for id in selected_incomings_ids if id]  # Удаляем пустые ID
            selected_incomings = Incoming.objects.filter(id__in=selected_incomings_ids)

            # Обработка инвентарных номеров
            try:
                inventory_data = json.loads(request.POST.get("selected_inventory", "{}"))
                places_data = json.loads(request.POST.get("places_data", "[]"))
            except json.JSONDecodeError:
                messages.error(request, "Ошибка в данных инвентарных номеров или мест. Пожалуйста, проверьте выбор.")
                return redirect('deliveries:consolidation-edit', pk=pk)

            # Установка статуса консолидации
            if 'save_draft' in request.POST:
                consolidation.status = 'Template'
            elif 'in_work' in request.POST:
                consolidation.status = 'Packaging'

            consolidation.save()
            form.save_m2m()

            # Очистка старых связей ConsolidationIncoming
            ConsolidationIncoming.objects.filter(consolidation=consolidation).delete()

            # Создание новых связей с поступлениями
            for incoming in selected_incomings:
                incoming_id = str(incoming.id)
                inventory_numbers = inventory_data.get(incoming_id, [])
                places_consolidated = len(inventory_numbers) if inventory_numbers else 0

                if places_consolidated == 0:
                    messages.error(request, f'Для поступления #{incoming_id} не выбраны инвентарные номера.')
                    return redirect('deliveries:consolidation-edit', pk=pk)

                consolidation_incoming = ConsolidationIncoming.objects.create(
                    consolidation=consolidation,
                    incoming=incoming,
                    places_consolidated=places_consolidated
                )

                for inventory_number in inventory_numbers:
                    inventory_obj = InventoryNumber.objects.get(number=inventory_number)
                    ConsolidationInventory.objects.create(
                        consolidation_incoming=consolidation_incoming,
                        inventory_number=inventory_obj
                    )

                incoming.status = "Consolidated"
                incoming.save()

            # Обработка мест
            consolidation.places.all().delete()
            consolidation_price = 0
            for place_data in places_data:
                package_type = PackageType.objects.get(name=place_data['package_type'])
                consolidation_price += package_type.price
                place = Place.objects.create(
                    consolidation=consolidation,
                    place_code=place_data['place_code'],
                    package_type=package_type,
                )
                inventory_objs = InventoryNumber.objects.filter(number__in=place_data['inventory_numbers'])
                place.inventory_numbers.set(inventory_objs)

            # Обновление связи консолидации с поступлениями
            consolidation.price = consolidation_price
            consolidation.save()
            consolidation.incomings.set(selected_incomings)

            messages.success(request, 'Консолидация успешно обновлена.')
            return redirect('deliveries:list-consolidation')
        else:
            messages.error(request, 'Ошибка при редактировании консолидации. Проверьте данные.')
    else:
        form = ConsolidationForm(instance=consolidation)

    # Подготовка данных для шаблона
    selected_incomings = consolidation.incomings.all()
    incomings = Incoming.objects.exclude(
        Q(id__in=selected_incomings.values_list('id', flat=True)) |
        Q(status='Unidentified') |
        Q(status='Template') |
        Q(status='Consolidated')
    )
    incomings_data = prepare_incoming_data(incomings)
    initial_incomings_data = prepare_incoming_data(selected_incomings)
    package_types = list(PackageType.objects.values_list('name', flat=True))

    # Подготовка данных об инвентарных номерах
    initial_inventory_data = {}
    for incoming in selected_incomings:
        inventory_numbers = ConsolidationInventory.objects.filter(
            consolidation_incoming__consolidation=consolidation,
            consolidation_incoming__incoming=incoming
        ).values_list('inventory_number__number', flat=True)
        initial_inventory_data[str(incoming.id)] = list(inventory_numbers)

    # Подготовка данных о местах
    places = consolidation.places.all()
    places_data = []
    for place in places:
        inventory_numbers = list(place.inventory_numbers.values_list('number', flat=True))
        places_data.append({
            'place_code': place.place_code,
            'package_type': place.package_type.name,
            'inventory_numbers': inventory_numbers,
        })

    return render(request, 'deliveries/outcomings/consolidation-edit.html', {
        'form': form,
        'consolidation': consolidation,
        'incomings': incomings,
        'incomings_data': incomings_data,
        'initial_incomings_data': initial_incomings_data,
        'package_types': package_types,
        'initial_inventory_data': initial_inventory_data,
        'places_data': places_data,
    })


@staff_and_login_required
def generate_inventory_numbers(request):
    if request.method == 'POST':
        form = GenerateInventoryNumbersForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            # Найти последний инвентарный номер
            last_number = InventoryNumber.objects.order_by('-number').first()
            if last_number:
                match = re.match(r'INV(\d+)', last_number.number)
                if match:
                    num = int(match.group(1))
                else:
                    num = 0
            else:
                num = 0
            # Генерировать новые номера
            new_numbers = []
            for i in range(1, count + 1):
                next_num = num + i
                next_number = f'INV{next_num}'  # Формат без padding: INV1, INV2 и т.д.
                new_numbers.append(next_number)
            # Сохранить новые инвентарные номера
            for number in new_numbers:
                InventoryNumber.objects.create(number=number, is_occupied=False)
            # Генерировать PDF с измененными размерами
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="inventory_numbers.pdf"'
            p = canvas.Canvas(response, pagesize=(3.5 * inch, 2.0 * inch))  # Увеличена ширина, уменьшена высота
            for number in new_numbers:
                # Нарисовать дату в правом верхнем углу
                p.setFont("Helvetica", 8)
                date_str = datetime.now().strftime("%Y-%m-%d")
                p.drawRightString(3.5 * inch - 10, 2.0 * inch - 10, date_str)
                # Нарисовать штрихкод в центре
                barcode = code128.Code128(number, barHeight=50)  # Уменьшена высота штрихкода
                barcode_width = barcode.width
                x = (3.5 * inch - barcode_width) / 2
                y = (2.0 * inch - 50) / 2
                barcode.drawOn(p, x, y)
                # Нарисовать инвентарный номер внизу
                p.setFont("Helvetica", 10)
                p.drawCentredString(3.5 * inch / 2, 10, number)
                p.showPage()
            p.save()
            return response
    else:
        form = GenerateInventoryNumbersForm()
    return render(request, 'deliveries/generate_inventory_numbers.html', {'form': form})


@staff_and_login_required
def search_users(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(profile__phone_number__icontains=query)  # Поиск по номеру телефона в UserProfile
    ).select_related('profile').distinct()

    results = [
        {
            'id': user.id,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'phone_number': user.profile.phone_number if hasattr(user, 'profile') else None
        }
        for user in users
    ]

    return JsonResponse(results, safe=False)


@staff_and_login_required
def get_tariff(request):
    try:
        density = float(request.GET.get('density', '').strip())
        delivery_type_name = request.GET.get('delivery_type', '').strip()

        delivery_type = DeliveryType.objects.get(name=delivery_type_name)

        try:
            price = DeliveryPriceRange.objects.filter(
                delivery_type=delivery_type,
                min_density__lte=density,
                max_density__gte=density,
            ).first().price_per_kg

        except AttributeError:
            price = 0

        return JsonResponse({'price_per_kg': price})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def location_new(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            Location.objects.create(name=name, created_by=request.user)
            return redirect('deliveries:list-location')
    else:
        form = LocationForm()
    return render(request, 'deliveries/location/create_location.html', {'form': form})


@staff_and_login_required
def location_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    locations = Location.objects.all()

    locations = locations.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(locations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
    ]

    return render(request, 'deliveries/location/location_list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()

            return redirect('deliveries:list-location')
    else:
        form = LocationForm(instance=location)

    return render(request, 'deliveries/location/location_edit.html',
                  {'form': form, 'location': location})


@staff_and_login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        location.delete()
        return redirect('deliveries:list-location')
    return render(request, 'deliveries/location/location_delete.html', {'location': location})


def delivery_type_new(request):
    if request.method == 'POST':
        form = DeliveryTypeForm(request.POST)
        formset = DeliveryPriceRangeFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            delivery_type = form.save()
            formset.instance = delivery_type
            formset.save()
            return redirect('deliveries:list-delivery-type')
    else:
        form = DeliveryTypeForm()
        formset = DeliveryPriceRangeFormSet()
    return render(request, 'deliveries/delivery_type/create_delivery_type.html', {'form': form, 'formset': formset})


@staff_and_login_required
def delivery_type_edit(request, pk):
    delivery_type = get_object_or_404(DeliveryType, pk=pk)

    if request.method == 'POST':
        form = DeliveryTypeForm(request.POST, instance=delivery_type)
        formset = DeliveryPriceRangeFormSet(request.POST, instance=delivery_type)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            return redirect('deliveries:list-delivery-type')
    else:
        form = DeliveryTypeForm(instance=delivery_type)
        formset = DeliveryPriceRangeFormSet(instance=delivery_type)

    return render(request, 'deliveries/delivery_type/delivery_type_edit.html',
                  {'form': form, 'delivery_type': delivery_type, 'formset': formset})


def package_type_new(request):
    if request.method == 'POST':
        form = PackageTypeForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            price = form.cleaned_data['price']
            description = form.cleaned_data['description']
            PackageType.objects.create(name=name, price=price, description=description)
            return redirect('deliveries:list-package-type')
    else:
        form = PackageTypeForm()
    return render(request, 'deliveries/package_type/create_package_type.html', {'form': form})


@staff_and_login_required
def package_type_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    package_types = PackageType.objects.all()

    package_types = package_types.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(package_types, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
        ('price', 'Цена'),
        ('description', 'Описание')
    ]

    return render(request, 'deliveries/package_type/package_type_list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def package_type_edit(request, pk):
    package_type = get_object_or_404(PackageType, pk=pk)

    if request.method == 'POST':
        form = PackageTypeForm(request.POST, instance=package_type)
        if form.is_valid():
            form.save()

            return redirect('deliveries:list-package-type')
    else:
        form = PackageTypeForm(instance=package_type)

    return render(request, 'deliveries/package_type/package_type_edit.html',
                  {'form': form, 'package_type': package_type})


@staff_and_login_required
def package_type_delete(request, pk):
    package_type = get_object_or_404(PackageType, pk=pk)
    if request.method == 'POST':
        package_type.delete()
        return redirect('deliveries:list-package-type')
    return render(request, 'deliveries/package_type/package_type_delete.html', {'package_type': package_type})


@staff_and_login_required
def delivery_type_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    delivery_types = DeliveryType.objects.all()

    delivery_types = delivery_types.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(delivery_types, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
        ('eta', 'Примерное время доставки')
    ]

    return render(request, 'deliveries/delivery_type/delivery_type_list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def delivery_type_delete(request, pk):
    delivery_type = get_object_or_404(DeliveryType, pk=pk)
    if request.method == 'POST':
        delivery_type.delete()
        return redirect('deliveries:list-delivery-type')
    return render(request, 'deliveries/delivery_type/delivery_type_delete.html', {'delivery_type': delivery_type})


def edit_delivery_price(request, pk):
    consolidation = get_object_or_404(Consolidation, pk=pk)

    if request.method == 'POST':
        consolidation.price = request.POST.get('total_price')
        consolidation.save()
        return redirect('deliveries:packaged-list')

    packages_price = \
        Place.objects.filter(consolidation=consolidation).aggregate(total_price=Sum('package_type__price'))[
            'total_price']
    weight = \
        Place.objects.filter(consolidation=consolidation).aggregate(total_weight=Sum('weight'))[
            'total_weight']
    volume = \
        Place.objects.filter(consolidation=consolidation).aggregate(total_volume=Sum('volume'))['total_volume']
    density = weight / volume
    tariff = DeliveryPriceRange.objects.filter(
        delivery_type=consolidation.delivery_type,
        min_density__lte=density,
        max_density__gte=density,
    ).first().price_per_kg
    delivery_types = DeliveryType.objects.all()

    return render(request, 'deliveries/outcomings/edit-delivery-price.html',
                  {'consolidation': consolidation, 'packages_price': packages_price, 'weight': weight, 'volume': volume,
                   'density': density, 'delivery_types': delivery_types, 'tariff': tariff})
