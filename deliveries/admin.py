from django.contrib import admin
from .models import Incoming, Tag, TagIncoming, Photo, TrackerIncoming, Tracker, InventoryNumber


class TagIncomingInline(admin.TabularInline):
    model = TagIncoming


class PhotoAdmin(admin.TabularInline):
    model = Photo
    extra = 1


class TrackerIncomingInline(admin.TabularInline):
    model = TrackerIncoming
    extra = 1


@admin.register(InventoryNumber)
class InventoryNumberAdmin(admin.ModelAdmin):
    search_fields = ['number']
    list_display = ['number', 'is_occupied']


@admin.register(Tracker)
class TrackerAdmin(admin.ModelAdmin):
    inlines = [TrackerIncomingInline]
    search_fields = ['name']
    list_display = ['name', 'status', 'source', 'created_by']
    fields = ['name', 'source', 'created_by']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'created_by']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Incoming)
class IncomingAdmin(admin.ModelAdmin):
    inlines = [PhotoAdmin, TrackerIncomingInline]

    list_display = ('arrival_date', 'places_count', 'weight')
    search_fields = ['inventory_numbers']
