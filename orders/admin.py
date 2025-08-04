from django.contrib import admin
from .models import Order, PhotoForOrder, OrderStatus


class PhotoForOrderAdmin(admin.TabularInline):
    model = PhotoForOrder
    extra = 1


@admin.register(Order)
class IncomingAdmin(admin.ModelAdmin):
    inlines = [PhotoForOrderAdmin]

    list_display = ('name', 'description', 'order_type', 'manager')
    search_fields = ['name', 'description']
    exclude = ('created_by', 'manager')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.manager = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']

    exclude = ['created_by']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
