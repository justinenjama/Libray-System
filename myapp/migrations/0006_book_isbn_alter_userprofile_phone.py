# Generated by Django 5.1.2 on 2024-12-17 12:32

import myapp.models
from django.db import migrations, models

def set_unique_isbn(apps, schema_editor):
    Book = apps.get_model('myapp', 'Book')
    for book in Book.objects.all():
        # Set a default ISBN if it doesn't have one (you could customize this logic)
        if not book.isbn:
            book.isbn = "DEFAULTISBN" + str(book.id)  # Unique ISBN per book (based on ID)
            book.save()
class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0005_returning"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="isbn",
            field=models.CharField(default="0000000000000", max_length=13, unique=True),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(
                max_length=15,
                unique=True,
                validators=[myapp.models.validate_phone_number],
            ),
        ),
    ]
