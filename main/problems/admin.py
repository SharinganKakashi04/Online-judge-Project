from django.contrib import admin
from .models import Problem, TestCase

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 2
    fields = ['input_data', 'expected_output', 'is_sample', 'points']

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty']  # Remove 'created_at'
    list_filter = ['difficulty']
    search_fields = ['title', 'description']

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['problem', 'is_sample', 'points']
    list_filter = ['is_sample', 'problem']