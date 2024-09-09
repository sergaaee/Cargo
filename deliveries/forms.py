from django import forms
from django.forms.models import inlineformset_factory
from .models import Incoming, Photo, Tag


class CustomClearableFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # Поддержка множественного выбора

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs['multiple'] = 'multiple'

    def value_from_datadict(self, data, files, name):
        """Обрабатываем множественные файлы"""
        upload = files.getlist(name)
        return upload


# Стандартная форма Incoming
class IncomingForm(forms.ModelForm):
    class Meta:
        model = Incoming
        fields = ['track_number', 'inventory_number', 'places_count', 'arrival_date', 'size', 'weight', 'state', 'package_type', 'status', 'tag']
        widgets = {
            'places_count': forms.NumberInput(attrs={'min': '1'}),
            'weight': forms.NumberInput(attrs={'min': '1'}),
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    places_count = forms.IntegerField(initial=1, min_value=1)
    weight = forms.IntegerField(initial=1, min_value=1)

    tag = forms.CharField(required=False, widget=forms.TextInput(attrs={'list': 'tag-list'}))  # Поле для автозаполнения

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_tag(self):
        tag_name = self.cleaned_data.get('tag')
        if tag_name:
            # Проверяем или создаем объект Tag
            tag, created = Tag.objects.get_or_create(name=tag_name)
            return tag  # Возвращаем объект Tag, а не строку
        return None

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['photo']
        widgets = {
            'photo': CustomClearableFileInput(),  # Используем кастомный виджет
        }

PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)