# Generated by Django 4.1.7 on 2023-08-01 14:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ads", "0005_alter_ad_price_alter_ad_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ad",
            name="location",
            field=models.CharField(max_length=255, null=True),
        ),
    ]