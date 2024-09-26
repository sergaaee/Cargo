from django import forms
from django.forms.models import inlineformset_factory
from .models import Incoming, Photo, Tag, InventoryNumber, Tracker, TrackerCode
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
    tracking_codes = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите коды через запятую'})
    )

    class Meta:
        model = Tracker
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            existing_codes = self.instance.tracking_codes.values_list('code', flat=True)
            self.fields['tracking_codes'].initial = ', '.join(existing_codes)

    def clean_tracking_codes(self):
        codes = self.cleaned_data['tracking_codes']
        code_list = [code.strip() for code in codes.split(',') if code.strip()]

        if not code_list:
            raise forms.ValidationError("Необходимо ввести хотя бы один трекинг-код.")

        tracker_codes = []
        for code in code_list:
            tracker_code, created = TrackerCode.objects.get_or_create(code=code, status="Inactive", source="Unknown")
            tracker_codes.append(tracker_code)

        return tracker_codes


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
        tracker_code = self.cleaned_data.get('tracker')

        if not tracker_code:
            raise forms.ValidationError("Трек-код не был введен.")

        try:
            tracker_obj = Tracker.objects.get(trackercodetracker__tracker_code__code=tracker_code.split(",")[0])
        except Tracker.DoesNotExist:
            raise forms.ValidationError(f'Трек-код "{tracker_code}" не найден.')

        return tracker_obj, tracker_code

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



class IncomingFormEdit(forms.ModelForm):
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

    places_count = forms.IntegerField(initial=1,
                                      widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    weight = forms.IntegerField(initial=1, required=False,
                                widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))

    inventory_numbers = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'list': 'inventory-numbers-list', 'class': 'form-control'}))
    tag = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'list': 'tag-list', 'class': 'form-control'}))
    tracker = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'list': 'tracker-list', 'class': 'form-control'}
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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
