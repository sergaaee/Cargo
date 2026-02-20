from django.db import models
from django.utils.translation import gettext_lazy as _

class StateType(models.Choices):
    PERFECT = 'Perfect'
    BROKEN_PACKAGE = 'Broken package'
    BROKEN_ITEM = 'Broken item'
    LOST = 'Lost'

class PackageTypeChoices(models.TextChoices):
    CARTON_BOX = "CARTON_BOX", _("Carton box")
    BAG = "BAG", _("Bag")

class PackageStatus(models.Choices):
    RECEIVED = 'Received'
    TEMPLATE = 'Template'
    UNIDENTIFIED = 'Unidentified'
    DECLINED = 'Declined'
    UNDECIDED = 'Undecided'


class PackagedStatuses(models.Choices):
    PACKAGED = 'Packaged'
    SENT = 'Sent'
    DELIVERED = 'Delivered'


class CodeStatus(models.Choices):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'


class TrackerStatus(models.Choices):
    COMPLETED = 'Completed'
    PARTLY_COMPLETED = 'Partly Completed'
    INCOMPLETE = 'Incomplete'
