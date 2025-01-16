from django.contrib import admin
from .models import Book, UserProfile, Borrowing, Returning

# Inline admin for Borrowing model
class BorrowingInline(admin.TabularInline):
    model = Borrowing
    extra = 0  # Number of empty rows to show by default (0 means no empty rows)
    fields = ['borrower', 'borrow_date', 'borrow_period', 'is_returned', 'lost']  # Fields to show in the inline form

# Custom admin for Book model
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'is_available', 'book_count')
    list_editable = ('is_available', 'book_count')  # Allows inline editing of is_available and book_count
    search_fields = ('title', 'author', 'isbn')

# Custom admin for UserProfile model
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'phone']
    search_fields = ['user__username', 'phone']
    list_filter = ['user']

# Custom admin for Borrowing model
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'book','borrow_date', 'return_date', 'is_returned', 'lost', 'calculate_overdue_fees', 'calculate_lost_book_fees']
    list_filter = ['is_returned', 'borrow_date', 'return_date', 'lost']
    search_fields = ['borrower__username', 'book__title']
    
    def calculate_overdue_fees(self, obj):
        return obj.calculate_overdue_fees()
    calculate_overdue_fees.short_description = 'Overdue Fees'

    def calculate_lost_book_fees(self, obj):
        return obj.calculate_lost_book_fees()
    calculate_lost_book_fees.short_description = 'Lost Book Fees'

# Custom admin for Returning model
class ReturningAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'book', 'return_date', 'fees_paid']
    search_fields = ['borrower__username', 'book__title']
    list_filter = ['return_date']

    # You can display a calculated value like 'fees_paid'
    def fees_paid(self, obj):
        return obj.calculate_fees()  # Assuming calculate_fees() is a method that exists on Returning
    fees_paid.short_description = 'Fees Paid'

# Register the models with the custom admin views
admin.site.register(Book, BookAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Borrowing, BorrowingAdmin)
admin.site.register(Returning, ReturningAdmin)
