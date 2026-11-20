# 📚 Library Management System (LMS)
**Group 2 – Web Application Project**

A complete, modern, responsive Library Management System web application developed using the **Django** backend framework, **SQLite** database, and **Bootstrap 5** frontend with a custom control panel design.

---

## 👥 Group 2 Members & Responsibilities

| Student Name | Role / Area of Responsibility | Planned Contributions |
| :--- | :--- | :--- |
| **Maxamed Abiib** | Backend Architecture & Models | Django project setup, Category & Book models, database migrations |
| **Nimco** | Member Management & Profiles | Member model, Member CRUD views, registration forms, member detail |
| **Subeer** | Circulation & Borrow Engine | BorrowRecord model, Issue Book logic, stock decrement/increment |
| **Muxiyadiin** | Book Management & Search | Book CRUD views, catalog search by title/author/ISBN, category filters |
| **Najma** | Return System & Fine Calculation | Book return processing, overdue calculation, fine tracking & history |
| **Khadar** | Authentication & Dashboard UI | Login/logout system, librarian dashboard stat cards, responsive template |

---

## 🌟 Key Features Implemented

1. **🔐 Authentication & Librarian Login ("Start Login")**:
   - Secure login screen that protects all library circulation and management endpoints.
   - Staff registration and user profile view with role badges.
   - Default demo administrative account provided (`admin` / `admin123`).

2. **📖 Register Books (CRUD Operations)**:
   - Create, Read, Update, and Delete books.
   - Tracks title, author, ISBN, category, total copies, available copies, shelf location, and book summary.
   - Real-time stock availability indicators (Available vs Out of stock).

3. **🏷️ Manage Book Categories (CRUD Operations)**:
   - Create, list, edit, and delete categories/genres.
   - Automatic counter showing the number of books in each category.

4. **👤 Register Library Members (CRUD Operations)**:
   - Register students, teachers, and public library members.
   - Auto-generated member ID (e.g. `MEM-1001`, `MEM-1002`).
   - Member profile view displaying currently active loans and past borrowing history.

5. **🔄 Borrow & Return Books (Circulation Management)**:
   - **Issue / Borrow Book**: Issue an available book to an active member with due date validation; automatically deducts 1 from available copies.
   - **Return Book**: Checks in borrowed books; restores the book's available stock count; automatically detects overdue days and calculates late fees.

6. **📊 Dashboard & Real-Time Tracking**:
   - Built to match the specified design layout (`dashboard tempalate.jpg`).
   - Top 4 vibrant statistic cards: **Members**, **Issued Books**, **Total Books**, **Fines Collected**.
   - Quick navigation action cards: **Manage Book**, **Manage User**, **Categories**, **Issue Book**.
   - Live alerts for overdue books and recent transaction activity.

7. **🔍 Search & Filter Functionality**:
   - Instant search across the catalog by **Book Title**, **Author Name**, or **ISBN Number**.
   - Category filter dropdown and availability filter (All, Available, Out of stock).
   - Search on members table and circulation history table.

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Django Web Framework (MVT Architecture)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, FontAwesome 6 Icons
- **Version Control**: Git & GitHub

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
- Python 3.10+ installed
- Git installed

### 1. Navigate to Project Directory
```bash
cd "library management system 2"
```

### 2. (Optional) Create and Activate Virtual Environment
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Initial Sample Data & Create Admin User
We have built an automated management command that sets up initial categories, books, members, sample loans, and the default librarian user:
```bash
python manage.py seed_data
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your web browser.

---

## 🔑 Default Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Librarian / Administrator** | `admin` | `admin123` |

*(You can also register a new account on the login page or create another superuser using `python manage.py createsuperuser`)*

---

## 🧪 Running Automated Tests

Run the full Django test suite to verify CRUD operations, search, and borrow cycles:
```bash
python manage.py test
```

---

## 🤝 GitHub Collaboration Guidelines (For All 6 Group Members)

Per the instructor's project instructions, **each group member must personally make at least THREE (3) meaningful commits**.

### Recommended Commit Distribution:

#### 1. Maxamed Abiib (Commit Focus: Core Setup & Models)
```bash
git add library/models.py library_system/settings.py
git commit -m "feat(models): implement Category and Book models with custom validations"
git add library/migrations/
git commit -m "feat(db): generate initial database migrations for library models"
git add requirements.txt .gitignore
git commit -m "chore(config): configure gitignore and project requirements"
```

#### 2. Nimco (Commit Focus: Member Management)
```bash
git add library/models.py
git commit -m "feat(member): add Member model with auto-generating member_id"
git add library/forms.py
git commit -m "feat(member-forms): add MemberForm with Bootstrap validation styling"
git add templates/members/
git commit -m "feat(member-ui): create member list, registration, and profile templates"
```

#### 3. Subeer (Commit Focus: Borrowing Engine)
```bash
git add library/models.py
git commit -m "feat(borrow): implement BorrowRecord model with due date and overdue logic"
git add library/views.py
git commit -m "feat(circulation): add borrow_create view with automatic stock deduction"
git add templates/borrows/borrow_form.html
git commit -m "feat(borrow-ui): add book issue form template with active member filter"
```

#### 4. Muxiyadiin (Commit Focus: Book CRUD & Search)
```bash
git add library/forms.py
git commit -m "feat(books): create BookForm with stock validation rules"
git add library/views.py
git commit -m "feat(search): add book search by title, author, and ISBN with category filter"
git add templates/books/
git commit -m "feat(books-ui): implement book catalog table, detail, and delete confirmation"
```

#### 5. Najma (Commit Focus: Return & Fine Calculation)
```bash
git add library/models.py
git commit -m "feat(fines): implement fine calculation and overdue detection methods"
git add library/views.py
git commit -m "feat(return): implement borrow_return view to restore stock and record fines"
git add templates/borrows/borrow_return.html templates/borrows/borrow_list.html
git commit -m "feat(return-ui): build book return check-in interface with fine assessment"
```

#### 6. Khadar (Commit Focus: Authentication & Dashboard)
```bash
git add library/forms.py templates/accounts/
git commit -m "feat(auth): implement customized librarian login and registration templates"
git add templates/base.html static/css/style.css
git commit -m "feat(layout): design responsive navigation bar, sidebar, and custom CSS"
git add templates/dashboard/
git commit -m "feat(dashboard): build dashboard control panel with colored stat cards"
```

### Git Workflow Steps:
1. **Clone repository**:
   ```bash
   git clone <INSTRUCTOR_OR_GROUP_REPO_URL>
   ```
2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Stage and commit changes**:
   ```bash
   git add .
   git commit -m "feat(component): descriptive explanation of your change"
   ```
4. **Push branch to GitHub**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open Pull Request (PR)** on GitHub, have another member review, and merge into `main`.

---

## 📁 Project Architecture & File Structure

```text
library management system 2/
│
├── library_system/             # Django Project Core Settings
│   ├── __init__.py
│   ├── settings.py             # App, DB, Static & Template configurations
│   ├── urls.py                 # Top-level URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── library/                    # LMS Application
│   ├── migrations/             # Database migrations
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py    # Auto-seed sample books, members & admin user
│   ├── admin.py                # Django Admin configurations
│   ├── apps.py
│   ├── forms.py                # Form definitions with Bootstrap validation
│   ├── models.py               # Category, Book, Member, BorrowRecord
│   ├── tests.py                # Comprehensive test suite
│   ├── urls.py                 # App URL patterns
│   └── views.py                # Views for CRUD, search, borrow, return & dashboard
│
├── static/                     # Static Assets
│   ├── css/
│   │   └── style.css           # Custom LMS styling matching the control panel template
│   ├── images/
│   │   ├── logo.png            # LMS Library Logo
│   │   └── dashboard_template.jpg
│   └── js/
│
├── templates/                  # HTML Templates (Bootstrap 5)
│   ├── base.html               # Shared layout (Header, Sidebar, Messages, Footer)
│   ├── accounts/
│   │   ├── login.html          # Start Login page
│   │   ├── register.html       # Staff registration
│   │   └── profile.html        # Librarian profile
│   ├── dashboard/
│   │   └── dashboard.html      # Stat cards & recent circulation table
│   ├── books/
│   │   ├── book_list.html      # Catalog with search & filter
│   │   ├── book_form.html      # Register / Edit book
│   │   ├── book_detail.html    # Book profile & circulation history
│   │   └── book_confirm_delete.html
│   ├── categories/
│   │   ├── category_list.html  # Categories grid
│   │   ├── category_form.html  # Create / Edit category
│   │   └── category_confirm_delete.html
│   ├── members/
│   │   ├── member_list.html    # Member directory
│   │   ├── member_form.html    # Register / Edit member
│   │   ├── member_detail.html  # Member card & loan history
│   │   └── member_confirm_delete.html
│   └── borrows/
│       ├── borrow_list.html    # Loan tracking & overdue filter
│       ├── borrow_form.html    # Issue book form
│       ├── borrow_return.html  # Check-in return & fine form
│       └── borrow_detail.html  # Transaction details
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

---
*Developed by Group 2: Maxamed Abiib, Nimco, Subeer, Muxiyadiin, Najma, Khadar.*
