from django.urls import path
from .views import tag_list, tag_new, tag_edit, tag_delete, incoming_new, incoming_detail, incoming_edit, incoming_delete, \
    incoming_list, UnidentifiedIncomingView, delete_photo

app_name = "deliveries"

urlpatterns = [
    path('new-incoming/', incoming_new, name='new-incoming'),
    path('list-incoming/', incoming_list, name='list-incoming'),
    path('list-incoming/<uuid:pk>/', incoming_detail, name='detail-incoming'),
    path('list-incoming/<uuid:pk>/edit', incoming_edit, name='edit-incoming'),
    path('list-incoming/<uuid:pk>/delete', incoming_delete, name='delete-incoming'),
    path('unidentified/', UnidentifiedIncomingView.as_view(), name='unidentified-incoming'),
    path('delete-photo/<uuid:pk>/', delete_photo, name='delete-photo'),
    path('new-tag/', tag_new, name='new-tag'),
    path('list-tag/', tag_list, name='list-tag'),
    path('list-tag/<uuid:pk>/edit', tag_edit, name='edit-tag'),
    path('list-tag/<uuid:pk>/delete', tag_delete, name='delete-tag'),
]
