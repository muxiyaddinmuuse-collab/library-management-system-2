from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Category, Book, Member, BorrowRecord
from .forms import (
    CategoryForm, BookForm, MemberForm,
    BorrowBookForm, ReturnBookForm,
    LibrarianLoginForm, LibrarianRegisterForm
)


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LibrarianLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! You are now logged in.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LibrarianLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LibrarianRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LibrarianRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


# ==============================================================================
# DASHBOARD
# ==============================================================================

@login_required
def dashboard_view(request):
    today = date.today()

    # Dynamic status update for overdue records
    overdue_records = BorrowRecord.objects.filter(status='Borrowed', due_date__lt=today)

    total_members = Member.objects.count()
    active_borrows = BorrowRecord.objects.filter(status='Borrowed').count()
    total_books = Book.objects.count()
    
    copies_stat = Book.objects.aggregate(
        total=Sum('total_copies'),
        available=Sum('available_copies')
    )
    total_copies = copies_stat['total'] or 0
    available_copies = copies_stat['available'] or 0
    borrowed_copies = max(0, total_copies - available_copies)

    total_fines = BorrowRecord.objects.aggregate(fines=Sum('fine_amount'))['fines'] or Decimal('0.00')
    total_categories = Category.objects.count()
    overdue_count = overdue_records.count()

    recent_borrows = BorrowRecord.objects.select_related('book', 'member').order_by('-created_at')[:6]
    recent_books = Book.objects.select_related('category').order_by('-created_at')[:5]

    context = {
        'total_members': total_members,
        'active_borrows': active_borrows,
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'borrowed_copies': borrowed_copies,
        'total_fines': total_fines,
        'total_categories': total_categories,
        'overdue_count': overdue_count,
        'recent_borrows': recent_borrows,
        'recent_books': recent_books,
        'today': today,
    }
    return render(request, 'dashboard/dashboard.html', context)


# ==============================================================================
# BOOKS CRUD & SEARCH
# ==============================================================================

@login_required
def book_list_view(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    books = Book.objects.select_related('category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    if status_filter == 'available':
        books = books.filter(available_copies__gt=0)
    elif status_filter == 'out_of_stock':
        books = books.filter(available_copies=0)

    categories = Category.objects.all()

    context = {
        'books': books,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status_filter,
        'total_results': books.count(),
    }
    return render(request, 'books/book_list.html', context)


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk)
    borrow_history = book.borrow_records.select_related('member').order_by('-created_at')[:10]
    return render(request, 'books/book_detail.html', {'book': book, 'borrow_history': borrow_history})


@login_required
def book_create_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' was successfully registered!")
            return redirect('book_list')
        else:
            messages.error(request, "Failed to register book. Please verify the input values.")
    else:
        form = BookForm()

    return render(request, 'books/book_form.html', {'form': form, 'title': 'Register New Book', 'action': 'Create'})


@login_required
def book_update_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' was updated successfully!")
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, "Failed to update book. Please review form errors.")
    else:
        form = BookForm(instance=book)

    return render(request, 'books/book_form.html', {'form': form, 'title': f"Edit Book: {book.title}", 'action': 'Update', 'book': book})


@login_required
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f"Book '{title}' was deleted successfully.")
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})


# ==============================================================================
# CATEGORIES CRUD
# ==============================================================================

@login_required
def category_list_view(request):
    query = request.GET.get('q', '').strip()
    categories = Category.objects.annotate(book_total=Count('books')).order_by('name')

    if query:
        categories = categories.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    context = {
        'categories': categories,
        'query': query,
    }
    return render(request, 'categories/category_list.html', context)


@login_required
def category_create_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created successfully!")
            return redirect('category_list')
        else:
            messages.error(request, "Please check the entered category information.")
    else:
        form = CategoryForm()

    return render(request, 'categories/category_form.html', {'form': form, 'title': 'Add New Category', 'action': 'Create'})


@login_required
def category_update_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' updated successfully!")
            return redirect('category_list')
        else:
            messages.error(request, "Error updating category.")
    else:
        form = CategoryForm(instance=category)

    return render(request, 'categories/category_form.html', {'form': form, 'title': f"Edit Category: {category.name}", 'action': 'Update', 'category': category})


@login_required
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted successfully.")
        return redirect('category_list')
    return render(request, 'categories/category_confirm_delete.html', {'category': category})


# ==============================================================================
# MEMBERS CRUD
# ==============================================================================

@login_required
def member_list_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()

    members = Member.objects.all()

    if query:
        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(member_id__icontains=query)
        )

    if status_filter:
        members = members.filter(status=status_filter)

    if type_filter:
        members = members.filter(membership_type=type_filter)

    context = {
        'members': members,
        'query': query,
        'selected_status': status_filter,
        'selected_type': type_filter,
    }
    return render(request, 'members/member_list.html', context)


@login_required
def member_detail_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    borrow_records = member.borrow_records.select_related('book').order_by('-created_at')
    active_borrows = borrow_records.filter(status='Borrowed')
    returned_borrows = borrow_records.filter(status='Returned')

    context = {
        'member': member,
        'active_borrows': active_borrows,
        'returned_borrows': returned_borrows,
        'total_borrows': borrow_records.count(),
    }
    return render(request, 'members/member_detail.html', context)


@login_required
def member_create_view(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Library member '{member.full_name}' ({member.member_id}) registered successfully!")
            return redirect('member_list')
        else:
            messages.error(request, "Could not register member. Check form fields.")
    else:
        form = MemberForm()

    return render(request, 'members/member_form.html', {'form': form, 'title': 'Register New Member', 'action': 'Register'})


@login_required
def member_update_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.full_name}' updated successfully!")
            return redirect('member_detail', pk=member.pk)
        else:
            messages.error(request, "Failed to update member.")
    else:
        form = MemberForm(instance=member)

    return render(request, 'members/member_form.html', {'form': form, 'title': f"Edit Member: {member.full_name}", 'action': 'Update', 'member': member})


@login_required
def member_delete_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f"Member '{name}' was deleted.")
        return redirect('member_list')
    return render(request, 'members/member_confirm_delete.html', {'member': member})


# ==============================================================================
# BORROW & RETURN OPERATIONS
# ==============================================================================

@login_required
def borrow_list_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    borrows = BorrowRecord.objects.select_related('book', 'member', 'issued_by').all()

    today = date.today()

    if query:
        borrows = borrows.filter(
            Q(book__title__icontains=query) |
            Q(book__isbn__icontains=query) |
            Q(member__first_name__icontains=query) |
            Q(member__last_name__icontains=query) |
            Q(member__member_id__icontains=query)
        )

    if status_filter == 'borrowed':
        borrows = borrows.filter(status='Borrowed', due_date__gte=today)
    elif status_filter == 'returned':
        borrows = borrows.filter(status='Returned')
    elif status_filter == 'overdue':
        borrows = borrows.filter(status='Borrowed', due_date__lt=today)

    context = {
        'borrows': borrows,
        'query': query,
        'selected_status': status_filter,
        'today': today,
    }
    return render(request, 'borrows/borrow_list.html', context)


@login_required
def borrow_create_view(request):
    book_id = request.GET.get('book_id')
    member_id = request.GET.get('member_id')

    if request.method == 'POST':
        form = BorrowBookForm(request.POST)
        if form.is_valid():
            borrow_record = form.save(commit=False)
            book = borrow_record.book

            if book.available_copies <= 0:
                messages.error(request, f"Cannot issue '{book.title}': No available copies left in library.")
                return render(request, 'borrows/borrow_form.html', {'form': form, 'title': 'Issue / Borrow Book'})

            # Deduct 1 available copy
            book.available_copies -= 1
            book.save()

            borrow_record.issued_by = request.user
            borrow_record.status = 'Borrowed'
            borrow_record.save()

            messages.success(request, f"Book '{book.title}' was successfully issued to {borrow_record.member.full_name}!")
            return redirect('borrow_list')
        else:
            messages.error(request, "Failed to issue book. Please check the errors below.")
    else:
        initial_data = {}
        if book_id:
            try:
                initial_data['book'] = Book.objects.get(pk=book_id)
            except Book.DoesNotExist:
                pass
        if member_id:
            try:
                initial_data['member'] = Member.objects.get(pk=member_id)
            except Member.DoesNotExist:
                pass
        form = BorrowBookForm(initial=initial_data)

    return render(request, 'borrows/borrow_form.html', {'form': form, 'title': 'Issue Book to Member'})


@login_required
def borrow_return_view(request, pk):
    borrow_record = get_object_or_404(BorrowRecord.objects.select_related('book', 'member'), pk=pk)

    if borrow_record.status == 'Returned':
        messages.warning(request, f"This book was already returned on {borrow_record.return_date}.")
        return redirect('borrow_list')

    today = date.today()
    calculated_fine = borrow_record.compute_fine(rate_per_day=Decimal('1.00'))

    if request.method == 'POST':
        form = ReturnBookForm(request.POST, instance=borrow_record)
        if form.is_valid():
            record = form.save(commit=False)
            record.status = 'Returned'
            if not record.return_date:
                record.return_date = today
            record.save()

            # Increase available copies of the book
            book = record.book
            if book.available_copies < book.total_copies:
                book.available_copies += 1
                book.save()

            messages.success(
                request,
                f"Book '{book.title}' successfully returned by {record.member.full_name}!"
                + (f" Fine recorded: ${record.fine_amount}" if record.fine_amount > 0 else "")
            )
            return redirect('borrow_list')
        else:
            messages.error(request, "Error processing book return.")
    else:
        form = ReturnBookForm(
            instance=borrow_record,
            initial={
                'return_date': today,
                'fine_amount': calculated_fine
            }
        )

    context = {
        'form': form,
        'record': borrow_record,
        'calculated_fine': calculated_fine,
        'days_overdue': borrow_record.days_overdue,
        'title': f"Return Book: {borrow_record.book.title}",
    }
    return render(request, 'borrows/borrow_return.html', context)


@login_required
def borrow_detail_view(request, pk):
    record = get_object_or_404(BorrowRecord.objects.select_related('book', 'member', 'issued_by'), pk=pk)
    return render(request, 'borrows/borrow_detail.html', {'record': record})
