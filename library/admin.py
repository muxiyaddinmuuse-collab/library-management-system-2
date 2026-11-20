from django.contrib import admin
from .models import Category, Book, Member, BorrowRecord


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'location_shelf')
    list_filter = ('category', 'publication_year')
    search_fields = ('title', 'author', 'isbn')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'full_name', 'email', 'phone', 'membership_type', 'status', 'registered_date')
    list_filter = ('membership_type', 'status')
    search_fields = ('member_id', 'first_name', 'last_name', 'email', 'phone')


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'issue_date', 'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('book__title', 'member__first_name', 'member__last_name', 'member__member_id')
