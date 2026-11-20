from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Category, Book, Member, BorrowRecord


class LibrarySystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create librarian user
        self.user = User.objects.create_user(
            username='librarian_test',
            password='testpassword123',
            email='librarian@example.com'
        )

        # Create category
        self.category = Category.objects.create(
            name='Computer Science',
            description='Tech books'
        )

        # Create book
        self.book = Book.objects.create(
            title='Django Web Development',
            author='John Doe',
            isbn='978-1111111111',
            category=self.category,
            total_copies=5,
            available_copies=5,
            location_shelf='Shelf A-1'
        )

        # Create member
        self.member = Member.objects.create(
            first_name='Ali',
            last_name='Hassan',
            email='ali@example.com',
            phone='+252 61 000 0000',
            membership_type='Student',
            status='Active'
        )

    def test_unauthenticated_redirect(self):
        """Unauthenticated requests to protected pages redirect to login"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_login_flow(self):
        """User can log in successfully"""
        response = self.client.post(reverse('login'), {
            'username': 'librarian_test',
            'password': 'testpassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_book_crud(self):
        """Test Book Create, Read, Update, Delete"""
        self.client.login(username='librarian_test', password='testpassword123')

        # 1. Create
        create_res = self.client.post(reverse('book_create'), {
            'title': 'Python Tricks',
            'author': 'Dan Bader',
            'isbn': '978-2222222222',
            'category': self.category.id,
            'total_copies': 3,
            'available_copies': 3,
            'location_shelf': 'Shelf B-2',
            'description': 'Helpful Python tips'
        }, follow=True)
        self.assertEqual(create_res.status_code, 200)
        self.assertTrue(Book.objects.filter(isbn='978-2222222222').exists())
        new_book = Book.objects.get(isbn='978-2222222222')

        # 2. Read / Detail
        detail_res = self.client.get(reverse('book_detail', args=[new_book.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Python Tricks')

        # 3. Update
        update_res = self.client.post(reverse('book_update', args=[new_book.pk]), {
            'title': 'Python Tricks (Updated)',
            'author': 'Dan Bader',
            'isbn': '978-2222222222',
            'category': self.category.id,
            'total_copies': 4,
            'available_copies': 4,
            'location_shelf': 'Shelf B-3',
            'description': 'Updated'
        }, follow=True)
        self.assertEqual(update_res.status_code, 200)
        new_book.refresh_from_db()
        self.assertEqual(new_book.title, 'Python Tricks (Updated)')
        self.assertEqual(new_book.total_copies, 4)

        # 4. Delete
        delete_res = self.client.post(reverse('book_delete', args=[new_book.pk]), follow=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertFalse(Book.objects.filter(pk=new_book.pk).exists())

    def test_search_books(self):
        """Test search by title or author"""
        self.client.login(username='librarian_test', password='testpassword123')

        # Search by title
        res_title = self.client.get(reverse('book_list'), {'q': 'Django'})
        self.assertContains(res_title, 'Django Web Development')

        # Search by author
        res_author = self.client.get(reverse('book_list'), {'q': 'John Doe'})
        self.assertContains(res_author, 'Django Web Development')

        # Search non-existent
        res_none = self.client.get(reverse('book_list'), {'q': 'NonExistentBookXYZ'})
        self.assertNotContains(res_none, 'Django Web Development')

    def test_borrow_and_return_cycle(self):
        """Test issuing and returning a book properly adjusts available copies"""
        self.client.login(username='librarian_test', password='testpassword123')

        initial_available = self.book.available_copies

        # 1. Issue Book
        issue_res = self.client.post(reverse('borrow_create'), {
            'book': self.book.id,
            'member': self.member.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today() + timedelta(days=14)),
            'notes': 'Test issue'
        }, follow=True)
        self.assertEqual(issue_res.status_code, 200)

        # Check stock reduced by 1
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, initial_available - 1)

        record = BorrowRecord.objects.get(book=self.book, member=self.member, status='Borrowed')
        self.assertIsNotNone(record)

        # 2. Return Book
        return_res = self.client.post(reverse('borrow_return', args=[record.pk]), {
            'return_date': str(date.today()),
            'fine_amount': '0.00',
            'notes': 'Returned in great condition'
        }, follow=True)
        self.assertEqual(return_res.status_code, 200)

        # Check stock restored by 1
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, initial_available)

        record.refresh_from_db()
        self.assertEqual(record.status, 'Returned')
