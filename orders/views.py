from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from orders.forms import OrderForm, PhotoOrderFormSet, OrderManagerForm, OrderStatusForm
from orders.models import PhotoForOrder, Order, OrderStatus


@login_required
def delete_photo_order(request, pk):
    photo = get_object_or_404(PhotoForOrder, pk=pk)
    if request.method == 'DELETE':
        photo.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def order_new_searching(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        formset = PhotoOrderFormSet(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.order_type = 'Searching'

            order.save()

            for file in request.FILES.getlist('photo'):
                photo = PhotoForOrder(photo=file, order=order)
                photo.save()

            return redirect('orders:list-orders')

    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'orders/client-side/order-searching.html', {
        'form': form,
        'formset': formset,
    })


@login_required
def order_new_production(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        formset = PhotoOrderFormSet(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.order_type = 'Production'

            order.save()

            for file in request.FILES.getlist('photo'):
                photo = PhotoForOrder(photo=file, order=order)
                photo.save()

            return redirect('orders:list-orders')
    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'orders/client-side/order-production.html', {
        'form': form,
        'formset': formset,
    })


@login_required
def order_new_delivery(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        formset = PhotoOrderFormSet(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.order_type = 'Delivery'

            order.save()

            for file in request.FILES.getlist('photo'):
                photo = PhotoForOrder(photo=file, order=order)
                photo.save()

            return redirect('orders:list-orders')
    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'orders/client-side/order-delivery.html', {
        'form': form,
        'formset': formset,
    })


@login_required
def order_new_buying(request):
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        formset = PhotoOrderFormSet(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.order_type = 'Buying'

            order.save()

            for file in request.FILES.getlist('photo'):
                photo = PhotoForOrder(photo=file, order=order)
                photo.save()

            return redirect('orders:list-orders')

    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'orders/client-side/order-buying.html', {
        'form': form,
        'formset': formset,
    })


@login_required
def order_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    orders = Order.objects.all().filter(created_by=request.user)

    orders = orders.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
        ('description', 'Описание'),
        ('type', 'Тип заказа'),
        ('status', 'Статус'),
        ('manager', 'Менеджер')
    ]

    return render(request, 'orders/client-side/order-list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()

            # Сохраняем фото
            for file in request.FILES.getlist('photo'):
                photo = PhotoForOrder(photo=file, order=order)
                photo.save()

            return redirect('orders:list-orders')
    else:
        form = OrderForm(instance=order)

    return render(request, 'orders/client-side/order-edit.html', {'form': form, 'order': order})


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_edit_manager(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderManagerForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            order.manager = request.user
            order.save()

            return redirect('orders:list-order-manager')
    else:
        form = OrderManagerForm(instance=order)

    return render(request, 'orders/manager-side/order-edit-manager.html', {'form': form, 'order': order})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('deliveries:list-orders')
    return render(request, 'orders/client-side/order-delete.html', {'order': order})


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_list_manager(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    query = request.GET.get('q', '').strip()
    orders = Order.objects.all()

    if query:
        orders = orders.filter(
            Q(status__name__icontains=query) |
            Q(order_type__icontains=query) |
            Q(created_by__email__icontains=query)
        ).distinct()

    orders = orders.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
        ('description', 'Описание'),
        ('type', 'Тип заказа'),
        ('client', 'Клиент'),
        ('status', 'Статус')
    ]

    return render(request, 'orders/manager-side/order-list-manager.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_detail_manager(request, pk):
    order = get_object_or_404(Order, pk=pk)

    return render(request, 'orders/manager-side/order-details-manager.html', {
        'order': order,
    })


@login_required
def order_detail_client(request, pk):
    order = get_object_or_404(Order, pk=pk)

    return render(request, 'orders/client-side/order-details-client.html', {
        'order': order,
    })


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_status_new(request):
    if request.method == 'POST':
        form = OrderStatusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('orders:list-order-status')
    else:
        form = OrderStatusForm()
    return render(request, 'orders/manager-side/order_status/create_order_status.html', {'form': form})


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_status_list(request):
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    order_status = OrderStatus.objects.all()

    order_status = order_status.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(order_status, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('name', 'Название'),
    ]

    return render(request, 'orders/manager-side/order_status/order_status_list.html', {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_status_edit(request, pk):
    order_status = get_object_or_404(OrderStatus, pk=pk)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order_status)
        if form.is_valid():
            form.save()

            return redirect('orders:list-order-status')
    else:
        form = OrderStatusForm(instance=order_status)

    return render(request, 'orders/manager-side/order_status/order_status_edit.html',
                  {'form': form, 'order_status': order_status})


@user_passes_test(lambda u: u.is_staff)
@login_required
def order_status_delete(request, pk):
    order_status = get_object_or_404(OrderStatus, pk=pk)
    if request.method == 'POST':
        order_status.delete()
        return redirect('orders:list-order-status')
    return render(request, 'orders/manager-side/order_status/order_status_delete.html',
                  {'order_status': order_status})
