from django.urls import path
from . import views

urlpatterns = [
    # Home & Dashboard
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),

    # Books CRUD
    path('books/', views.book_list_view, name='book_list'),
    path('books/new/', views.book_create_view, name='book_create'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_update_view, name='book_update'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),

    # Categories CRUD
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/new/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update_view, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # Members CRUD
    path('members/', views.member_list_view, name='member_list'),
    path('members/new/', views.member_create_view, name='member_create'),
    path('members/<int:pk>/', views.member_detail_view, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_update_view, name='member_update'),
    path('members/<int:pk>/delete/', views.member_delete_view, name='member_delete'),

    # Borrow & Return
    path('borrows/', views.borrow_list_view, name='borrow_list'),
    path('borrows/issue/', views.borrow_create_view, name='borrow_create'),
    path('borrows/<int:pk>/', views.borrow_detail_view, name='borrow_detail'),
    path('borrows/<int:pk>/return/', views.borrow_return_view, name='borrow_return'),
]
