from django.urls import path

from .views import order_new_searching, delete_photo_order, order_new_production, order_new_buying

app_name = "orders"

urlpatterns = [
    path('new-searching/', order_new_searching, name='new-searching'),
    path('new-production', order_new_production, name='new-production'),
    path('new-buying', order_new_buying, name='new-buying'),
    path('delete-photo/<uuid:pk>/', delete_photo_order, name='delete-photo'),
]
