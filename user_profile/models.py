from django.db import models
from django.contrib.auth.models import User

class ClientManagerRelation(models.Model):
    client = models.ForeignKey(
        User,
        related_name='client_relations',
        on_delete=models.CASCADE,
        limit_choices_to={'groups__name': 'Clients'}
    )
    manager = models.ForeignKey(
        User,
        related_name='manager_relations',
        on_delete=models.CASCADE,
        limit_choices_to={'groups__name': 'Managers'}
    )

    def __str__(self):
        return f'{self.manager.username} -> {self.client.username}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'
