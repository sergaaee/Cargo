from django import forms
from django.forms.models import inlineformset_factory
from .models import Incoming, Photo, Tag, InventoryNumber, Tracker, TrackerCode, Consolidation


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


class IncomingFormEdit(BaseIncomingForm):
    pass


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
        fields = ['client', 'delivery_type', 'track_code', 'instruction']
        widgets = {
            'created_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'delivery_type': forms.Select(attrs={'class': 'form-control'}),
            'track_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Трек-номер',}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Любые инструкции для работника склада'}),
        }

    client = forms.CharField(required=True,
                             widget=forms.TextInput(
                                 attrs={'list': 'clients-list', 'class': 'form-control', 'placeholder': 'Начните писать номер',}, ),
                             error_messages={
                                 'required': 'Пожалуйста, выберите клиента.',
                                 'invalid': 'Некорректный клиент.',
                             }, )


PhotoFormSet = inlineformset_factory(Incoming, Photo, form=PhotoForm, fields=('photo',), extra=1, can_delete=True)
