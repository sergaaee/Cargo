from django.db import models


class StateType(models.Choices):
    PERFECT = 'Perfect'
    BROKEN_PACKAGE = 'Broken package'
    BROKEN_ITEM = 'Broken item'
    LOST = 'Lost'


class PackageType(models.Choices):
    CARTOON_BOX = 'Cartoon Box'
    ENVELOPE = 'Envelope'
    SCOTCH_TAPE_BAG = 'Scotch Tape Bag'
    CASE = 'Case'


class DeliveryType(models.Choices):
    AVIA = 'Avia'
    EXPRESS_TRAIN = 'Express Train'
    AUTO = 'Auto'
    AUTO_MEDAL = 'Auto Medal'


class PackageStatus(models.Choices):
    RECEIVED = 'Received'
    TEMPLATE = 'Template'
    UNIDENTIFIED = 'Unidentified'
    DECLINED = 'Declined'
    UNDECIDED = 'Undecided'


class CodeStatus(models.Choices):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'


class TrackerStatus(models.Choices):
    COMPLETED = 'Completed'
    PARTLY_COMPLETED = 'Partly Completed'
    INCOMPLETE = 'Incomplete'
