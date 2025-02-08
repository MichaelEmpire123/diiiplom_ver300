# Generated by Django 5.1.5 on 2025-02-08 11:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almet', '0011_message_image_alter_message_id_sitizen_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='id_sitizen',
        ),
        migrations.RemoveField(
            model_name='message',
            name='id_sotrudnik',
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
