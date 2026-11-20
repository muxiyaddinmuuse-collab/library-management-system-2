from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods

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
    """
    Renders the Librarian sign-in page and handles authentication.
    Redirects already authenticated users directly to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LibrarianLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! You are now signed in.")
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LibrarianLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logs out the current librarian and redirects to the login screen.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def register_view(request):
    """
    Allows registering a new librarian / staff account.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LibrarianRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff account created for {user.username}! You may now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please review and correct the errors below.")
    else:
        form = LibrarianRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    """
    Displays current librarian profile and account details.
    """
    return render(request, 'accounts/profile.html', {'user': request.user})


# ==============================================================================
# DASHBOARD
# ==============================================================================

@login_required
def dashboard_view(request):
    """
    Main Librarian Control Panel dashboard.
    Calculates live statistics and displays recent circulation records.
    """
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
    """
    Lists all books with instant search (title, author, ISBN) and filters.
    Includes pagination for large inventories.
    """
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page_number = request.GET.get('page', 1)

    books_qs = Book.objects.select_related('category').all()

    if query:
        books_qs = books_qs.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books_qs = books_qs.filter(category_id=category_id)

    if status_filter == 'available':
        books_qs = books_qs.filter(available_copies__gt=0)
    elif status_filter == 'out_of_stock':
        books_qs = books_qs.filter(available_copies=0)

    # Paginate books (15 per page)
    paginator = Paginator(books_qs, 15)
    try:
        books_page = paginator.page(page_number)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    context = {
        'books': books_page,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status_filter,
        'total_results': books_qs.count(),
    }
    return render(request, 'books/book_list.html', context)


@login_required
def book_detail_view(request, pk):
    """
    Displays full details of a specific book, including stock and loan history.
    """
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk)
    borrow_history = book.borrow_records.select_related('member').order_by('-created_at')[:10]
    return render(request, 'books/book_detail.html', {'book': book, 'borrow_history': borrow_history})


@login_required
def book_create_view(request):
    """
    Registers a new book in the library inventory.
    """
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' was successfully registered in the catalog!")
            return redirect('book_list')
        else:
            messages.error(request, "Failed to register book. Please verify all required fields.")
    else:
        form = BookForm()

    return render(request, 'books/book_form.html', {'form': form, 'title': 'Register New Book', 'action': 'Create'})


@login_required
def book_update_view(request, pk):
    """
    Updates an existing book's information.
    """
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
    """
    Deletes a book with confirmation.
    """
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
    """
    Lists all book categories with total book counts and search filter.
    """
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
    """
    Creates a new book category.
    """
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
    """
    Updates an existing category.
    """
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
    """
    Deletes a category with confirmation.
    """
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
    """
    Lists library members with search and status/type filters.
    Includes pagination.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    type_filter = request.GET.get('type', '').strip()
    page_number = request.GET.get('page', 1)

    members_qs = Member.objects.all()

    if query:
        members_qs = members_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(member_id__icontains=query)
        )

    if status_filter:
        members_qs = members_qs.filter(status=status_filter)

    if type_filter:
        members_qs = members_qs.filter(membership_type=type_filter)

    paginator = Paginator(members_qs, 15)
    try:
        members_page = paginator.page(page_number)
    except PageNotAnInteger:
        members_page = paginator.page(1)
    except EmptyPage:
        members_page = paginator.page(paginator.num_pages)

    context = {
        'members': members_page,
        'query': query,
        'selected_status': status_filter,
        'selected_type': type_filter,
    }
    return render(request, 'members/member_list.html', context)


@login_required
def member_detail_view(request, pk):
    """
    Displays full member profile with active loans and past return history.
    """
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
    """
    Registers a new patron/member in the library system.
    """
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
    """
    Updates an existing member's information.
    """
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
    """
    Deletes a member with confirmation.
    """
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f"Member '{name}' was deleted.")
        return redirect('member_list')
    return render(request, 'members/member_confirm_delete.html', {'member': member})


# ==============================================================================
# BORROW & RETURN OPERATIONS (TRANSACTION SAFE)
# ==============================================================================

@login_required
def borrow_list_view(request):
    """
    Lists circulation records with filters (borrowed, returned, overdue) and search.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page_number = request.GET.get('page', 1)

    borrows_qs = BorrowRecord.objects.select_related('book', 'member', 'issued_by').all()

    today = date.today()

    if query:
        borrows_qs = borrows_qs.filter(
            Q(book__title__icontains=query) |
            Q(book__isbn__icontains=query) |
            Q(member__first_name__icontains=query) |
            Q(member__last_name__icontains=query) |
            Q(member__member_id__icontains=query)
        )

    if status_filter == 'borrowed':
        borrows_qs = borrows_qs.filter(status='Borrowed', due_date__gte=today)
    elif status_filter == 'returned':
        borrows_qs = borrows_qs.filter(status='Returned')
    elif status_filter == 'overdue':
        borrows_qs = borrows_qs.filter(status='Borrowed', due_date__lt=today)

    paginator = Paginator(borrows_qs, 15)
    try:
        borrows_page = paginator.page(page_number)
    except PageNotAnInteger:
        borrows_page = paginator.page(1)
    except EmptyPage:
        borrows_page = paginator.page(paginator.num_pages)

    context = {
        'borrows': borrows_page,
        'query': query,
        'selected_status': status_filter,
        'today': today,
    }
    return render(request, 'borrows/borrow_list.html', context)


@login_required
@transaction.atomic
def borrow_create_view(request):
    """
    Issues a book to a member safely within a database transaction.
    Locks the book row to prevent race conditions during copy reduction.
    """
    book_id = request.GET.get('book_id')
    member_id = request.GET.get('member_id')

    if request.method == 'POST':
        form = BorrowBookForm(request.POST)
        if form.is_valid():
            borrow_record = form.save(commit=False)
            
            # Select book with row locking for safe concurrency
            book = Book.objects.select_for_update().get(pk=borrow_record.book.pk)

            if book.available_copies <= 0:
                messages.error(request, f"Cannot issue '{book.title}': No available copies left in library.")
                return render(request, 'borrows/borrow_form.html', {'form': form, 'title': 'Issue / Borrow Book'})

            # Deduct 1 available copy
            book.available_copies -= 1
            book.save(update_fields=['available_copies', 'updated_at'])

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
@transaction.atomic
def borrow_return_view(request, pk):
    """
    Processes book return safely within a database transaction.
    Restores the book's stock and updates fine amount.
    """
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

            # Increase available copies of the book with row locking
            book = Book.objects.select_for_update().get(pk=record.book.pk)
            if book.available_copies < book.total_copies:
                book.available_copies += 1
                book.save(update_fields=['available_copies', 'updated_at'])

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
    """
    Displays full details of a specific circulation record.
    """
    record = get_object_or_404(BorrowRecord.objects.select_related('book', 'member', 'issued_by'), pk=pk)
    return render(request, 'borrows/borrow_detail.html', {'record': record})
