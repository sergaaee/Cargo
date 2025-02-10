from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from orders.forms import OrderForm, PhotoOrderFormSet, OrderManagerForm
from orders.models import PhotoForOrder, Order


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

            return redirect('index')

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

            return redirect('index')

    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'orders/client-side/order-production.html', {
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
        ('status', 'Статус')
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

            return redirect('orders:list-order-manager')
    else:
        form = OrderManagerForm(instance=order)

    return render(request, 'orders/manager-side/order-edit-manager.html', {'form': form, 'order': order})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('deliveries:list-order')
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

    orders = Order.objects.all()


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
