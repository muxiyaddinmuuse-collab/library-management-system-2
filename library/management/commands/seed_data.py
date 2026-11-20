from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from library.models import Category, Book, Member, BorrowRecord


class Command(BaseCommand):
    help = "Seeds initial sample data for the Library Management System"

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for Group 2 LMS...")

        # 1. Create Default Admin/Librarian User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Library',
                'last_name': 'Administrator',
                'email': 'admin@library.edu',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        if created:
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))
        else:
            self.stdout.write(self.style.SUCCESS("Updated admin password to: admin123"))

        # 2. Categories
        categories_data = [
            ("Computer Science & AI", "Algorithms, Python, Artificial Intelligence, and Systems"),
            ("Software Engineering", "Clean code, web architecture, design patterns, and agile methods"),
            ("Database Systems", "Relational databases, SQL, NoSQL, and data modeling"),
            ("Mathematics & Statistics", "Linear algebra, calculus, probability, and discrete mathematics"),
            ("Literature & Fiction", "Classic world novels, poetry, and modern prose"),
            ("Business & Leadership", "Entrepreneurship, economics, management, and strategy"),
        ]

        categories_map = {}
        for name, desc in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories_map[name] = cat
        self.stdout.write(self.style.SUCCESS(f"Categories ready: {len(categories_map)}"))

        # 3. Books
        books_data = [
            {
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "isbn": "978-0132350884",
                "category": categories_map["Software Engineering"],
                "total_copies": 5,
                "available_copies": 4,
                "publication_year": 2008,
                "location_shelf": "Shelf A-1",
                "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
            },
            {
                "title": "Introduction to Algorithms (4th Edition)",
                "author": "Thomas H. Cormen, Charles E. Leiserson",
                "isbn": "978-0262046305",
                "category": categories_map["Computer Science & AI"],
                "total_copies": 4,
                "available_copies": 3,
                "publication_year": 2022,
                "location_shelf": "Shelf A-2",
                "description": "Comprehensive textbook on computer algorithms, covering a broad range of data structures and analysis.",
            },
            {
                "title": "Django for Beginners: Build websites with Python and Django",
                "author": "William S. Vincent",
                "isbn": "978-1735467221",
                "category": categories_map["Software Engineering"],
                "total_copies": 6,
                "available_copies": 4,
                "publication_year": 2024,
                "location_shelf": "Shelf B-1",
                "description": "Step-by-step guide to building web applications with the Django framework.",
            },
            {
                "title": "Designing Data-Intensive Applications",
                "author": "Martin Kleppmann",
                "isbn": "978-1449373320",
                "category": categories_map["Database Systems"],
                "total_copies": 4,
                "available_copies": 3,
                "publication_year": 2017,
                "location_shelf": "Shelf B-3",
                "description": "The definitive guide to the architecture, data models, reliability and scalability of storage engines.",
            },
            {
                "title": "Artificial Intelligence: A Modern Approach",
                "author": "Stuart Russell, Peter Norvig",
                "isbn": "978-0134610993",
                "category": categories_map["Computer Science & AI"],
                "total_copies": 3,
                "available_copies": 2,
                "publication_year": 2020,
                "location_shelf": "Shelf C-1",
                "description": "The leading textbook in AI, exploring intelligent agents, neural networks, and modern probabilistic models.",
            },
            {
                "title": "The Lean Startup",
                "author": "Eric Ries",
                "isbn": "978-0307887894",
                "category": categories_map["Business & Leadership"],
                "total_copies": 4,
                "available_copies": 4,
                "publication_year": 2011,
                "location_shelf": "Shelf D-2",
                "description": "How today's entrepreneurs use continuous innovation to create radically successful businesses.",
            },
            {
                "title": "To Kill a Mockingbird",
                "author": "Harper Lee",
                "isbn": "978-0061120084",
                "category": categories_map["Literature & Fiction"],
                "total_copies": 5,
                "available_copies": 5,
                "publication_year": 1960,
                "location_shelf": "Shelf E-1",
                "description": "The unforgettable novel of a childhood in a sleepy Southern town and the crisis of conscience that rocked it.",
            },
        ]

        books_map = {}
        for b_data in books_data:
            book, _ = Book.objects.get_or_create(isbn=b_data["isbn"], defaults=b_data)
            books_map[book.title] = book
        self.stdout.write(self.style.SUCCESS(f"Books ready: {len(books_map)}"))

        # 4. Members
        members_data = [
            ("Maxamed", "Abiib", "maxamed.abiib@university.edu", "+252 61 555 1001", "Student", "Hodan District, Mogadishu"),
            ("Nimco", "Axmed", "nimco.axmed@university.edu", "+252 61 555 1002", "Student", "Wadajir, Mogadishu"),
            ("Subeer", "Jaamac", "subeer.jaamac@university.edu", "+252 61 555 1003", "Student", "Hawl-Wadaag, Mogadishu"),
            ("Muxiyadiin", "Maxamuud", "muxiyadiin@university.edu", "+252 61 555 1004", "Student", "Karaan, Mogadishu"),
            ("Najma", "Cali", "najma.cali@university.edu", "+252 61 555 1005", "Teacher", "Shibis, Mogadishu"),
            ("Khadar", "Cumar", "khadar.cumar@university.edu", "+252 61 555 1006", "Teacher", "Daynile, Mogadishu"),
        ]

        members_list = []
        for fn, ln, email, phone, mtype, addr in members_data:
            member, _ = Member.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'phone': phone,
                    'membership_type': mtype,
                    'address': addr,
                    'status': 'Active',
                }
            )
            members_list.append(member)
        self.stdout.write(self.style.SUCCESS(f"Members ready: {len(members_list)}"))

        # 5. Borrow Records (Active, Returned, Overdue)
        today = date.today()

        # Record 1: Active normal loan
        clean_code = Book.objects.get(isbn="978-0132350884")
        m_maxamed = Member.objects.get(email="maxamed.abiib@university.edu")
        BorrowRecord.objects.get_or_create(
            book=clean_code,
            member=m_maxamed,
            issue_date=today - timedelta(days=5),
            defaults={
                'due_date': today + timedelta(days=9),
                'status': 'Borrowed',
                'issued_by': admin_user,
                'notes': 'Course textbook checkout.',
            }
        )

        # Record 2: Active Overdue loan (demonstrates late alert and fine)
        django_book = Book.objects.get(isbn="978-1735467221")
        m_subeer = Member.objects.get(email="subeer.jaamac@university.edu")
        BorrowRecord.objects.get_or_create(
            book=django_book,
            member=m_subeer,
            issue_date=today - timedelta(days=20),
            defaults={
                'due_date': today - timedelta(days=6),  # 6 days overdue
                'status': 'Borrowed',
                'issued_by': admin_user,
                'notes': 'Overdue notice sent via email.',
            }
        )

        # Record 3: Another active loan
        algo_book = Book.objects.get(isbn="978-0262046305")
        m_nimco = Member.objects.get(email="nimco.axmed@university.edu")
        BorrowRecord.objects.get_or_create(
            book=algo_book,
            member=m_nimco,
            issue_date=today - timedelta(days=3),
            defaults={
                'due_date': today + timedelta(days=11),
                'status': 'Borrowed',
                'issued_by': admin_user,
                'notes': 'Algorithm midterm preparation.',
            }
        )

        # Record 4: Returned loan with fine
        ai_book = Book.objects.get(isbn="978-0134610993")
        m_najma = Member.objects.get(email="najma.cali@university.edu")
        BorrowRecord.objects.get_or_create(
            book=ai_book,
            member=m_najma,
            issue_date=today - timedelta(days=30),
            defaults={
                'due_date': today - timedelta(days=16),
                'return_date': today - timedelta(days=12),
                'status': 'Returned',
                'fine_amount': Decimal('4.00'),
                'issued_by': admin_user,
                'notes': 'Returned 4 days late, $4 fine paid in full.',
            }
        )

        self.stdout.write(self.style.SUCCESS("Sample data seeding completed successfully!"))
