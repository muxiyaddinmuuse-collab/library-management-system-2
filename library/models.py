from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def books_count(self):
        return self.books.count()


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Book Title")
    author = models.CharField(max_length=150, verbose_name="Author")
    isbn = models.CharField(max_length=30, unique=True, verbose_name="ISBN Number")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books', verbose_name="Category")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Total Copies")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="Available Copies")
    publication_year = models.PositiveIntegerField(blank=True, null=True, verbose_name="Publication Year")
    location_shelf = models.CharField(max_length=100, blank=True, null=True, verbose_name="Shelf / Location", help_text="e.g. Shelf B-2")
    description = models.TextField(blank=True, null=True, verbose_name="Description / Summary")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        super().clean()
        if self.available_copies is not None and self.total_copies is not None:
            if self.available_copies > self.total_copies:
                raise ValidationError({
                    'available_copies': "Available copies cannot exceed total copies."
                })

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def borrowed_copies_count(self):
        return max(0, self.total_copies - self.available_copies)


class Member(models.Model):
    MEMBERSHIP_TYPE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Staff', 'Staff'),
        ('General', 'General Public'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
    ]

    member_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Member ID")
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone = models.CharField(max_length=30, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Residential Address")
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPE_CHOICES, default='Student', verbose_name="Membership Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name="Account Status")
    registered_date = models.DateField(auto_now_add=True, verbose_name="Registration Date")

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ['-registered_date', 'first_name']

    def __str__(self):
        return f"{self.member_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.member_id:
            # Auto-generate member ID like MEM-1001
            last_member = Member.objects.all().order_by('id').last()
            if last_member and last_member.id:
                next_id = last_member.id + 1
            else:
                next_id = 1
            self.member_id = f"MEM-{next_id + 1000}"
        super().save(*args, **kwargs)

    @property
    def active_borrow_count(self):
        return self.borrow_records.filter(status='Borrowed').count()


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('Borrowed', 'Borrowed'),
        ('Returned', 'Returned'),
        ('Overdue', 'Overdue'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records', verbose_name="Book")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='borrow_records', verbose_name="Member")
    issue_date = models.DateField(default=date.today, verbose_name="Issue Date")
    due_date = models.DateField(verbose_name="Due Date")
    return_date = models.DateField(null=True, blank=True, verbose_name="Return Date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Borrowed', verbose_name="Status")
    fine_amount = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'), verbose_name="Fine Amount ($)")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Remarks")
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Issued By")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Borrow Record"
        verbose_name_plural = "Borrow Records"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.book.title} issued to {self.member.full_name}"

    def clean(self):
        super().clean()
        if self.issue_date and self.due_date:
            if self.due_date < self.issue_date:
                raise ValidationError({
                    'due_date': "Due date cannot be earlier than issue date."
                })

    @property
    def is_currently_overdue(self):
        if self.status == 'Borrowed' and date.today() > self.due_date:
            return True
        return False

    @property
    def days_overdue(self):
        if self.status == 'Borrowed' and date.today() > self.due_date:
            return (date.today() - self.due_date).days
        elif self.return_date and self.return_date > self.due_date:
            return (self.return_date - self.due_date).days
        return 0

    def compute_fine(self, rate_per_day=Decimal('1.00')):
        overdue_days = self.days_overdue
        if overdue_days > 0:
            return Decimal(overdue_days) * rate_per_day
        return Decimal('0.00')
