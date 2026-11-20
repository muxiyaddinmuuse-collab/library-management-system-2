from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from decimal import Decimal


class Category(models.Model):
    """
    Represents a genre, department, or classification for books in the library.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def books_count(self) -> int:
        """Returns the total number of books registered in this category."""
        return self.books.count()


class Book(models.Model):
    """
    Represents a book title and its inventory within the library catalog.
    """
    title = models.CharField(max_length=200, verbose_name="Book Title")
    author = models.CharField(max_length=150, verbose_name="Author")
    isbn = models.CharField(max_length=30, unique=True, verbose_name="ISBN Number")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='books',
        verbose_name="Category"
    )
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Total Copies")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="Available Copies")
    publication_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Publication Year"
    )
    location_shelf = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Shelf / Location",
        help_text="e.g. Shelf B-2"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description / Summary")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['isbn']),
        ]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    def clean(self):
        super().clean()
        if self.available_copies is not None and self.total_copies is not None:
            if self.available_copies > self.total_copies:
                raise ValidationError({
                    'available_copies': "Available copies cannot exceed total copies."
                })

    @property
    def is_available(self) -> bool:
        """Checks if there is at least one copy currently available to borrow."""
        return self.available_copies > 0

    @property
    def borrowed_copies_count(self) -> int:
        """Returns the number of copies currently out on loan."""
        return max(0, self.total_copies - self.available_copies)


class Member(models.Model):
    """
    Represents a registered library patron (Student, Teacher, Staff, or General Public).
    """
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
    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_TYPE_CHOICES,
        default='Student',
        verbose_name="Membership Type"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active',
        verbose_name="Account Status"
    )
    registered_date = models.DateField(auto_now_add=True, verbose_name="Registration Date")

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ['-registered_date', 'first_name']
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f"{self.member_id} - {self.full_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.member_id:
            # Auto-generate unique member ID with collision prevention
            last_member = Member.objects.all().order_by('id').last()
            next_num = (last_member.id + 1) if last_member and last_member.id else 1
            candidate = f"MEM-{next_num + 1000}"
            while Member.objects.filter(member_id=candidate).exists():
                next_num += 1
                candidate = f"MEM-{next_num + 1000}"
            self.member_id = candidate
        super().save(*args, **kwargs)

    @property
    def active_borrow_count(self) -> int:
        """Returns the number of active book loans for this member."""
        return self.borrow_records.filter(status='Borrowed').count()


class BorrowRecord(models.Model):
    """
    Represents an issuance/loan transaction of a book to a library member.
    """
    STATUS_CHOICES = [
        ('Borrowed', 'Borrowed'),
        ('Returned', 'Returned'),
        ('Overdue', 'Overdue'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrow_records',
        verbose_name="Book"
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='borrow_records',
        verbose_name="Member"
    )
    issue_date = models.DateField(default=date.today, verbose_name="Issue Date")
    due_date = models.DateField(verbose_name="Due Date")
    return_date = models.DateField(null=True, blank=True, verbose_name="Return Date")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Borrowed',
        verbose_name="Status"
    )
    fine_amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Fine Amount ($)"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Remarks")
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Issued By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Borrow Record"
        verbose_name_plural = "Borrow Records"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['issue_date']),
        ]

    def __str__(self) -> str:
        return f"{self.book.title} issued to {self.member.full_name}"

    def clean(self):
        super().clean()
        if self.issue_date and self.due_date:
            if self.due_date < self.issue_date:
                raise ValidationError({
                    'due_date': "Due date cannot be earlier than issue date."
                })

    @property
    def is_currently_overdue(self) -> bool:
        """Checks if the loan is currently active and past its due date."""
        if self.status == 'Borrowed' and date.today() > self.due_date:
            return True
        return False

    @property
    def days_overdue(self) -> int:
        """Calculates how many days late the book is (or was when returned)."""
        if self.status == 'Borrowed' and date.today() > self.due_date:
            return (date.today() - self.due_date).days
        elif self.return_date and self.return_date > self.due_date:
            return (self.return_date - self.due_date).days
        return 0

    def compute_fine(self, rate_per_day: Decimal = Decimal('1.00')) -> Decimal:
        """Calculates the assessed fine based on days overdue and daily rate."""
        overdue_days = self.days_overdue
        if overdue_days > 0:
            return Decimal(overdue_days) * rate_per_day
        return Decimal('0.00')
