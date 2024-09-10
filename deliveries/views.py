from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from .forms import IncomingForm, PhotoFormSet
from .models import Tag, Photo, Incoming
from django.contrib.auth.decorators import login_required

@login_required
def incoming_new(request):
    if request.method == 'POST':
        form = IncomingForm(request.POST, request.FILES)
        formset = PhotoFormSet(request.POST, request.FILES)

        incoming = form.save(commit=False)
        incoming.tag = form.cleaned_data['tag']
        if form.is_valid():
            incoming = form.save(commit=False)

            # Обрабатываем тег
            tag_name = form.cleaned_data.get('tag')
            if tag_name:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                incoming.tag = tag

            incoming.save()

            # Обрабатываем множественные изображения
            for file in request.FILES.getlist('photo'):
                photo = Photo(photo=file, incoming=incoming)
                photo.save()

            return redirect('index')
    else:
        form = IncomingForm()
        formset = PhotoFormSet()

    tags = Tag.objects.all()
    return render(request, 'deliveries/incoming-new.html', {'form': form, 'formset': formset, 'tags': tags})

@login_required
def incoming_list(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'arrival_date')
    sort_order = request.GET.get('order', 'asc')

    if sort_order == 'desc':
        order_prefix = '-'
    else:
        order_prefix = ''

    incomings = Incoming.objects.all()

    if query:
        incomings = incomings.filter(
            Q(track_number__icontains=query) | Q(inventory_number__icontains=query)
        )

    incomings = incomings.order_by(f'{order_prefix}{sort_by}')

    paginator = Paginator(incomings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Добавляем колонки с метками для отображения в таблице
    columns = [
        ('track_number', 'Трек-номер'),
        ('tag__name', 'Тег'),
        ('arrival_date', 'Дата прибытия'),
        ('inventory_number', 'Инвентарный номер'),
        ('places_count', 'Количество мест'),
        ('weight', 'Вес'),
        ('status', 'Статус'),
    ]

    return render(request, 'deliveries/incoming-list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'order': sort_order,
        'columns': columns  # Передаем колонки в шаблон
    })





class UnidentifiedIncomingView(LoginRequiredMixin, TemplateView):
    template_name = 'deliveries/incoming-unidentified.html'

@login_required
def incoming_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)  # Получаем объект по первичному ключу (id)
    return render(request, 'deliveries/incoming-detail.html', {'incoming': incoming})

@login_required
def incoming_edit(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    # Пытаемся получить тег, если он существует, иначе присваиваем пустую строку
    tag = Tag.objects.filter(pk=incoming.tag.id).first() if incoming.tag else ''

    if request.method == 'POST':
        form = IncomingForm(request.POST, instance=incoming)
        if form.is_valid():
            form.save()
            return redirect('deliveries:list-incoming')  # Перенаправляем на список после сохранения
    else:
        form = IncomingForm(instance=incoming)

    return render(request, 'deliveries/incoming-edit.html', {'form': form, 'incoming': incoming, 'tag': tag})


@login_required
def incoming_delete(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    if request.method == 'POST':
        incoming.delete()
        return redirect('deliveries:list-incoming')  # Перенаправляем на список после удаления
    return render(request, 'deliveries/incoming-delete.html', )
