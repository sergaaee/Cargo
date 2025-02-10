import json

from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from .choices import PackageType  # Импортируем PackageType

from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404

from user_profile.models import ClientManagerRelation, UserProfile
from .utils import staff_and_login_required, login_required, update_inventory_numbers, incoming_columns, \
    paginated_query_incoming_list, prepare_incoming_data, consolidation_columns, paginated_query_consolidation_list

from .forms import IncomingForm, PhotoFormSet, TagForm, TrackerForm, IncomingFormEdit, ConsolidationForm, PackageForm
from .models import Tag, Photo, Incoming, InventoryNumber, Tracker, TrackerCode, InventoryNumberTrackerCode, \
    ConsolidationCode, Consolidation, ConsolidationIncoming, InventoryNumberIncoming
from django.http import JsonResponse


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
        formset = PhotoFormSet(request.POST, request.FILES)

        errors = []

        # Получаем введенный номер телефона
        client_phone = request.POST.get("client", "").strip()

        if form.is_valid():
            incoming = form.save(commit=False)
            incoming.manager = request.user
            incoming.tag = form.cleaned_data['tag']

            tracker, tracker_codes = form.cleaned_data.get('tracker')

            # 🔹 Если клиент введён вручную, проверяем его
            if client_phone:
                try:
                    client_profile = UserProfile.objects.get(phone_number=client_phone)
                    incoming.client = client_profile.user
                except UserProfile.DoesNotExist:
                    return JsonResponse({'success': False, 'errors': [f'❌ Клиент с номером {client_phone} не найден!']})


            else:
                # 🔹 Используем стандартную логику
                if tracker.created_by:
                    incoming.client = tracker.created_by
                elif incoming.tag and incoming.tag.created_by:
                    incoming.client = incoming.tag.created_by
                else:
                    incoming.status = 'Unidentified'
                    incoming.client = None

            # 🔹 Проверка трек-кодов и тегов на владельца
            conflicting_items = []

            # Проверяем, не принадлежат ли трек-коды другому клиенту
            for tracker_code in tracker_codes:
                tracker_code_obj = TrackerCode.objects.filter(code=tracker_code).first()
                if tracker_code_obj and tracker_code_obj.created_by and tracker_code_obj.created_by != incoming.client:
                    conflicting_items.append(f'❌ Трек-код {tracker_code} принадлежит другому клиенту!')

            # Проверяем, не принадлежит ли метка другому клиенту
            if incoming.tag and incoming.tag.created_by and incoming.tag.created_by != incoming.client:
                conflicting_items.append(f'❌ Метка "{incoming.tag.name}" принадлежит другому клиенту!')

            # Если есть конфликты, не сохраняем и показываем ошибку
            if conflicting_items:
                return JsonResponse({'success': False, 'errors': conflicting_items})

            incoming.save()

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

            # Активируем трек-коды
            for tracker_code in tracker_codes:
                tracker_code_obj, created = TrackerCode.objects.get_or_create(code=tracker_code,
                                                                              defaults={'status': 'Active'})
                tracker_code_obj.status = 'Active'
                tracker_code_obj.save()

            # Привязываем трекер
            incoming.tracker.add(tracker)

            update_inventory_numbers(form.cleaned_data['inventory_numbers'], incoming, occupied=True)

            # Сохраняем фотографии
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            if tracker.tracking_codes.filter(status='Inactive').count() == 0:
                tracker.status = 'Completed'
                tracker.save()

            return JsonResponse({'success': True, 'redirect_url': reverse('deliveries:list-incoming')})
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

    return render(request, 'deliveries/incomings/incoming-new.html', {
        'form': form,
        'formset': formset,
        'tags': tags,
        'trackers': trackers,
        'available_inventory_numbers': available_inventory_numbers,
    })


@staff_and_login_required
def incoming_edit(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    if request.method == 'POST':
        form = IncomingFormEdit(request.POST, instance=incoming)

        if form.is_valid():
            incoming = form.save(commit=False)
            incoming.manager = request.user
            incoming.tag = form.cleaned_data['tag']
            new_client_phone = request.POST.get("client", "").strip()
            old_client = incoming.client

            errors = []

            # 🔹 Проверяем клиента, если он изменился
            if new_client_phone and (not old_client or old_client.profile.phone_number != new_client_phone):
                try:
                    new_client_profile = UserProfile.objects.get(phone_number=new_client_phone)
                    incoming.client = new_client_profile.user
                    incoming.status = 'Received'
                except UserProfile.DoesNotExist:
                    errors.append(f'❌ Клиент с номером {new_client_phone} не найден!')

            incoming.save()

            # Получаем старые и новые инвентарные номера
            new_inventory_numbers = set(form.cleaned_data['inventory_numbers'])
            initial_inventory_numbers = set(request.POST.get('initial_inventory_numbers', '').split(','))

            removed_inventory_numbers = initial_inventory_numbers - new_inventory_numbers
            # update_inventory_numbers(removed_inventory_numbers, incoming, occupied=False)
            # update_inventory_numbers(new_inventory_numbers, incoming, occupied=True)

            # Сохраняем фото
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            if errors:
                return JsonResponse({'success': False, 'errors': errors})

            return JsonResponse({'success': True, 'redirect_url': reverse('deliveries:list-incoming')})
        else:
            errors = [f'{field}: {error}' for field, error_list in form.errors.items() for error in error_list]
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = IncomingFormEdit(instance=incoming)

    active_tracker_codes = TrackerCode.objects.filter(tracker__incoming=incoming, status='Active')
    tags = Tag.objects.all()
    trackers = Tracker.objects.all()
    available_inventory_numbers = InventoryNumber.objects.filter(is_occupied=False)

    return render(request, 'deliveries/incomings/incoming-edit.html',
                  {'form': form, 'incoming': incoming, 'tags': tags, 'trackers': trackers,
                   'available_inventory_numbers': available_inventory_numbers,
                   'active_tracker_codes': active_tracker_codes})


@staff_and_login_required
def incoming_list(request):
    query = request.GET.get('q', '').strip()
    incomings = Incoming.objects.exclude(status="Unidentified")

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
        # Пытаемся получить связь, где текущий пользователь является клиентом
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

    # Добавляем колонки с метками для отображения в таблице
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

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
    ]

    return render(request, 'deliveries/client-side/tag/tag-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
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
def incoming_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    # Получаем только активные трек-коды
    active_tracker_codes = TrackerCode.objects.filter(tracker__incoming=incoming, status='Active')

    return render(request, 'deliveries/incomings/incoming-detail.html', {
        'incoming': incoming,
        'active_tracker_codes': active_tracker_codes
    })


@login_required
def goods_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    # Получаем только активные трек-коды
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
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')
    hide_completed = request.GET.get('hide_completed', '')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    trackers = Tracker.objects.filter(created_by=request.user)

    trackers = trackers.order_by(f'{order_prefix}{sort_by}')

    if hide_completed == 'on':
        trackers = trackers.exclude(status='Completed')

    paginator = Paginator(trackers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
        ('tracking_codes', 'Коды'),
        ('source', 'Источник'),
        ('status', 'Статус')
    ]

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
            tracking_codes = form.cleaned_data['tracking_codes']

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


@login_required
@transaction.atomic  # Используем транзакцию для обеспечения целостности данных
def new_consolidation(request):
    if request.method == 'POST':
        selected_incomings_ids = request.POST.getlist('selected_incomings')[0].split(",")
        selected_incomings = []
        if selected_incomings_ids:
            for incoming_id in selected_incomings_ids:
                incoming = Incoming.objects.get(pk=incoming_id)
                selected_incomings.append(Incoming.objects.get(pk=incoming_id))
                incoming.status = "Consolidated"
                incoming.save()

            form = ConsolidationForm(request.POST)
            if form.is_valid():
                # Создаем объект консолидации без сохранения в базу
                consolidation = form.save(commit=False)
                consolidation.manager = request.user
                consolidation.client = form.cleaned_data['client']
                consolidation.track_code = form.cleaned_data['track_code']

                if 'save_draft' in request.POST:
                    consolidation.status = 'Template'
                elif 'in_work' in request.POST:
                    consolidation.status = 'Packaging'

                consolidation.save()

                form.save_m2m()  # Сохраняем ManyToMany отношения

                # Обрабатываем выбранные поступления и количество мест
                incoming_data = request.POST.getlist('incoming_inv')
                places_data = request.POST.getlist('places_consolidated')

                # Загружаем все инкаминги одним запросом, чтобы избежать N+1 проблемы
                incoming_objects = Incoming.objects.filter(inventory_numbers__number__in=incoming_data).distinct()

                for incoming_inv, places in zip(incoming_data, places_data):
                    try:
                        incoming = incoming_objects.get(inventory_numbers__number=incoming_inv)
                        ConsolidationIncoming.objects.create(
                            consolidation=consolidation,
                            incoming=incoming,
                            places_consolidated=places
                        )
                    except Incoming.DoesNotExist:
                        messages.error(request, f'Incoming with inventory number {incoming_inv} not found.')
                        return redirect('deliveries:list-consolidation')

                # Устанавливаем связанные инкаминги
                consolidation.incomings.set(selected_incomings)
                consolidation.save()

                return redirect('deliveries:list-consolidation')

        else:
            messages.error(request, 'Вы не выбрали ни одного постуления.')
            return redirect('deliveries:list-consolidation')

    else:
        form = ConsolidationForm()

    # Получаем все инкаминги, которые не были выбраны
    try:
        incomings = Incoming.objects.exclude(
            Q(id__in=selected_incomings_ids) | Q(status='Unidentified')
        )
    except UnboundLocalError:
        incomings = Incoming.objects.all()

    try:
        selected_incomings = Incoming.objects.filter(id__in=selected_incomings_ids)
    except UnboundLocalError:
        selected_incomings = []

    incomings_data = prepare_incoming_data(incomings)
    initial_incomings_data = prepare_incoming_data(selected_incomings)

    package_types = PackageType.choices

    return render(request, 'deliveries/outcomings/consolidation-new.html', {
        'form': form,
        'incomings': incomings,
        'selected_incomings': selected_incomings,
        'consolidation_code': ConsolidationCode.generate_code(),
        'incomings_data': incomings_data,
        'initial_incomings_data': initial_incomings_data,
        'package_types': package_types,
        'users': UserProfile.objects.filter(user__groups__name="Clients"),
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
    consolidations = Consolidation.objects.all()
    page_obj, sort_by, sort_order = paginated_query_consolidation_list(request, consolidations)

    columns = consolidation_columns()

    return render(request, 'deliveries/outcomings/consolidation-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@staff_and_login_required
def package_new(request, pk):
    consolidation = get_object_or_404(Consolidation, pk=pk)

    if request.method == 'POST':
        incomings_data = {incoming.id: incoming for incoming in consolidation.incomings.all()}
        form = PackageForm(request.POST, instance=consolidation, incomings_data=incomings_data)

        if form.is_valid():
            consolidation = form.save()

            incoming_ids = request.POST.getlist('incoming_id')
            weights = request.POST.getlist('weight_consolidated')
            volumes = request.POST.getlist('volume_consolidated')

            for incoming_id, weight, volume in zip(incoming_ids, weights, volumes):
                incoming = Incoming.objects.get(pk=incoming_id)
                consolidation_incoming = ConsolidationIncoming.objects.get(
                    consolidation=consolidation,
                    incoming=incoming,
                )
                consolidation_incoming.weight_consolidated = weight
                consolidation_incoming.volume_consolidated = volume

                consolidation_incoming.save()

            consolidation.status = "Packaged"
            consolidation.save()

            messages.success(request, 'Данные упаковки успешно обновлены!')
            return redirect('deliveries:list-consolidation')
    else:
        form = PackageForm(instance=consolidation)

    incomings = consolidation.incomings.all()
    return render(request, 'deliveries/outcomings/package.html', {
        'form': form,
        'consolidation': consolidation,
        'incomings': incomings,
    })


@staff_and_login_required
def consolidation_edit(request, pk):
    consolidation = get_object_or_404(Consolidation, pk=pk)

    if request.method == 'POST':
        form = ConsolidationForm(request.POST, instance=consolidation)
        if form.is_valid():
            if 'save_draft' in request.POST:
                consolidation.status = 'Template'
            elif 'in_work' in request.POST:
                consolidation.status = 'Packaging'

            form.save()
            messages.success(request, 'Консолидация успешно отредактирована!')
            return redirect('deliveries:list-consolidation')
    else:
        form = ConsolidationForm(instance=consolidation)

    package_types = PackageType.choices

    return render(request, 'deliveries/outcomings/consolidation-edit.html', {
        'form': form,
        'consolidation': consolidation,
        'package_types': package_types,
    })


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
