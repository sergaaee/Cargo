from django.urls import path

from .views import order_list_manager, order_new_searching, delete_photo_order, order_new_production, order_new_buying, order_list, order_edit, order_delete

app_name = "orders"

urlpatterns = [
    path('new-searching/', order_new_searching, name='new-searching'),
    path('new-production/', order_new_production, name='new-production'),
    path('new-buying/', order_new_buying, name='new-buying'),
    path('list-order/', order_list, name='list-orders'),
    path('list-order-manager/', order_list_manager, name='list-order-manager'),
    path('list-order/<uuid:pk>/edit/', order_edit, name='edit-order'),
    path('list-order/<uuid:pk>/delete/', order_delete, name='delete-order'),
    path('delete-photo/<uuid:pk>/', delete_photo_order, name='delete-photo'),
]
