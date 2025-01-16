from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Book, UserProfile, Borrowing, Returning
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator

# Index view to display all books with pagination and search functionality
@login_required
def index(request):
    search_query = request.GET.get('search', '')
    books = Book.objects.all()

    if search_query:
        books = books.filter(title__icontains=search_query)

    paginator = Paginator(books, 5)  # Show 5 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {'page_obj': page_obj})


# Borrow book functionality
@login_required
def borrowbook(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == "POST":
        # Check if the book is available for borrowing
        if book.is_available:
            book.is_available = False
            book.save()

            # Get the borrow period from the POST data (default to 120 days)
            borrow_period = request.POST.get('borrow_period', 120)
            try:
                borrow_period = int(borrow_period)
            except ValueError:
                borrow_period = 120  # Default to 120 days if the value is invalid

            # Calculate the return date based on the borrow period
            return_date = timezone.now().date() + timedelta(days=borrow_period)

            # Create a borrowing record for this book
            borrowing = Borrowing.objects.create(
                book=book,
                borrower=request.user,
                return_date=return_date,
                borrow_period=borrow_period
            )
            borrowing.save()

            # Notify the user of successful borrowing
            messages.info(request, f"You have successfully borrowed '{book.title}'. Please return it by {return_date}.")
            return redirect("index")  # Redirect to the book details page
        else:
            # If the book is not available, show an error message
            messages.error(request, f"Sorry, '{book.title}' is currently unavailable.")
            return redirect("borrow-book", id=book.id)  # Redirect back to the borrow page

    return render(request, "borrowbook.html", {"book": book})  # Render the borrowing form



# Return book functionality
@login_required
def returnbook(request, id):
    # Get the borrowing record by ID
    borrowing = get_object_or_404(Borrowing, id=id)

    if request.method == "POST":
        # Get the return date from the POST data (ensure it is a valid date)
        return_date_str = request.POST.get('return_date')
        lost = 'lost' in request.POST  # Check if the book is marked as lost

        try:
            return_date = timezone.datetime.strptime(return_date_str, "%Y-%m-%d").date() if return_date_str else timezone.now().date()
        except ValueError:
            messages.error(request, "Invalid return date provided.")
            return redirect("return-book", id=id)

        # Update the borrowing record as returned
        borrowing.lost = lost
        borrowing.is_returned = True
        borrowing.return_date = return_date  # Store the return date
        borrowing.save()

        # Update the book's status (increment book_count and set availability)
        book = borrowing.book
        book.book_count += 1
        book.is_available = True
        book.save()

        # Create the Returning record
        returning = Returning.objects.create(
            borrowing=borrowing,
            book=book,
            borrower=borrowing.borrower,
            return_date=return_date
        )

        # Calculate any fees (e.g., late fees, lost fees) based on the return date
        returning.calculate_fees()

        messages.info(request, f"Book '{book.title}' returned successfully.")

        return redirect("dashboard")  # Redirect to the dashboard or any relevant page

    return render(request, "returnbook.html", {"borrowing": borrowing})  # Render the return book page



# Add book functionality (only available for staff)
@login_required
def addbook(request):
    if not request.user.is_staff:
        return redirect("index")

    if request.method == "POST":
        title = request.POST['title']
        author = request.POST['author']
        isbn = request.POST['isbn']
        price = request.POST['price']
        book_count = int(request.POST['book_count'])

        if Book.objects.filter(title=title).exists():
            messages.info(request, f"{title} already exists!")
            return redirect("index")
        elif Book.objects.filter(isbn=isbn).exists():
            messages.info(request, f"A book with ISBN {isbn} already exists!")
            return redirect("index")
        else:
            book = Book(title=title, author=author, isbn=isbn, price=price, book_count=book_count)
            book.save()

            messages.info(request, f'{title} added successfully.')
            return redirect("index")

    return render(request, 'addbook.html')


# Edit book functionality (only available for staff)
@login_required
def editbook(request, id):
    if not request.user.is_staff:
        return redirect("index")

    book = get_object_or_404(Book, id=id)

    if request.method == "POST":
        title = request.POST['title']
        author = request.POST['author']
        isbn = request.POST['isbn']
        price = request.POST['price']

        book.title = title
        book.author = author
        book.isbn = isbn
        book.price = price
        book.save()

        messages.info(request, f"{title} updated successfully!")
        return redirect("index")

    return render(request, "editbook.html", {"book": book})


# Delete book functionality (only available for staff)
@login_required
def deletebook(request, id):
    if not request.user.is_staff:
        return redirect("index")

    book = get_object_or_404(Book, id=id)

    if request.method == "POST":
        book_title = book.title
        book.delete()
        messages.info(request, f"{book_title} deleted successfully!")
        return redirect("index")

    return render(request, "deletebook.html", {"book": book})


# User registration functionality
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        phone_number = request.POST['phoneNumber']
        password = request.POST['password']
        confirmPassword = request.POST['confirmPassword']
        gender = request.POST['gender']
        address = request.POST['address']

        if len(password) < 8:
            messages.info(request, "Password should be at least 8 characters long")
            return redirect('register')

        if not username.isalnum():
            messages.info(request, "Username should only contain letters and numbers")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.info(request, f"Username {username} already exists!")
            return redirect('register')
        elif UserProfile.objects.filter(phone=phone_number).exists():
            messages.info(request, 'Phone number already exists.')
            return redirect('register')

        if password != confirmPassword:
            messages.info(request, "Passwords do not match")
            return redirect('register')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            user_profile = UserProfile.objects.create(
                user=user,
                phone=phone_number,
                gender=gender,
                address=address
            )
            user_profile.save()
            messages.info(request, f"{username} registered successfully!")
            return redirect('login')

    return render(request, "register.html")


# Login functionality
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')
    else:
        return render(request, 'login.html')


# Logout functionality
def logout(request):
    auth_logout(request)
    return redirect('index')


# User dashboard view showing borrowed books with pagination
@login_required
def user_dashboard(request):
    user = request.user
    borrowed_books = Borrowing.objects.filter(borrower=user)
    borrowed_books_with_fees = []

    for borrowing in borrowed_books:
        overdue_fee = borrowing.calculate_overdue_fees()
        lost_fee = borrowing.calculate_lost_book_fees()
        total_fee = overdue_fee + lost_fee
        borrowed_books_with_fees.append({
            'borrowing': borrowing,
            'overdue_fee': overdue_fee,
            'lost_fee': lost_fee,
            'total_fee': total_fee
        })

    paginator = Paginator(borrowed_books_with_fees, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "user_dashboard.html", {
        "borrowed_books_with_fees": borrowed_books_with_fees,
        "page_obj": page_obj,
        "search_query": request.GET.get('search', '')
    })


# Admin dashboard for librarians to see all borrowings with pagination
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    borrowed_books = Borrowing.objects.all()
    borrowed_books_with_fees = []

    for borrowing in borrowed_books:
        overdue_fee = borrowing.calculate_overdue_fees()
        lost_fee = borrowing.calculate_lost_book_fees()
        total_fee = overdue_fee + lost_fee
        borrowed_books_with_fees.append({
            'borrowing': borrowing,
            'overdue_fee': overdue_fee,
            'lost_fee': lost_fee,
            'total_fee': total_fee
        })

    paginator = Paginator(borrowed_books_with_fees, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "admin_dashboard.html", {"page_obj": page_obj})


# Search for borrowed books by a specific borrower for admins
@login_required
@user_passes_test(lambda u: u.is_staff)
def search_borrower(request):
    search_query = request.GET.get('search', '')
    borrowed_books = Borrowing.objects.filter(borrower__username__icontains=search_query)

    borrowed_books_with_fees = []
    for borrowing in borrowed_books:
        overdue_fee = borrowing.calculate_overdue_fees()
        lost_fee = borrowing.calculate_lost_book_fees()
        total_fee = overdue_fee + lost_fee
        borrowed_books_with_fees.append({
            'borrowing': borrowing,
            'overdue_fee': overdue_fee,
            'lost_fee': lost_fee,
            'total_fee': total_fee
        })

    return render(request, "search_borrower.html", {
        "borrowed_books_with_fees": borrowed_books_with_fees,
        "search_query": search_query
    })


# Clear a return and mark it as returned for admin
@login_required
@user_passes_test(lambda u: u.is_staff)
def clear_return(request, id):
    borrowing = get_object_or_404(Borrowing, id=id)

    if not borrowing.is_returned:
        borrowing.is_returned = True
        borrowing.book.book_count += 1
        borrowing.book.is_available = borrowing.book.book_count > 0
        borrowing.book.save()

        returning = Returning.objects.create(
            borrowing=borrowing,
            book=borrowing.book,
            borrower=borrowing.borrower,
            return_date=timezone.now().date()
        )

        returning.calculate_fees()
        borrowing.save()

        messages.info(request, f"Book '{borrowing.book.title}' has been marked as returned.")
    else:
        messages.info(request, f"Book '{borrowing.book.title}' has already been returned.")

    return redirect('admin-dashboard')


# Mark a book as available for admin
@login_required
@user_passes_test(lambda u: u.is_staff)
def mark_available(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.book_count > 0:
        book.is_available = True
        book.save()

        messages.success(request, f"Book '{book.title}' is now available.")
    else:
        messages.error(request, f"Book '{book.title}' cannot be marked as available. No copies left.")

    return redirect('admin-dashboard')


# Update availability status of a book
def update_availability(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == 'POST':
        # Get the value of the 'is_available' field from the form
        is_available = request.POST.get('is_available')#'True' if checked, otherwise 'False'
        if is_available == 'True':
            book.book_count += 1
            # Update the book's availability
            book.is_available = is_available
            book.save()  # Save the updated book

            # Add a success message
            messages.success(request, f"Availability of '{book.title}' updated successfully.")
        else:
            book.book_count -= 1
        # Redirect to the book details page or another appropriate page
            return redirect('borrow-book', id=book.id)

    return render(request, 'update_availability.html', {'book': book})
