from django.urls import path
from .views import incoming_new, incoming_detail, incoming_edit, incoming_delete, incoming_list, UnidentifiedIncomingView, delete_photo

app_name = "deliveries"

urlpatterns = [
    path('new-incoming/', incoming_new, name='new-incoming'),
    path('list-incoming/', incoming_list, name='list-incoming'),
    path('list-incoming/<uuid:pk>/', incoming_detail, name='detail-incoming'),
    path('list-incoming/<uuid:pk>/edit', incoming_edit, name='edit-incoming'),
    path('list-incoming/<uuid:pk>/delete', incoming_delete, name='delete-incoming'),
    path('unidentified/', UnidentifiedIncomingView.as_view(), name='unidentified-incoming'),
    path('delete-photo/<uuid:pk>/', delete_photo, name='delete-photo'),
]