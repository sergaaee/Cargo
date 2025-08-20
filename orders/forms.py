from django import forms
from django.forms.models import inlineformset_factory
from .models import Order, PhotoForOrder, OrderStatus


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


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class OrderManagerForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class PhotoOrderForm(forms.ModelForm):
    class Meta:
        model = PhotoForOrder
        fields = ['photo']
        widgets = {
            'photo': CustomClearableFileInput(),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = OrderStatus
        fields = ['name', 'description']

    name = forms.CharField(label="Название статуса заказа", required=True,
                           widget=forms.TextInput(
                               attrs={'class': 'form-control'}, ),
                           error_messages={
                               'required': 'Пожалуйста, введите название.',
                           }, )

    description = forms.CharField(label="Описание статуса заказа", required=False,
                                  widget=forms.TextInput(
                                      attrs={'class': 'form-control'}, ),
                                  )


PhotoOrderFormSet = inlineformset_factory(Order, PhotoForOrder, form=PhotoOrderForm, fields=('photo',), extra=1,
                                          can_delete=True)
