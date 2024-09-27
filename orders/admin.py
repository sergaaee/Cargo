from django.contrib import admin
from .models import Order, PhotoForOrder


class PhotoForOrderAdmin(admin.TabularInline):
    model = PhotoForOrder
    extra = 1


@admin.register(Order)
class IncomingAdmin(admin.ModelAdmin):
    inlines = [PhotoForOrderAdmin]

    list_display = ('name', 'description', 'order_type')
    search_fields = ['name', 'description']
