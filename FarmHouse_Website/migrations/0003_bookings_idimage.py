# Generated by Django 5.2.3 on 2025-06-12 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FarmHouse_Website', '0002_menu_reviews_reviewcontent'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookings',
            name='IDimage',
            field=models.BinaryField(default=b''),
        ),
    ]
