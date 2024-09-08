from django.urls import path
from .views import profile_view

app_name = "web"

urlpatterns = [
    path('', profile_view, name='profile'),
    path('profile/', profile_view, name='profile'),
]