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


class PackageStatus(models.Choices):
    RECEIVED = 'Received'
    DECLINED = 'Declined'
    TO_DELIVER = 'To Deliver'
    STORED = 'Stored'
    UNDECIDED = 'Undecided'