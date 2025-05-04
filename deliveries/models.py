from django.core.validators import MinValueValidator

from PIL import Image
from deliveries.choices import *
from deliveries.mixins import UUIDMixin, TimeStampedMixin
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Photo(UUIDMixin, TimeStampedMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE, related_name='images_set', blank=True, null=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, related_name='images_set_place', blank=True, null=True)
    photo = models.ImageField(upload_to='images/')

    # resizing the image, you can change parameters like size and quality.
    def save(self, *args, **kwargs):
        super(Photo, self).save(*args, **kwargs)
        img = Image.open(self.photo.path)
        if img.height > 1125 or img.width > 1125:
            img.thumbnail((1125, 1125))
        img.save(self.photo.path, quality=70, optimize=True)


class InventoryNumber(UUIDMixin, TimeStampedMixin):
    number = models.CharField(max_length=100, unique=True)
    is_occupied = models.BooleanField(default=False)
    tracker_code = models.ForeignKey('TrackerCode', on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='inventory_numbers_tracker_code')

    def __str__(self):
        return self.number


class TrackerCode(UUIDMixin, TimeStampedMixin):
    code = models.CharField(_('Code'), max_length=1000, unique=True)
    status = models.CharField(_('Status'), choices=CodeStatus.choices, default="Inactive")
    inventory_numbers = models.ManyToManyField(InventoryNumber, through='InventoryNumberTrackerCode',
                                               related_name='tracker_code_inventory_numbers', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Created by'),
                                   blank=True, null=True)

    def __str__(self):
        return self.code


class InventoryNumberTrackerCode(UUIDMixin, TimeStampedMixin):
    tracker_code = models.ForeignKey(TrackerCode, on_delete=models.CASCADE)
    inventory_number = models.ForeignKey(InventoryNumber, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['tracker_code_id', 'inventory_number_id'], name='tracker_code_IN_idx'),
        ]


class Tracker(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('Name'), max_length=100)
    status = models.CharField(_('Status'), choices=TrackerStatus.choices, default="Incomplete",
                              max_length=100)
    tracking_codes = models.ManyToManyField(TrackerCode, through='TrackerCodeTracker',
                                            blank=True)
    source = models.CharField(_('Source'), max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Created by'),
                                   null=True)

    def __str__(self):
        return self.name


class TrackerCodeTracker(UUIDMixin):
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)
    tracker_code = models.ForeignKey(TrackerCode, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['tracker_id', 'tracker_code_id'], name='tracker_code_tracker_idx'),
        ]


class TrackerIncoming(UUIDMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    tracker = models.ForeignKey('Tracker', on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['incoming_id'], name='tracker_incoming_idx'),
        ]


class Tag(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('Name'), max_length=100)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=_('Created by'))

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
    places_count = models.IntegerField(_('Places count'), default=0, validators=[MinValueValidator(1)])
    arrival_date = models.DateTimeField(_('Arrival date'), blank=True, null=True)
    size = models.CharField(_('Size (LxHxW)'), blank=True, null=True)
    weight = models.FloatField(_('Weight (kg)'), blank=True, null=True, validators=[MinValueValidator(0)])
    state = models.CharField(_('State'), choices=StateType.choices, default=StateType.PERFECT, max_length=100)
    package_type = models.CharField(_('Package type'), choices=PackageType.choices, default=PackageType.CARTOON_BOX,
                                    max_length=100)
    status = models.CharField(_('Status'), choices=PackageStatus.choices, default=PackageStatus.UNDECIDED,
                              max_length=100)

    volume = models.FloatField(blank=True, null=True, validators=[MinValueValidator(1)])

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='incoming_clients',
        verbose_name=_('Client')
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='incoming_managers',
        verbose_name=_('Manager')
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, blank=True, null=True)

    images = models.ManyToManyField(Photo, through='PhotoIncoming', related_name='incoming_images', blank=True)
    tracker = models.ManyToManyField(Tracker, through='TrackerIncoming', blank=True, verbose_name=_('Tracker'))
    inventory_numbers = models.ManyToManyField(InventoryNumber, through='InventoryNumberIncoming',
                                               related_name='incoming_inventory_numbers', blank=True)

    def __str__(self):
        return f'{self.tracker} ({self.inventory_numbers})'

    class Meta:
        verbose_name = _('Incoming')
        verbose_name_plural = _('Incomings')
        indexes = [
            models.Index(fields=['id'], name='incoming_idx'),
        ]


class ConsolidationIncoming(UUIDMixin):
    consolidation = models.ForeignKey('Consolidation', on_delete=models.CASCADE)
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    places_consolidated = models.IntegerField(_('Places to consolidate'), validators=[MinValueValidator(1)])
    volume_consolidated = models.FloatField(_('Volume'), validators=[MinValueValidator(1)], blank=True, null=True)
    weight_consolidated = models.FloatField(_('Weight (kg)'), blank=True, null=True,
                                              validators=[MinValueValidator(0)])

    class Meta:
        unique_together = (
            'consolidation', 'incoming')  # Чтобы каждое поступление могло участвовать в консолидации только один раз
        indexes = [
            models.Index(fields=['consolidation', 'incoming'], name='consolidation_incoming_idx'),
        ]


class ConsolidationInventory(UUIDMixin, TimeStampedMixin):
    consolidation_incoming = models.ForeignKey(ConsolidationIncoming, on_delete=models.CASCADE)
    inventory_number = models.ForeignKey(InventoryNumber, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('consolidation_incoming', 'inventory_number')
        indexes = [
            models.Index(fields=['consolidation_incoming', 'inventory_number'], name='consolidation_inventory_idx'),
        ]


class Consolidation(UUIDMixin, TimeStampedMixin):
    incomings = models.ManyToManyField(Incoming, through='ConsolidationIncoming', blank=True)
    consolidation_date = models.DateTimeField(_('Consolidation date'), blank=True, null=True)
    track_code = models.ForeignKey(
        'ConsolidationCode',
        on_delete=models.CASCADE,
        related_name='track_code',
        verbose_name=_('Consolidation code'),
        unique=True
    )
    instruction = models.TextField(_('Instruction'), blank=True, null=True)
    delivery_type = models.CharField(
        _('Delivery type'), choices=DeliveryType.choices, default=DeliveryType.AVIA, max_length=100
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        related_name='consolidation_client',
        verbose_name=_('Client')
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        related_name='consolidation_manager',
        verbose_name=_('Manager')
    )

    status = models.CharField(blank=True, null=True, max_length=100, default="Template")
    price = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])

    def __str__(self):
        return f'{self.incomings} ({self.track_code})'


class Place(UUIDMixin, TimeStampedMixin):
    consolidation = models.ForeignKey(
        'Consolidation',
        on_delete=models.CASCADE,
        related_name='places',
        verbose_name=_('Consolidation')
    )
    place_code = models.CharField(
        _('Place Code'),
        max_length=100,
        help_text=_('Unique code for the place, e.g., ST28-1')
    )
    weight = models.FloatField(
        _('Weight (kg)'),
        validators=[MinValueValidator(0)],
        help_text=_('Weight of the place in kilograms'),
        null=True, blank=True
    )
    volume = models.FloatField(
        _('Volume (m^3)'),
        validators=[MinValueValidator(1)],
        help_text=_('Volume of the place in cubic meters'),
        null=True, blank=True
    )
    inventory_numbers = models.ManyToManyField(
        'InventoryNumber',
        through='PlaceInventory',
        related_name='place_inventory_numbers',
        verbose_name=_('Inventory Numbers')
    )
    package_type = models.CharField(
        _('Package type'),
        choices=PackageType.choices,
        default=PackageType.CARTOON_BOX,
        max_length=100
    )

    images = models.ManyToManyField(Photo, through='PhotoPlace', related_name='place_images', blank=True)

    def __str__(self):
        return f"Place {self.place_code} for Consolidation {self.consolidation.track_code}"

    class Meta:
        unique_together = ('consolidation', 'place_code')
        indexes = [
            models.Index(fields=['consolidation', 'place_code'], name='place_consolidation_idx'),
        ]

class PlaceInventory(UUIDMixin, TimeStampedMixin):
    place = models.ForeignKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='place_inventories',
        verbose_name=_('Place')
    )
    inventory_number = models.ForeignKey(
        'InventoryNumber',
        on_delete=models.CASCADE,
        related_name='place_inventory',
        verbose_name=_('Inventory Number')
    )

    class Meta:
        unique_together = ('place', 'inventory_number')
        indexes = [
            models.Index(fields=['place', 'inventory_number'], name='place_inventory_idx'),
        ]


class ConsolidationCode(UUIDMixin, TimeStampedMixin):
    code = models.CharField(_('Code'), max_length=1000, unique=True)
    status = models.CharField(_('Status'), choices=CodeStatus.choices, default="Active")

    def __str__(self):
        return self.code

    @staticmethod
    def generate_code():
        last_code = ConsolidationCode.objects.order_by('-updated_at').first()
        if last_code and last_code.code.startswith('ST'):
            last_number = int(last_code.code[2:])  # Получаем число из кода
            new_number = last_number + 1
        else:
            new_number = 1
        return f'ST{new_number}'


class InventoryNumberIncoming(UUIDMixin):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    inventory_number = models.ForeignKey('InventoryNumber', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['incoming_id', 'inventory_number_id'], name='inventory_number_incoming_idx'),
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


class PhotoPlace(UUIDMixin):
    place = models.ForeignKey('Place', on_delete=models.CASCADE)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['place_id', 'photo_id'], name='photo_place_idx'),
        ]
