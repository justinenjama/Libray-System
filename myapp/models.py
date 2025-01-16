from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

# Custom validation for phone number format
def validate_phone_number(value):
    if not re.match(r'^\+?[1-9]\d{1,14}$', value):  # Example regex for international phone numbers
        raise ValidationError(f"{value} is not a valid phone number.")

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    isbn = models.CharField(max_length=13, unique=True, default="0000000000000")  # ISBN is unique
    book_count = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        """
        Override the save method to automatically update `is_available` based on `book_count`.
        If the `book_count` is more than 0, the book is available.
        """
        self.is_available = self.book_count > 0  # Automatically update availability
        super().save(*args, **kwargs)

    def return_book(self):
        """
        Increments the `book_count` when a book is returned and updates availability.
        """
        self.book_count += 1  # Increase the book count when the book is returned
        self.save()  # This will also update `is_available` if needed

    def __str__(self):
        return f"{self.title} by {self.author} - ${self.price}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    phone = models.CharField(max_length=15, unique=True, validators=[validate_phone_number])
    address = models.CharField(max_length=255, blank=True, null=True)  # Additional field for address

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Borrowing(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    borrow_date = models.DateField(null=True, blank=True)  # Automatically set when the object is created
    borrow_period = models.PositiveIntegerField()  # Number of days
    return_date = models.DateField()  # Calculated return date
    is_returned = models.BooleanField(default=False)
    lost = models.BooleanField(default=False)
    extra_days = models.PositiveIntegerField(default=0)
    fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Ensure borrow_date is set before calculating return_date
        if not self.borrow_date:
            self.borrow_date = timezone.now().date()  
        self.return_date = self.borrow_date + timedelta(days=self.borrow_period)

        if self.book.book_count < 1:
            raise ValueError(f"Sorry, '{self.book.title}' is currently unavailable.")

        self.book.book_count -= 1
        self.book.is_available = self.book.book_count > 0
        self.book.save()

        super().save(*args, **kwargs)

    def calculate_overdue_fees(self):
        """Calculate overdue fees if the book is returned late."""
        if self.is_returned or self.lost:
            return 0
        today = timezone.now().date()
        overdue_days = (today - self.return_date).days
        if overdue_days > 0:
            return overdue_days * 10 
        return 0

    def calculate_lost_book_fees(self):
        """Calculate the lost book fees, which could be the price of the book."""
        if self.lost:
            overdue_fees = self.calculate_overdue_fees()
            return self.book.price + overdue_fees
        return 0

    def calculate_total_fees(self):
        """Calculate the total fees (overdue + lost)"""
        overdue_fees = self.calculate_overdue_fees()
        lost_fees = self.calculate_lost_book_fees()
        return overdue_fees + lost_fees

    def __str__(self):
        return f"{self.book.title} borrowed by {self.borrower.username}"


class Returning(models.Model):
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE, related_name="return_records")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    return_date = models.DateField(auto_now_add=True)
    overdue_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lost_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_fees(self):
        """Calculate overdue and lost fees, and update total fee"""
        if self.borrowing.lost:
            self.lost_fee = self.borrowing.calculate_lost_book_fees()
        else:
            self.overdue_fee = self.borrowing.calculate_overdue_fees()

        self.total_fee = self.lost_fee + self.overdue_fee
        self.borrowing.fees_paid += self.total_fee
        self.borrowing.save()

        # Save the return record with the updated fees
        self.save()

    def __str__(self):
        return f"Return Record for {self.book.title} by {self.borrower.username}"