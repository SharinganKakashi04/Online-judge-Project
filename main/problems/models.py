from django.db import models

class Problem(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    input_format = models.TextField(blank=True, null=True)
    output_format = models.TextField(blank=True, null=True)
    sample_input = models.TextField(blank=True, null=True)
    sample_output = models.TextField(blank=True, null=True)
    difficulty = models.CharField(max_length=20, choices = [("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")])
    input_data = models.TextField(blank =True,help_text = "sample input to be given to the user's code")
    expected_output = models.TextField(blank=True,help_text = "Expected output for the given input")
    def __str__(self):
        return self.title;

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='testcases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)  # True for sample test cases shown to users
    points = models.IntegerField(default=1)  # Points for this test case
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.problem.title} - Test Case {self.id}"
    
    class Meta:
        ordering = ['id']
