from django.urls import path

from .views import order_list_manager, order_new_searching, delete_photo_order, order_new_production, order_new_buying, \
    order_list, order_edit, order_delete, order_edit_manager, order_new_delivery, order_detail_manager, \
    order_detail_client, order_status_new, order_status_list, order_status_edit, order_status_delete

app_name = "orders"

urlpatterns = [
    path('new-searching/', order_new_searching, name='new-searching'),
    path('new-production/', order_new_production, name='new-production'),
    path('new-buying/', order_new_buying, name='new-buying'),
    path('new-delivery/', order_new_delivery, name='new-delivery'),
    path('list-order/', order_list, name='list-orders'),
    path('list-order-manager/', order_list_manager, name='list-order-manager'),
    path('list-order-manager/<uuid:pk>/edit/', order_edit_manager, name='edit-order-manager'),
    path('list-order/<uuid:pk>/edit/', order_edit, name='edit-order'),
    path('list-order/<uuid:pk>/delete/', order_delete, name='delete-order'),
    path('delete-photo/<uuid:pk>/', delete_photo_order, name='delete-photo'),
    path('list-order-manager/<uuid:pk>/', order_detail_manager, name='detail-order-manager'),
    path('list-order/<uuid:pk>/', order_detail_client, name='detail-order-client'),
    path('create-order-status', order_status_new, name='create-order-status'),
    path('list-order-status', order_status_list, name='list-order-status'),
    path('list-order-status/<uuid:pk>/edit/', order_status_edit, name='edit-order-status'),
    path('delete-order-status/<uuid:pk>/', order_status_delete, name='delete-order-status'),
]
