# Generated by Django 4.1.7 on 2023-08-16 08:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matrimonials", "0008_alter_matrimonialprofile_income"),
    ]

    operations = [
        migrations.AlterField(
            model_name="matrimonialprofileimage",
            name="image",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
