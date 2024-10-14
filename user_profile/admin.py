from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import ClientManagerRelation


@admin.register(ClientManagerRelation)
class ClientManagerRelationAdmin(admin.ModelAdmin):
    list_display = ('client', 'manager')  # Отображение клиентов и их менеджеров в списке
    search_fields = ('client__username', 'manager__username')  # Поля для поиска
    list_filter = ('client__groups', 'manager__groups')  # Фильтрация по группам
    autocomplete_fields = ['client', 'manager']  # Автозаполнение при выборе пользователя

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ограничение выбора клиентами и менеджерами только пользователей соответствующих групп
        form.base_fields['client'].queryset = User.objects.filter(groups__name='Clients')
        form.base_fields['manager'].queryset = User.objects.filter(groups__name='Managers')
        return form

# Кастомизация админки для модели пользователя
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'phone_number'),
        }),
    )
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number',)}),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and hasattr(obj, 'profile'):
            form.base_fields['phone_number'].initial = obj.profile.phone_number
        return form

# Отменяем регистрацию стандартного User и регистрируем кастомного администратора
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
