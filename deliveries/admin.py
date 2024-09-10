from django.contrib import admin
from .models import Incoming, Tag, TagIncoming, Photo


class TagIncomingInline(admin.TabularInline):
    model = TagIncoming


class PhotoAdmin(admin.TabularInline):
    model = Photo
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Incoming)
class IncomingAdmin(admin.ModelAdmin):
    inlines = [PhotoAdmin]

    list_display = ('track_number', 'arrival_date', 'places_count', 'weight')
    search_fields = ['track_number', 'inventory_numbers']
