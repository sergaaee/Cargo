from django.db import models


class OrderStatus(models.Choices):
    UNDER_REVIEW = 'Under review'
    DECLINED = 'Declined'
    WORKING_AT = 'Working at'
