import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404

from user_profile.models import ClientManagerRelation
from .utils import staff_and_login_required, login_required, update_inventory_numbers, incoming_columns, \
    paginated_query_incoming_list

from .forms import IncomingForm, PhotoFormSet, TagForm, TrackerForm, IncomingFormEdit
from .models import Tag, Photo, Incoming, InventoryNumber, Tracker, TrackerCode, InventoryNumberTrackerCode
from django.http import JsonResponse
from django.db.models import CharField
from django.db.models.functions import Cast


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

        if form.is_valid():
            incoming = form.save(commit=False)
            incoming.manager = request.user
            incoming.tag = form.cleaned_data['tag']

            # Получаем трекер и трек-коды
            tracker, tracker_codes = form.cleaned_data.get('tracker')

            if tracker.created_by is None:
                if incoming.tag:
                    if incoming.tag.created_by is None:
                        incoming.status = 'Unidentified'
                    else:
                        incoming.client = incoming.tag.created_by
                else:
                    incoming.status = 'Unidentified'
                    incoming.client = None
            else:
                incoming.client = tracker.created_by
            incoming.save()

            # Привязываем трек-коды к трекеру и обновляем их статус
            tracker_inventory_map = json.loads(request.POST.get('tracker_inventory_map'))
            for tracker_code, inventory_numbers in tracker_inventory_map.items():
                tracker_code_obj = TrackerCode.objects.get(code=tracker_code)

                for inventory_number in inventory_numbers:
                    inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
                    InventoryNumberTrackerCode.objects.create(
                        tracker_code=tracker_code_obj,
                        inventory_number=inventory_number_obj
                    )

            for tracker_code in tracker_codes:
                try:
                    tracker_code_obj = TrackerCode.objects.get(code=tracker_code)
                    tracker_code_obj.status = 'Active'
                    tracker_code_obj.save()
                except TrackerCode.DoesNotExist:
                    tracker_code_obj = TrackerCode.objects.create(code=tracker_code, created_by=request.user,
                                                                  status="Active")
                    tracker_code_obj.save()

            # Привязываем трекер к поступлению
            incoming.tracker.add(tracker)

            update_inventory_numbers(form.cleaned_data['inventory_numbers'], incoming, occupied=True)

            # Сохраняем фотографии
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            if tracker.tracking_codes.filter(status='Inactive').count() == 0:
                tracker.status = 'Completed'
                tracker.save()

            return redirect('deliveries:list-incoming')

    else:
        form = IncomingForm()
        formset = PhotoFormSet()

    # Получаем доступные трекеры и инвентарные номера
    trackers = Tracker.objects.all()
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

            incoming.save()

            # Получаем старые и новые инвентарные номера
            new_inventory_numbers = set(form.cleaned_data['inventory_numbers'])
            initial_inventory_numbers = set(request.POST.get('initial_inventory_numbers', '').split(','))

            removed_inventory_numbers = initial_inventory_numbers - new_inventory_numbers
            update_inventory_numbers(removed_inventory_numbers, incoming, occupied=False)
            update_inventory_numbers(new_inventory_numbers, incoming, occupied=True)

            # Сохраняем фото
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            return redirect('deliveries:list-incoming')
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
    query = request.GET.get('q')
    incomings = Incoming.objects.exclude(status="Unidentified")
    page_obj, sort_by, sort_order = paginated_query_incoming_list(request, query, incomings)

    columns = incoming_columns()

    return render(request, 'deliveries/incomings/incoming-list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@login_required
def goods_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'arrival_date')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    incomings = Incoming.objects.filter(client=request.user)

    if request.user.groups.filter(name='Clients').exists():
        # Пытаемся получить связь, где текущий пользователь является клиентом
        try:
            relation = ClientManagerRelation.objects.get(client=request.user)
            manager = relation.manager
        except ClientManagerRelation.DoesNotExist:
            manager = None
    else:
        manager = None

    if query:
        incomings = incomings.annotate(
            codes_str=Cast('tracker__tracking_codes', CharField())
        ).filter(
            Q(codes_str__icontains=query) | Q(inventory_numbers__number__icontains=query)
        )

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
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns,
        'manager': manager, # Передаем колонки в шаблон
    })


@login_required
def tag_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    tags = Tag.objects.all().filter(created_by=request.user)

    if query:
        tags = tags.filter(
            Q(name__icontains=query)
        )

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
        'query': query,
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
    page_obj, sort_by, sort_order = paginated_query_incoming_list(request, query, incomings)

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
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')
    hide_completed = request.GET.get('hide_completed', '')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    trackers = Tracker.objects.filter(created_by=request.user)

    if query:
        trackers = trackers.filter(
            Q(name__icontains=query) | Q(tracking_codes__code__icontains=query)
        ).distinct()

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
        'query': query,
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
        return redirect('deliveries:list-incoming')  # Перенаправляем на список после удаления
    return render(request, 'deliveries/incomings/incoming-delete.html', )
