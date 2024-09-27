from PIL import Image
from deliveries.choices import *
from deliveries.mixins import UUIDMixin, TimeStampedMixin
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class PhotoForOrder(UUIDMixin, TimeStampedMixin):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name=_('Order'), related_name='images_set')
    photo = models.ImageField(upload_to='images/')

    def save(self, *args, **kwargs):
        super(PhotoForOrder, self).save(*args, **kwargs)
        img = Image.open(self.photo.path)
        if img.height > 1125 or img.width > 1125:
            img.thumbnail((1125, 1125))
        img.save(self.photo.path, quality=70, optimize=True)


class PhotoOrder(UUIDMixin):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    photo = models.ForeignKey('PhotoForOrder', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['order_id', 'photo_id'], name='photo_order_idx'),
        ]


class Order(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Created by'),
                                   blank=True)
    order_type = models.CharField(_('Type'), max_length=100, default='Searching')
    images = models.ManyToManyField(PhotoForOrder, through='PhotoOrder', related_name='order_images', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        indexes = [
            models.Index(fields=['id'], name='order_pkey'),
            models.Index(fields=['name'], name='order_name_idx')
        ]
