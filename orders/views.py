from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from orders.forms import OrderForm, PhotoOrderFormSet
from orders.models import PhotoForOrder


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

    return render(request, 'deliveries/client-side/orders/order-searching.html', {
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

    return render(request, 'deliveries/client-side/orders/order-production.html', {
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

            return redirect('index')

    else:
        form = OrderForm()
        formset = PhotoOrderFormSet()

    return render(request, 'deliveries/client-side/orders/order-buying.html', {
        'form': form,
        'formset': formset,
    })
