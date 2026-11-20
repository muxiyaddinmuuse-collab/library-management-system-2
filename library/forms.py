import re
from datetime import date, timedelta
from decimal import Decimal
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Category, Book, Member, BorrowRecord


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name (e.g., Computer Science, Literature)',
                'required': True,
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional description of this category...',
                'rows': 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise ValidationError("Category name must be at least 2 characters long.")
        return name


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'category',
            'total_copies', 'available_copies', 'publication_year',
            'location_shelf', 'description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 978-0132350884'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024'}),
            'location_shelf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Shelf A-3, Rack 2'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description or summary of the book...'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError("Book title is required.")
        return title

    def clean_author(self):
        author = self.cleaned_data.get('author', '').strip()
        if not author:
            raise ValidationError("Author name is required.")
        return author

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn', '').strip().replace(' ', '')
        if len(isbn) < 5:
            raise ValidationError("Please provide a valid ISBN (at least 5 characters).")
        # Check uniqueness excluding current instance
        qs = Book.objects.filter(isbn__iexact=isbn)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A book with ISBN '{isbn}' is already registered in the library.")
        return isbn

    def clean_publication_year(self):
        year = self.cleaned_data.get('publication_year')
        if year is not None:
            current_year = date.today().year
            if year < 1000 or year > current_year + 1:
                raise ValidationError(f"Please enter a valid publication year between 1000 and {current_year + 1}.")
        return year

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies')
        available = cleaned_data.get('available_copies')

        if total is not None and available is not None:
            if available > total:
                self.add_error('available_copies', 'Available copies cannot be greater than total copies.')
        return cleaned_data


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'membership_type', 'status']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+252 61 XXX XXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'City, District, Street...'}),
            'membership_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name:
            raise ValidationError("First name is required.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name:
            raise ValidationError("Last name is required.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = Member.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"A member with email '{email}' is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if len(phone) < 6:
            raise ValidationError("Phone number must have at least 6 digits.")
        return phone


class BorrowBookForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['book', 'member', 'issue_date', 'due_date', 'notes']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-select'}),
            'member': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional borrow notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0)
            self.fields['member'].queryset = Member.objects.filter(status='Active')
            self.fields['issue_date'].initial = date.today()
            self.fields['due_date'].initial = date.today() + timedelta(days=14)

    def clean(self):
        cleaned_data = super().clean()
        book = cleaned_data.get('book')
        member = cleaned_data.get('member')
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')

        if book and book.available_copies <= 0:
            self.add_error('book', f"'{book.title}' is currently out of stock (0 available copies).")

        if member and member.status != 'Active':
            self.add_error('member', f"Member {member.full_name} is currently {member.status} and cannot borrow books.")

        if issue_date and due_date and due_date < issue_date:
            self.add_error('due_date', "Due date cannot be prior to the issue date.")

        return cleaned_data


class ReturnBookForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['return_date', 'fine_amount', 'notes']
        widgets = {
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fine_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Return notes (condition of book, etc.)'}),
        }

    def clean_fine_amount(self):
        fine = self.cleaned_data.get('fine_amount')
        if fine is not None and fine < Decimal('0.00'):
            raise ValidationError("Fine amount cannot be negative.")
        return fine or Decimal('0.00')

    def clean_return_date(self):
        ret_date = self.cleaned_data.get('return_date')
        if not ret_date:
            ret_date = date.today()
        if self.instance and self.instance.issue_date:
            if ret_date < self.instance.issue_date:
                raise ValidationError("Return date cannot be earlier than the book's issue date.")
        return ret_date


class LibrarianLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Username or Email',
            'autofocus': True,
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )


class LibrarianRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address is already registered.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        for field_name in ['password', 'confirm_password']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
