# Generated by Django 5.0.3 on 2024-09-06 07:26

import multiselectfield.db.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tag', multiselectfield.db.fields.MultiSelectField(choices=[(1, 'Item title 2.1'), (2, 'Item title 2.2'), (3, 'Item title 2.3'), (4, 'Item title 2.4'), (5, 'Item title 2.5')], max_length=3)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]