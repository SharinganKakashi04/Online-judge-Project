# judge/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Problem, Submission
from .tasks import run_judging
from django.http import JsonResponse
from judge.tasks import compile_and_run
from celery.result import AsyncResult
from django.views.decorators.http import require_GET
from django.conf import settings

@require_POST
def submit_code(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    language = request.POST.get("language")      # "cpp17", "py3", etc.
    source = request.POST.get("source", "")

    sub = Submission.objects.create(problem=problem, language=language, source=source, verdict="Queued")
    run_judging.delay(sub.id)
    return JsonResponse({"submission_id": sub.id, "status": "Queued"})

def get_submission(request, sid):
    sub = get_object_or_404(Submission, pk=sid)
    return JsonResponse({
        "id": sub.id,
        "verdict": sub.verdict,
        "time_ms": sub.time_ms,
        "memory_kb": sub.memory_kb,
        "message": sub.message
    })

def submit(request):
    if request.method == "POST":
        language = request.POST.get("language")  # "cpp", "py", "java", "js", "c"
        source = request.POST.get("source_code", "")
        stdin_data = request.POST.get("stdin", "")

        # Optional: per-problem limits
        limits = {
            "time": 2.0,    # seconds
            "memory": "256m",
            "cpus": "1.0",
            "pids": 64,
        }

        async_res = compile_and_run.delay(language, source, stdin_data, limits)
        return JsonResponse({"task_id": async_res.id})
    return JsonResponse({"error": "POST only"}, status=405)

@require_GET
def result(request):
    task_id = request.GET.get("task_id")
    if not task_id:
        return JsonResponse({"error": "missing task_id"}, status=400)
    res = AsyncResult(task_id)
    if not res.ready():
        return JsonResponse({"state": res.state})
    return JsonResponse(res.result)