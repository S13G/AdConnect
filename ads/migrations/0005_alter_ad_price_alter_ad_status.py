# Generated by Django 4.1.7 on 2023-08-01 05:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ads", "0004_alter_adcategory_image_alter_adimage_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ad",
            name="price",
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name="ad",
            name="status",
            field=models.CharField(
                choices=[
                    ("Paused", "Paused"),
                    ("Denied", "Denied"),
                    ("Pending", "Pending"),
                    ("Active", "Active"),
                ],
                default="Pending",
                max_length=20,
                null=True,
            ),
        ),
    ]
