from django import forms
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError
import json

from user_profile.models import UserProfile
from .models import Incoming, Photo, Tag, InventoryNumber, Tracker, TrackerCode, Consolidation, ConsolidationCode


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

    def clean_name(self):
        try:
            tag = Tag.objects.get(name=self.cleaned_data['name'])
            if tag:
                raise forms.ValidationError(f'Тэг с именем "{tag.name}" уже существует')
        except Tag.DoesNotExist:
            return self.cleaned_data['name']


class TrackerForm(forms.ModelForm):
    tracking_codes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите код, а затем нажмите enter'})
    )

    class Meta:
        model = Tracker
        fields = ['name', 'source', 'tracking_codes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название'}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите источник (прим. CDEK)'}),
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
            tracker_code, created = TrackerCode.objects.get_or_create(code=code, status="Inactive")
            tracker_codes.append(tracker_code)

        return tracker_codes


class BaseIncomingForm(forms.ModelForm):
    class Meta:
        model = Incoming
        fields = ['inventory_numbers',
                  'places_count',
                  'arrival_date',
                  'size',
                  'weight',
                  'state',
                  'package_type',
                  'status',
                  'tag']
        widgets = {
            'arrival_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000x000x000',
                                           'data-inputmask': "'mask': '999x999x999'"}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'package_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    places_count = forms.IntegerField(initial=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    weight = forms.IntegerField(initial=1, required=False,
                                widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))

    inventory_numbers = forms.CharField(required=True,
                                        widget=forms.TextInput(
                                            attrs={'list': 'inventory-numbers-list', 'class': 'form-control'}, ),
                                        error_messages={
                                            'required': 'Пожалуйста, введите инвентарные номера.',
                                            'invalid': 'Некорректный формат инвентарного номера.',
                                        }, )

    tag = forms.CharField(required=False, widget=forms.TextInput(attrs={'list': 'tag-list', 'class': 'form-control'}))
    tracker = forms.CharField(required=False,
                              widget=forms.TextInput(attrs={'list': 'tracker-list', 'class': 'form-control'}),
                              error_messages={
                                  'required': 'Трек-коды не были введены.',
                              },
                              )

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
                # Используем get_or_create для поиска или создания инвентарного номера
                inventory_number_obj, created = InventoryNumber.objects.get_or_create(number=inventory_number)

                # Проверяем, занят ли инвентарный номер, если он уже существует и не принадлежит текущему объекту Incoming
                if inventory_number_obj.is_occupied and inventory_number_obj not in incoming.inventory_numbers.all():
                    raise forms.ValidationError(f'Inventory number {inventory_number} is already occupied.')

                # Добавляем инвентарный номер в список, чтобы вернуть его в cleaned_data
                inventory_number_objects.append(inventory_number_obj)

            return inventory_number_objects

        return None

    def clean_client(self):
        client_phone_number = self.cleaned_data.get('client')
        if client_phone_number:
            try:
                user_profile = UserProfile.objects.get(phone_number=client_phone_number)
                return user_profile.user
            except UserProfile.DoesNotExist:
                raise forms.ValidationError(f"❌ Клиент с номером {client_phone_number} не найден!")

        return None

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get("client")
        tracker_codes = cleaned_data.get("tracker")
        tag = cleaned_data.get("tag")
        inventory_numbers = cleaned_data.get('inventory_numbers')
        places_count = cleaned_data.get('places_count')

        # Проверка трек-кодов на владельца
        conflicting_items = []
        if client:
            for tracker_code in tracker_codes:
                tracker_code_obj = TrackerCode.objects.filter(code=tracker_code).first()
                if tracker_code_obj and tracker_code_obj.created_by and tracker_code_obj.created_by != client:
                    conflicting_items.append(f'❌ Трек-код {tracker_code} принадлежит другому клиенту!')

            if tag and tag.created_by and tag.created_by != client:
                conflicting_items.append(f'❌ Метка "{tag.name}" принадлежит другому клиенту!')

        if inventory_numbers and places_count:
            if len(inventory_numbers) != places_count:
                conflicting_items.append(
                    f"❌ Кол-во инвентарных номеров ({len(inventory_numbers)}) не соответствует кол-ву мест ({places_count}).")

        if conflicting_items:
            raise forms.ValidationError(conflicting_items)

        return cleaned_data


# Стандартная форма Incoming
class IncomingForm(BaseIncomingForm):
    def clean_tracker(self):
        tracker_codes = self.cleaned_data.get('tracker')
        if not tracker_codes:
            raise forms.ValidationError("Трек-коды не были введены.")

        # Получаем список трек-кодов
        code_list = [code.strip() for code in tracker_codes.split(',') if code.strip()]

        # Ищем трекер, к которому привязан хотя бы один из этих кодов
        tracker_obj = Tracker.objects.filter(tracking_codes__code__in=code_list).first()

        if tracker_obj:
            existing_incoming = Incoming.objects.filter(tracker=tracker_obj).exclude(id=self.instance.id).first()
            if existing_incoming:
                raise forms.ValidationError("Этот трекер уже привязан к другому поступлению.")

        # Если трекер не найден, создаем новый
        if not tracker_obj:
            tracker_obj = Tracker.objects.create(name="Трекер для " + ", ".join(code_list), )

            # Привязываем коды к новому трекеру
            for code in code_list:
                tracker_code, created = TrackerCode.objects.get_or_create(code=code, defaults={'status': 'Active', })
                tracker_code.tracker = tracker_obj
                tracker_obj.tracking_codes.add(tracker_code)
                tracker_code.save()
            tracker_obj.save()
        return tracker_obj, code_list


class IncomingEditForm(BaseIncomingForm):

    def clean_tracker(self):
        tracker_codes = self.cleaned_data.get('tracker', '').strip()

        if not tracker_codes:
            raise forms.ValidationError("❌ Введите хотя бы один трек-код.")

        code_list = [code.strip() for code in tracker_codes.split(',') if code.strip()]
        tracker_obj = Tracker.objects.filter(tracking_codes__code__in=code_list).first()

        if not tracker_obj:
            tracker_obj = Tracker.objects.create(name="Трекер для " + ", ".join(code_list))

            for code in code_list:
                tracker_code, created = TrackerCode.objects.get_or_create(code=code, defaults={'status': 'Active'})
                tracker_code.tracker = tracker_obj
                tracker_obj.tracking_codes.add(tracker_code)
                tracker_code.save()
            tracker_obj.save()

        return tracker_obj, code_list

    def clean_inventory_numbers(self):
        inventory_numbers = self.cleaned_data.get('inventory_numbers')

        if inventory_numbers:
            # ✅ Разбиваем строку по запятым и удаляем пробелы
            inventory_numbers = [num.strip() for num in inventory_numbers.split(',')]

            inventory_number_objects = []
            for inventory_number in inventory_numbers:
                inventory_number_obj, created = InventoryNumber.objects.get_or_create(number=inventory_number)
                inventory_number_objects.append(inventory_number_obj)

            return inventory_number_objects

        return None


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['photo']
        widgets = {
            'photo': CustomClearableFileInput(),
        }


class ConsolidationForm(forms.ModelForm):
    class Meta:
        model = Consolidation
        fields = ['client', 'delivery_type', 'track_code', 'instruction', 'consolidation_date']
        widgets = {
            'consolidation_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'delivery_type': forms.Select(attrs={'class': 'form-control'}),
            'instruction': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Любые инструкции для работника склада'}),
        }

    client = forms.CharField(required=True,
                             widget=forms.TextInput(
                                 attrs={'list': 'clients-list', 'class': 'form-control',
                                        'placeholder': 'Начните писать номер', }, ),
                             error_messages={
                                 'required': 'Пожалуйста, выберите клиента.',
                                 'invalid': 'Некорректный клиент.',
                             }, )
    track_code = forms.CharField(required=True,
                                 widget=forms.TextInput(
                                     attrs={'list': 'clients-list', 'class': 'form-control',
                                            'placeholder': 'Начните писать код ST', }, ),
                                 error_messages={
                                     'required': 'Пожалуйста, введите трек-код.',
                                     'invalid': 'Некорректный трек-код.',
                                 }, )

    def clean_client(self):
        client_phone_number = self.cleaned_data.get('client')
        if not client_phone_number:
            raise forms.ValidationError(
                "Please provide a client phone number."
            )

        try:
            user_profile = UserProfile.objects.get(phone_number=client_phone_number)
            user = user_profile.user
        except UserProfile.DoesNotExist:
            raise forms.ValidationError(
                f"No client found with phone number {client_phone_number}."
            )

        return user

    def clean_track_code(self):
        track_code = self.cleaned_data.get('track_code')
        if track_code:
            try:
                consolidation_code = ConsolidationCode.objects.get(code=track_code)
            except ConsolidationCode.DoesNotExist:
                consolidation_code = ConsolidationCode.objects.create(code=track_code)

            return consolidation_code
        else:
            raise forms.ValidationError("Пожалуйста, введите трек-код.")


class PackageForm(forms.ModelForm):
    class Meta:
        model = Consolidation
        fields = ['consolidation_date', 'instruction']
        widgets = {
            'consolidation_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'instruction': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Любые инструкции для работника склада'}),
        }

    def __init__(self, *args, **kwargs):
        self.incomings_data = kwargs.pop('incomings_data', {})
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем инвентарные номера для каждого поступления
        errors = []
        index = 0
        for incoming_id, incoming in self.incomings_data.items():
            index += 1
            field_name = f'inventory_numbers_{incoming_id}'
            inventory_numbers_raw = self.data.get(field_name, '')

            # Разделяем номера
            inventory_numbers = [num.strip() for num in inventory_numbers_raw.split(',') if num.strip()]

            # Проверяем количество номеров
            if len(inventory_numbers) != incoming.places_count:
                errors.append(
                    f'Для {index}-го поступления необходимо указать {incoming.places_count} номера(-ов), '
                    f'но введено {len(inventory_numbers)}.'
                )

            # Проверяем валидность номеров
            valid_numbers = list(incoming.inventory_numbers.values_list('number', flat=True))
            invalid_numbers = [num for num in inventory_numbers if num not in valid_numbers]
            if invalid_numbers:
                errors.append(
                    f'Следующие номера не принадлежат {index}(-ому/-ему) поступлению: {", ".join(invalid_numbers)}.'
                )

        if errors:
            raise ValidationError(errors)

        return cleaned_data


PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)
