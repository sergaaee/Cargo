from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from PIL import Image
from deliveries.choices import StateType, PackageType, PackageStatus
from deliveries.mixins import UUIDMixin, TimeStampedMixin
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField

class Photo(UUIDMixin, TimeStampedMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE, related_name='images_set')
    photo = models.ImageField(upload_to ='images/')

    # resizing the image, you can change parameters like size and quality.
    def save(self, *args, **kwargs):
       super(Photo, self).save(*args, **kwargs)
       img = Image.open(self.photo.path)
       if img.height > 1125 or img.width > 1125:
           img.thumbnail((1125,1125))
       img.save(self.photo.path,quality=70,optimize=True)


class Tag(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('Name'), max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        indexes = [
            models.Index(fields=['id'], name='tag_pkey'),
            models.Index(fields=['name'], name='tag_name_idx')
        ]


class Incoming(UUIDMixin, TimeStampedMixin):
    track_number = models.CharField(_('Track Number'), max_length=1000, null=True, blank=True)
    inventory_number = models.CharField(_('Inventory Number, spaces between'), max_length=1000, default='')
    places_count = models.IntegerField(_('Places count'), default=0, validators=[MinValueValidator(1)])
    arrival_date = models.DateTimeField(_('Arrival date'), blank=True, null=True)
    size = models.CharField(_('Size (LxHxW)'), blank=True, null=True)
    weight = models.IntegerField(_('Weight (kg)'), blank=True, null=True, validators=[MinValueValidator(0)])
    state = models.CharField(_('State'), choices=StateType.choices, default=StateType.PERFECT, max_length=100)
    package_type = models.CharField(_('Package type'), choices=PackageType.choices, default=PackageType.CARTOON_BOX, max_length=100)
    status = models.CharField(_('Status'), choices=PackageStatus.choices, default=PackageStatus.UNDECIDED, max_length=100)

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, blank=True, null=True)
    images = models.ManyToManyField(Photo, through='PhotoIncoming', related_name='incoming_images', blank=True)

    def __str__(self):
        return self.track_number

    class Meta:
        verbose_name = _('Incoming')
        verbose_name_plural = _('Incomings')
        indexes = [
            models.Index(fields=['id'], name='incoming_idx'),
            models.Index(fields=['track_number'], name='incoming_track_number_idx')

        ]


class TagIncoming(UUIDMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['incoming_id', 'tag_id'], name='tag_incoming_idx'),
        ]


class PhotoIncoming(UUIDMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['incoming_id', 'photo_id'], name='photo_incoming_idx'),
        ]