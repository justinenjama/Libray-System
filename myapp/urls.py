from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('add-book/', views.addbook, name='add-book'),
    path('edit/<int:id>/', views.editbook, name='edit-book'),
    path('delete/<int:id>/', views.deletebook, name='delete-book'),
    path('borrow-book/<int:id>/', views.borrowbook, name='borrow-book'),
    path('return-book', views.returnbook, name='return-book'),
    path('user-dashboard/', views.user_dashboard, name='user-dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('search-borrower/', views.search_borrower, name='search-borrower'),
    path('clear-return/<int:id>/', views.clear_return, name='clear-return'),
    path('mark-available/<int:book_id>/', views.mark_available, name='mark-available'),
    path('borrow-book/<int:id>/update-availability/', views.update_availability, name='update-availability'),
]
