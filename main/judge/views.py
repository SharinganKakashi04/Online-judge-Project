# judge/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from .models import Problem, Submission
from .tasks import compile_and_run, judge_solution
from celery.result import AsyncResult
from judge.models import Submission


# -----------------------------
# 1. Run with custom input (like IDE "Run" button)
# -----------------------------
@require_POST
def run_code(request):
    lang = request.POST.get("language", "cpp")
    code = request.POST.get("source_code", "")
    custom_input = request.POST.get("custom_input", "")

    limits = {"time": 2.0, "memory": "256m"}

    task = compile_and_run.delay(lang, code, custom_input, limits)
    return JsonResponse({"task_id": task.id})


# -----------------------------
# 2. Judge submission with official testcases (like "Submit" button)
# -----------------------------
@require_POST
def submit_code(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    code = request.POST.get("source_code", "")
    lang = request.POST.get("language", "cpp")

    # create submission row
    submission = Submission.objects.create(
        problem=problem,
        user=request.user if request.user.is_authenticated else None,
        code=code,
        language=lang,
        verdict="Pending",
    )

    tests = [
        {"in": t.input_data, "out": t.expected_output}
        for t in problem.testcase_set.all()
    ]

    limits = {"time": 2.0, "memory": "256m"}

    task = judge_solution.delay(submission.id, lang, code, tests, limits)

    return JsonResponse({
        "task_id": task.id,
        "submission_id": submission.id,
    })

# -----------------------------
# 3. Check async task status
@require_GET
def submission_status(request):
    tid = request.GET.get("task_id")
    res = AsyncResult(tid)
    if not res.ready():
        return JsonResponse({"ready": False})
    return JsonResponse({"ready": True, "result": res.result})

# -----------------------------
@require_GET
def task_status(request):
    task_id = request.GET.get("task_id")
    if not task_id:
        return JsonResponse({"error": "missing task_id"}, status=400)

    res = AsyncResult(task_id)
    if not res.ready():
        return JsonResponse({"ready": False, "state": res.state})
    return JsonResponse({"ready": True, "state": res.state, "result": res.result})
