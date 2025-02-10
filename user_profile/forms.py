from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from phonenumber_field.formfields import PhoneNumberField
from django import forms

from user_profile.models import UserProfile
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False, label='Phone Number')

    class Meta(UserCreationForm.Meta):
        model = User
        field_classes = UserCreationForm.Meta.field_classes.update({'phone_number': PhoneNumberField})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()  # Сохранение пользователя

        # Сохраняем номер телефона только если профиль уже создан
        if hasattr(user, 'profile'):
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()

        return user

class CustomUserChangeForm(UserChangeForm):
    phone_number = forms.CharField(max_length=15, required=False, label='Phone Number')

    class Meta(UserChangeForm.Meta):
        model = User
        field_classes = UserChangeForm.Meta.field_classes.update({'phone_number': PhoneNumberField})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()

        if hasattr(user, 'profile'):
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()
        return user