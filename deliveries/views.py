from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django.shortcuts import render, redirect
from .forms import IncomingForm, PhotoFormSet
from .models import Tag, Photo


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


class ListIncomingView(LoginRequiredMixin, TemplateView):
    template_name = 'deliveries/incoming-list.html'



class UnidentifiedIncomingView(LoginRequiredMixin, TemplateView):
    template_name = 'deliveries/incoming-unidentified.html'
