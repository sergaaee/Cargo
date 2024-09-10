from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import User
from .models import Incoming, Photo, Tag, InventoryNumber
import os
from dotenv import load_dotenv

load_dotenv()

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
        fields = ['track_number', 'inventory_numbers', 'places_count', 'arrival_date', 'size', 'weight', 'state', 'package_type', 'status', 'tag']
        widgets = {
            'track_number': forms.TextInput(attrs={'class': 'form-control'}),
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000x000x000',
                'data-inputmask': "'mask': '999x999x999'" }),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'package_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    places_count = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    weight = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))

    inventory_numbers = forms.CharField(required=True, widget=forms.TextInput(attrs={'list': 'inventory-numbers-list', 'class': 'form-control'}))
    tag = forms.CharField(required=False, widget=forms.TextInput(attrs={'list': 'tag-list', 'class': 'form-control'}))  # Поле для автозаполнения

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_tag(self):
        tag_name = self.cleaned_data.get('tag')
        if tag_name:
            # Get or create the tag
            tag, created = Tag.objects.get_or_create(name=tag_name)

            # Check if a user with this username (equal to tag name) exists
            user, user_created = User.objects.get_or_create(username=tag_name)

            # If the user is newly created, set a default password
            if user_created:
                user.set_password(os.environ.get('DEFAULT_PASSWORD'))
                user.save()

            return tag
        return None

    def clean_inventory_numbers(self):
        inventory_numbers = self.cleaned_data.get('inventory_numbers')
        if inventory_numbers:
            inventory_numbers = inventory_numbers.split(',')
            for inventory_number in inventory_numbers:
                inventory_number_obj, created = InventoryNumber.objects.get_or_create(number=inventory_number)
                # Теперь проверяем is_occupied, а не location
                if inventory_number_obj.is_occupied:
                    raise forms.ValidationError(f'Inventory number {inventory_number} is already occupied.')
                inventory_number_obj.is_occupied = True
                inventory_number_obj.save()
            return inventory_numbers
        return None

#29.4 14:30
class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['photo']
        widgets = {
            'photo': CustomClearableFileInput(),  # Используем кастомный виджет
        }

PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)
