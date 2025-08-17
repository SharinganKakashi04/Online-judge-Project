from django.shortcuts import render, get_object_or_404, redirect
from .models import Problem
from submissions.models import Submission

def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems':problems})

def problem_detail(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    if request.method == "POST":
        code = request.POST.get("code")
        Submission.objects.create(
            problem=problem,
            user=request.user,
            code=code,
            language="python",  # later make this dynamic
            verdict="Pending"
        )
        return redirect("submission_list")
    return render(request, "problems/problem_detail.html", {"problem": problem})


