from django.urls import path
from .views import tag_list, tag_new, tag_edit, tag_delete, incoming_new, incoming_detail, incoming_edit, \
    incoming_delete, search_users, \
    incoming_list, consolidation_edit, package_new, consolidation_list, new_consolidation, goods_list, goods_detail, \
    incoming_unidentified, delete_photo, tracker_delete, tracker_new, tracker_edit, tracker_detail, tracker_list, \
    incoming_templates

app_name = "deliveries"

urlpatterns = [
    path('new-incoming/', incoming_new, name='new-incoming'),
    path('list-incoming/', incoming_list, name='list-incoming'),
    path('list-incoming/<uuid:pk>/', incoming_detail, name='detail-incoming'),
    path('list-incoming/<uuid:pk>/edit', incoming_edit, name='edit-incoming'),
    path('list-incoming/<uuid:pk>/delete', incoming_delete, name='delete-incoming'),
    path('unidentified/', incoming_unidentified, name='unidentified-incoming'),
    path('templates/', incoming_templates, name='templates-incoming'),
    path('delete-photo/<uuid:pk>/', delete_photo, name='delete-photo'),
    path('new-tag/', tag_new, name='new-tag'),
    path('list-tag/', tag_list, name='list-tag'),
    path('list-tag/<uuid:pk>/edit', tag_edit, name='edit-tag'),
    path('list-tag/<uuid:pk>/delete', tag_delete, name='delete-tag'),
    path('new-tracker/', tracker_new, name='new-tracker'),
    path('list-tracker/', tracker_list, name='list-tracker'),
    path('list-tracker/<uuid:pk>/', tracker_detail, name='detail-tracker'),
    path('list-tracker/<uuid:pk>/edit', tracker_edit, name='edit-tracker'),
    path('list-tracker/<uuid:pk>/delete', tracker_delete, name='delete-tracker'),
    path('list-goods/', goods_list, name='list-goods'),
    path('list-goods/<uuid:pk>/', goods_detail, name='detail-goods'),
    path('consolidation/', new_consolidation, name='consolidation'),
    path('consolidation/edit/<uuid:pk>/', consolidation_edit, name='consolidation-edit'),
    path('list-consolidation/', consolidation_list, name='list-consolidation'),
    path('new-package/<uuid:pk>/', package_new, name='new-package'),
    path('search-users/', search_users, name='search-users'),
]
