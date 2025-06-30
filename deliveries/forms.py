from django import forms
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError

from user_profile.models import UserProfile
from .models import Incoming, Photo, Tag, InventoryNumber, Tracker, TrackerCode, Consolidation, ConsolidationCode, \
    ConsolidationInventory, PackageType, DeliveryType, DeliveryPriceRange


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
    weight = forms.FloatField(initial=1, required=False,
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
                try:
                    inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
                except InventoryNumber.DoesNotExist:
                    raise forms.ValidationError(f'Инвентарный номер {inventory_number} не существует в базе данных.')

                if inventory_number_obj.is_occupied and inventory_number_obj not in incoming.inventory_numbers.all():
                    raise forms.ValidationError(f'Инвентарный номер {inventory_number} уже занят.')

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
            existing_incoming = Incoming.objects.filter(tracker=tracker_obj).first()

            if existing_incoming:
                existing_code = TrackerCode.objects.filter(tracker=tracker_obj, code__in=code_list).first()
                raise forms.ValidationError(f"Трек-код '{existing_code.code}' уже привязан к другому поступлению.")

        return tracker_obj, code_list


class IncomingEditForm(BaseIncomingForm):

    def clean_tracker(self):
        tracker_codes = self.cleaned_data.get('tracker', '').strip()

        if not tracker_codes:
            raise forms.ValidationError("❌ Введите хотя бы один трек-код.")

        code_list = [code.strip() for code in tracker_codes.split(',') if code.strip()]
        tracker_obj = Tracker.objects.filter(tracking_codes__code__in=code_list).first()

        if tracker_obj:
            existing_incoming = Incoming.objects.filter(tracker=tracker_obj).exclude(id=self.instance.id).first()
            existing_code = TrackerCode.objects.filter(tracker=tracker_obj, code__in=code_list).first()

            if existing_incoming:
                raise forms.ValidationError(f"Трек-код '{existing_code.code}' уже привязан к другому поступлению.")

        return tracker_obj, code_list

    def clean_inventory_numbers(self):
        inventory_numbers = self.cleaned_data.get('inventory_numbers')

        if inventory_numbers:
            # ✅ Разбиваем строку по запятым и удаляем пробелы
            inventory_numbers = [num.strip() for num in inventory_numbers.split(',')]

            inventory_number_objects = []
            for inventory_number in inventory_numbers:
                try:
                    inventory_number_obj = InventoryNumber.objects.get(number=inventory_number)
                except InventoryNumber.DoesNotExist:
                    raise forms.ValidationError(f'Инвентарный номер {inventory_number} не найден в базе данных.')
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
            'instruction': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Любые инструкции для работника склада'}),
        }

    delivery_type = forms.ModelChoiceField(
        queryset=DeliveryType.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

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

    def clean(self):
        cleaned_data = super().clean()

        places_data = {}
        for key, value in self.data.items():
            if key.startswith('inventory_numbers_'):
                place_index = key.split('_')[-1]
                inventory_numbers = [num.strip() for num in value.split(',') if num.strip()]
                weight = self.data.get(f'weight_consolidated_{place_index}', 0)
                volume = self.data.get(f'volume_consolidated_{place_index}', 0)
                place_code = self.data.get(f'place_consolidated_{place_index}', '')
                package_type = self.data.get(f'package_type_{place_index}', '')
                places_data[place_index] = {
                    'inventory_numbers': inventory_numbers,
                    'weight': float(weight) if weight else 0,
                    'volume': float(volume) if volume else 0,
                    'place_code': place_code,
                    'package_type': package_type,
                }

        if 'in_work' in self.data and not places_data:
            raise ValidationError('Должно быть указано хотя бы одно место для отправки в работу.')

        place_codes = [place_data['place_code'] for place_data in places_data.values()]
        if len(place_codes) != len(set(place_codes)):
            raise ValidationError('Коды мест должны быть уникальными.')

        valid_numbers = list(ConsolidationInventory.objects.filter(
            consolidation_incoming__consolidation=self.instance
        ).values_list('inventory_number__number', flat=True).distinct())

        all_inventory_numbers = []
        errors = []
        for place_index, place_data in places_data.items():
            inventory_numbers = place_data['inventory_numbers']
            place_code = place_data['place_code']

            if not inventory_numbers:
                errors.append(f'Для места {place_code} не указаны инвентарные номера.')
                continue

            if place_data['weight'] <= 0:
                errors.append(f'Вес для места {place_code} должен быть больше 0.')
            if place_data['volume'] <= 0:
                errors.append(f'Объём для места {place_code} должен быть больше 0.')
            if not place_data['package_type']:
                errors.append(f'Для места {place_code} не указан тип упаковки.')

        if errors:
            raise ValidationError(errors)

        return cleaned_data


class GenerateInventoryNumbersForm(forms.Form):
    count = forms.IntegerField(min_value=1, label="Количество инвентарных номеров для генерации")


class NewLocationForm(forms.Form):
    name = forms.CharField(label="Название локации")


class PackageTypeForm(forms.ModelForm):
    class Meta:
        model = PackageType
        fields = ['name', 'price', 'description']

    name = forms.CharField(label="Название вида упаковки", required=True,
                           widget=forms.TextInput(
                               attrs={'class': 'form-control'}, ),
                           error_messages={
                               'required': 'Пожалуйста, введите название.',
                           }, )
    price = forms.FloatField(label="Цена", initial=1, required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    description = forms.CharField(
        label="Описание упаковки",
        widget=forms.TextInput(
            attrs={'class': 'form-control'}, ),
    )


class DeliveryTypeForm(forms.ModelForm):
    class Meta:
        model = DeliveryType
        fields = ['name', 'eta']

    name = forms.CharField(label="Название вида упаковки", required=True,
                           widget=forms.TextInput(
                               attrs={'class': 'form-control'}, ),
                           error_messages={
                               'required': 'Пожалуйста, введите название.',
                           }, )

    eta = forms.CharField(
        label="Примерное время доставки",
        widget=forms.TextInput(
            attrs={'class': 'form-control'}, ),
    )


DeliveryPriceRangeFormSet = inlineformset_factory(
    DeliveryType,
    DeliveryPriceRange,
    fields=['min_density', 'max_density', 'price_per_kg'],
    extra=1,
    can_delete=True,
    widgets={
        'min_density': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        'max_density': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
    },
    labels={
        'min_density': 'Минимальная плотность',
        'max_density': 'Максимальная плотность',
        'price_per_kg': 'Цена за кг ($)',
    },
    error_messages={
        'min_density': {'required': 'Пожалуйста, введите минимальнаю плотность.'},
        'max_density': {'required': 'Пожалуйста, введите максимальную плотность.'},
        'price_per_kg': {'required': 'Пожалуйста, введите цену за кг.'},
    }
)

PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)
