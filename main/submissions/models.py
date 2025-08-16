from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem

class submissions(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=20)
    verdict = models.CharField(max_length=20, default="Pending")
    score = models.IntegerField(default=0)  # New field
    total_score = models.IntegerField(default=0)  # New field
    runtime = models.FloatField(null=True, blank=True)  # New field
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.problem.title}"