from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from problems.models import Problem
from .models import submissions
from compiler.utils import run_code
from django.http import JsonResponse
import json
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .judge import Judge


@login_required
def submissions_list(request):
    # Get filter parameters
    user_filter = request.GET.get('user', '')
    problem_filter = request.GET.get('problem', '')
    language_filter = request.GET.get('language', '')
    verdict_filter = request.GET.get('verdict', '')
    
    # Start with only current user's submissions, ordered by most recent
    submissions_query = submissions.objects.filter(user=request.user).order_by('-submitted_at')
    
    # Apply additional filters if provided
    if problem_filter:
        submissions_query = submissions_query.filter(
            problem__title__icontains=problem_filter
        )
    
    if language_filter:
        submissions_query = submissions_query.filter(language=language_filter)
    
    if verdict_filter:
        submissions_query = submissions_query.filter(verdict=verdict_filter)
    
    # Pagination
    paginator = Paginator(submissions_query, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics for current user only
    total_submissions = submissions.objects.filter(user=request.user).count()
    accepted_submissions = submissions.objects.filter(user=request.user, verdict='Accepted').count()
    acceptance_rate = (accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0
    languages_count = submissions.objects.filter(user=request.user).values('language').distinct().count()
    
    context = {
        'submissions': page_obj,
        'total_submissions': total_submissions,
        'accepted_submissions': accepted_submissions,
        'acceptance_rate': round(acceptance_rate, 1),
        'languages_count': languages_count,
        'problem_filter': problem_filter,
        'language_filter': language_filter,
        'verdict_filter': verdict_filter,
    }
    
    return render(request, 'submissions/submissions_list.html', context)

@login_required
def submit_code(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    
    if request.method == 'POST':
        code = request.POST.get('code', '')
        language = request.POST.get('language', 'python')
        
        # Create submission record
        submission = submissions.objects.create(
            problem=problem,
            user=request.user,
            code=code,
            language=language,
            verdict='Judging'
        )
        
        # Judge the submission
        judge = Judge()
        result = judge.judge_submission(submission)
        
        # Update submission with results
        submission.verdict = result['verdict']
        submission.score = result['score']
        submission.total_score = result['total_score']
        submission.save()
        
        return render(request, 'submissions/results.html', {
            'submission': submission,
            'result': result
        })
    
    return redirect('problems:problem_detail', problem_id=problem_id)

@login_required
def run_code_ajax(request, problem_id):
    if request.method == 'POST':
        try:
            problem = get_object_or_404(Problem, id=problem_id)
            data = json.loads(request.body)
            code = data.get('code', '')
            language = data.get('language', 'python')
            input_data = data.get('input_data', '')
            
            # If no custom input, use sample test case
            if not input_data:
                sample_testcase = problem.testcases.filter(is_sample=True).first()
                if sample_testcase:
                    input_data = sample_testcase.input_data
            
            # Create temporary submission for testing
            temp_submission = submissions(
                problem=problem,
                user=request.user,
                code=code,
                language=language
            )
            
            # Create temporary test case
            from problems.models import TestCase
            temp_testcase = TestCase(
                problem=problem,
                input_data=input_data,
                expected_output="",  # We don't check output for run
                is_sample=False
            )
            
            judge = Judge()
            result = judge.run_test_case(temp_submission, temp_testcase)
            
            return JsonResponse({
                'output': result['output'],
                'runtime': result['runtime'],
                'status': result['status']
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
def run_code_ajax(request, problem_id):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get("code")
        language = data.get("language", "python")
        input_data = data.get("input_data")  # 👈 from AJAX

        problem = get_object_or_404(Problem, id=problem_id)

        if not input_data:  # fallback
            input_data = problem.input_data or ""

        result = run_code(language, code, input_data)
        return JsonResponse(result)
