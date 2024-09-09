from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django.shortcuts import render, redirect, get_object_or_404
from .forms import IncomingForm, PhotoFormSet
from .models import Tag, Photo, Incoming


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
                check = Tag.objects.get_or_create(name=tag_name)
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


def incoming_list(request):
    incomings = Incoming.objects.all()  # Получаем все записи из модели Incoming
    return render(request, 'deliveries/incoming-list.html', {'incomings': incomings})



class UnidentifiedIncomingView(LoginRequiredMixin, TemplateView):
    template_name = 'deliveries/incoming-unidentified.html'

def incoming_detail(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)  # Получаем объект по первичному ключу (id)
    return render(request, 'deliveries/incoming-detail.html', {'incoming': incoming})

def incoming_edit(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)
    tag = get_object_or_404(Tag, pk=incoming.tag.id)

    if request.method == 'POST':
        form = IncomingForm(request.POST, instance=incoming)
        if form.is_valid():
            form.save()
            return redirect('deliveries:list-incoming')  # Перенаправляем на список после сохранения
    else:
        form = IncomingForm(instance=incoming)

    return render(request, 'deliveries/incoming-edit.html', {'form': form, 'incoming': incoming, 'tag': tag})

def incoming_delete(request, pk):
    incoming = get_object_or_404(Incoming, pk=pk)

    if request.method == 'POST':
        incoming.delete()
        return redirect('deliveries:list-incoming')  # Перенаправляем на список после удаления
    return render(request, 'deliveries/incoming-delete.html', )
