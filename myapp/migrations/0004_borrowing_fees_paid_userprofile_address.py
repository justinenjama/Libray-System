# Generated by Django 5.1.2 on 2024-12-17 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0003_book_author_book_is_available_alter_book_price_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="borrowing",
            name="fees_paid",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="address",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
