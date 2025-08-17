# judge/models.py
from django.db import models

class Problem(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    time_limit_ms = models.PositiveIntegerField(default=1000)
    memory_limit_mb = models.PositiveIntegerField(default=256)
    # optional: statement, constraints, etc.

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='tests')
    input_data = models.TextField(blank=True, default="")
    output_data = models.TextField()  # expected output
    is_sample = models.BooleanField(default=False)

class Submission(models.Model):
    LANG_CHOICES = [
        ("cpp17", "C++17"),
        ("c", "C11"),
        ("py3", "Python 3"),
        ("java", "Java 17"),
    ]
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='subs')
    language = models.CharField(max_length=10, choices=LANG_CHOICES)
    source = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # results
    verdict = models.CharField(max_length=30, default="Queued")
    time_ms = models.IntegerField(default=0)
    memory_kb = models.IntegerField(default=0)
    message = models.TextField(blank=True, default="")

