from django import forms
from django.forms.models import inlineformset_factory
from .models import Incoming, Photo, Tag, InventoryNumber, Tracker
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


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TrackerForm(forms.ModelForm):
    class Meta:
        model = Tracker
        fields = ['name', 'codes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'codes': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Стандартная форма Incoming
class IncomingForm(forms.ModelForm):
    class Meta:
        model = Incoming
        fields = ['inventory_numbers', 'places_count', 'arrival_date', 'size', 'weight', 'state',
                  'package_type', 'status', 'tag']
        widgets = {
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000x000x000',
                                           'data-inputmask': "'mask': '999x999x999'"}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'package_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    places_count = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    weight = forms.IntegerField(initial=1, required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))

    inventory_numbers = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'list': 'inventory-numbers-list', 'class': 'form-control'}))
    tag = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'list': 'tag-list', 'class': 'form-control'}))
    tracker = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'list': 'tracker-list', 'class': 'form-control'}
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_tracker(self):
        tracker_codes = self.cleaned_data.get('tracker')
        if tracker_codes:
            tracker_codes_list = [code.strip() for code in tracker_codes.split(',') if code.strip()]
            tracker_objects = []

            for tracker_code in tracker_codes_list:
                tracker = Tracker.objects.filter(codes__contains=[tracker_code]).first()
                if tracker:
                    tracker_objects.append(tracker)
                else:
                    raise forms.ValidationError(f'Tracker with code {tracker_code} not found.')

            return tracker_objects
        return None

    def clean_tag(self):
        tag_name = self.cleaned_data.get('tag')
        if tag_name:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            return tag
        return None

    def clean_places_count(self):
        places_count = self.cleaned_data.get('places_count')
        if places_count is None:
            raise forms.ValidationError("Places count must be provided.")
        return places_count

    def clean_inventory_numbers(self):
        inventory_numbers = self.cleaned_data.get('inventory_numbers')

        if inventory_numbers:
            inventory_numbers = [num.strip() for num in inventory_numbers.split(',')]
            inventory_number_objects = []

            incoming = self.instance
            for inventory_number in inventory_numbers:
                try:
                    inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
                    if inventory_number_obj.is_occupied and inventory_number_obj not in incoming.inventory_numbers.all():
                        raise forms.ValidationError(f'Inventory number {inventory_number} is already occupied.')
                    inventory_number_objects.append(inventory_number_obj)
                except InventoryNumber.DoesNotExist:
                    raise forms.ValidationError(f'Inventory number {inventory_number} does not exist.')

            return inventory_number_objects
        return None

    def clean(self):
        cleaned_data = super().clean()
        inventory_numbers = cleaned_data.get('inventory_numbers')
        places_count = cleaned_data.get('places_count')
        weight = cleaned_data.get('weight')

        if weight is None:
            cleaned_data['weight'] = 1

        if inventory_numbers and places_count:
            if len(inventory_numbers) != places_count:
                raise forms.ValidationError(
                    f"The number of inventory numbers ({len(inventory_numbers)}) does not match the number of places ({places_count})."
                )
        return cleaned_data


# 29.4 14:30
class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['photo']
        widgets = {
            'photo': CustomClearableFileInput(),  # Используем кастомный виджет
        }


PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)
