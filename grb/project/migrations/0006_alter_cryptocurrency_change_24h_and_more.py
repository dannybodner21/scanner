# Generated by Django 4.2.8 on 2024-11-27 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_cryptocurrency_price_change_10min_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cryptocurrency',
            name='change_24h',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='cryptocurrency',
            name='close_price',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='cryptocurrency',
            name='last_price',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='cryptocurrency',
            name='volume_24h',
            field=models.FloatField(default=0.0),
        ),
    ]