# Generated by Django 5.1.5 on 2025-01-28 17:37

import almet.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almet', '0006_remove_appeals_photo_appealphoto'),
    ]

    operations = [
        migrations.AddField(
            model_name='appeals',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to=almet.models.get_upload_path),
        ),
        migrations.DeleteModel(
            name='AppealPhoto',
        ),
    ]
