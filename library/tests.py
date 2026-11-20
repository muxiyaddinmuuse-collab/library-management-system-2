from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Category, Book, Member, BorrowRecord


class LibrarySystemQualityTests(TestCase):
    """
    Comprehensive test suite ensuring code quality, security,
    data integrity, model validations, and business logic.
    """

    def setUp(self):
        self.client = Client()

        # Create staff librarian user
        self.librarian = User.objects.create_user(
            username='librarian_test',
            password='testpassword123',
            email='librarian@example.com',
            first_name='Test',
            last_name='Librarian'
        )

        # Create sample category
        self.category = Category.objects.create(
            name='Computer Science',
            description='Tech books and manuals'
        )

        # Create sample book with 3 copies
        self.book = Book.objects.create(
            title='Django Web Development',
            author='John Doe',
            isbn='978-1111111111',
            category=self.category,
            total_copies=3,
            available_copies=3,
            publication_year=2024,
            location_shelf='Shelf A-1'
        )

        # Create active member
        self.member = Member.objects.create(
            first_name='Ali',
            last_name='Hassan',
            email='ali@example.com',
            phone='+252 61 000 0000',
            membership_type='Student',
            status='Active'
        )

    # --------------------------------------------------------------------------
    # 1. AUTHENTICATION & ACCESS CONTROL TESTS
    # --------------------------------------------------------------------------

    def test_unauthenticated_redirect(self):
        """Unauthenticated requests to protected pages must redirect to /login/"""
        protected_urls = [
            reverse('dashboard'),
            reverse('book_list'),
            reverse('member_list'),
            reverse('borrow_list'),
            reverse('category_list'),
            reverse('profile'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)

    def test_login_flow_success(self):
        """Valid credentials log the librarian in and grant access to dashboard"""
        response = self.client.post(reverse('login'), {
            'username': 'librarian_test',
            'password': 'testpassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_flow_invalid_credentials(self):
        """Invalid credentials show error and deny authentication"""
        response = self.client.post(reverse('login'), {
            'username': 'librarian_test',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Invalid username or password')

    # --------------------------------------------------------------------------
    # 2. BOOKS CRUD & SEARCH TESTS
    # --------------------------------------------------------------------------

    def test_book_crud_lifecycle(self):
        """Tests the full lifecycle of creating, reading, updating, and deleting a book"""
        self.client.login(username='librarian_test', password='testpassword123')

        # Create
        create_res = self.client.post(reverse('book_create'), {
            'title': 'Clean Architecture',
            'author': 'Robert C. Martin',
            'isbn': '978-0134494166',
            'category': self.category.id,
            'total_copies': 4,
            'available_copies': 4,
            'publication_year': 2017,
            'location_shelf': 'Shelf B-1',
            'description': 'A Craftsman Guide to Software Structure'
        }, follow=True)
        self.assertEqual(create_res.status_code, 200)
        self.assertTrue(Book.objects.filter(isbn='978-0134494166').exists())
        book = Book.objects.get(isbn='978-0134494166')

        # Read / Detail
        detail_res = self.client.get(reverse('book_detail', args=[book.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Clean Architecture')

        # Update
        update_res = self.client.post(reverse('book_update', args=[book.pk]), {
            'title': 'Clean Architecture (2nd Edition)',
            'author': 'Robert C. Martin',
            'isbn': '978-0134494166',
            'category': self.category.id,
            'total_copies': 5,
            'available_copies': 5,
            'publication_year': 2018,
            'location_shelf': 'Shelf B-2',
            'description': 'Updated description'
        }, follow=True)
        self.assertEqual(update_res.status_code, 200)
        book.refresh_from_db()
        self.assertEqual(book.title, 'Clean Architecture (2nd Edition)')
        self.assertEqual(book.total_copies, 5)

        # Delete
        delete_res = self.client.post(reverse('book_delete', args=[book.pk]), follow=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_search_and_filter_books(self):
        """Tests searching by title, author, and filtering by category"""
        self.client.login(username='librarian_test', password='testpassword123')

        # Search by Title
        res_title = self.client.get(reverse('book_list'), {'q': 'Django'})
        self.assertContains(res_title, 'Django Web Development')

        # Search by Author
        res_author = self.client.get(reverse('book_list'), {'q': 'John Doe'})
        self.assertContains(res_author, 'Django Web Development')

        # Search by ISBN
        res_isbn = self.client.get(reverse('book_list'), {'q': '978-1111111111'})
        self.assertContains(res_isbn, 'Django Web Development')

        # Category Filter
        res_cat = self.client.get(reverse('book_list'), {'category': self.category.id})
        self.assertContains(res_cat, 'Django Web Development')

    # --------------------------------------------------------------------------
    # 3. CIRCULATION & STOCK INTEGRITY TESTS
    # --------------------------------------------------------------------------

    def test_borrow_and_return_cycle(self):
        """Tests issuing and returning a book correctly modifies available_copies"""
        self.client.login(username='librarian_test', password='testpassword123')

        initial_available = self.book.available_copies

        # 1. Issue Book
        issue_res = self.client.post(reverse('borrow_create'), {
            'book': self.book.id,
            'member': self.member.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=14)),
            'notes': 'Normal loan test'
        }, follow=True)
        self.assertEqual(issue_res.status_code, 200)

        # Stock should be decremented by 1
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, initial_available - 1)

        record = BorrowRecord.objects.get(book=self.book, member=self.member, status='Borrowed')
        self.assertEqual(record.status, 'Borrowed')

        # 2. Return Book
        return_res = self.client.post(reverse('borrow_return', args=[record.pk]), {
            'return_date': str(date.today()),
            'fine_amount': '0.00',
            'notes': 'Book returned in good condition'
        }, follow=True)
        self.assertEqual(return_res.status_code, 200)

        # Stock should be restored
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, initial_available)

        record.refresh_from_db()
        self.assertEqual(record.status, 'Returned')

    def test_cannot_borrow_out_of_stock_book(self):
        """Negative test: Attempting to borrow when available copies is 0 is rejected by form"""
        self.client.login(username='librarian_test', password='testpassword123')

        self.book.available_copies = 0
        self.book.save()

        response = self.client.post(reverse('borrow_create'), {
            'book': self.book.id,
            'member': self.member.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=14)),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BorrowRecord.objects.filter(book=self.book, member=self.member).exists())
        self.assertContains(response, 'Select a valid choice')

    def test_inactive_member_cannot_borrow(self):
        """Negative test: Inactive or suspended members cannot borrow books"""
        self.client.login(username='librarian_test', password='testpassword123')

        self.member.status = 'Suspended'
        self.member.save()

        response = self.client.post(reverse('borrow_create'), {
            'book': self.book.id,
            'member': self.member.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=14)),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BorrowRecord.objects.filter(book=self.book, member=self.member).exists())
        self.assertContains(response, 'Select a valid choice')

    # --------------------------------------------------------------------------
    # 4. MODEL VALIDATION & BUSINESS LOGIC TESTS
    # --------------------------------------------------------------------------

    def test_available_copies_cannot_exceed_total(self):
        """Negative test: Model validation fails when available_copies > total_copies"""
        invalid_book = Book(
            title='Invalid Copies',
            author='Tester',
            isbn='978-9999999999',
            category=self.category,
            total_copies=2,
            available_copies=5
        )
        with self.assertRaises(ValidationError):
            invalid_book.clean()

    def test_due_date_cannot_precede_issue_date(self):
        """Negative test: Due date before issue date raises ValidationError"""
        invalid_loan = BorrowRecord(
            book=self.book,
            member=self.member,
            issue_date=date.today(),
            due_date=date.today() - timedelta(days=1),
            status='Borrowed'
        )
        with self.assertRaises(ValidationError):
            invalid_loan.clean()

    def test_member_id_auto_generation(self):
        """Member save automatically creates formatted ID like MEM-100X"""
        m = Member.objects.create(
            first_name='Fatima',
            last_name='Farah',
            email='fatima@example.com',
            phone='+252 61 111 2222'
        )
        self.assertTrue(m.member_id.startswith('MEM-'))
        self.assertGreaterEqual(len(m.member_id), 8)

    def test_overdue_fine_computation(self):
        """Tests mathematical calculation of overdue fine at $1 per day"""
        loan = BorrowRecord.objects.create(
            book=self.book,
            member=self.member,
            issue_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=5),  # 5 days overdue
            status='Borrowed'
        )
        self.assertTrue(loan.is_currently_overdue)
        self.assertEqual(loan.days_overdue, 5)
        self.assertEqual(loan.compute_fine(rate_per_day=Decimal('1.00')), Decimal('5.00'))

    def test_category_crud_operations(self):
        """Tests Category creation, book relation counter, and deletion"""
        self.client.login(username='librarian_test', password='testpassword123')

        cat = Category.objects.create(name='Data Science', description='Machine learning books')
        self.assertEqual(cat.books_count, 0)

        # Attach book
        self.book.category = cat
        self.book.save()
        self.assertEqual(cat.books_count, 1)
