import os, tempfile, shutil
from celery import shared_task
from .languages import LANGS
from .docker_runner import run_in_container
from .models import Submission

@shared_task
def _write_source(tmpdir, filename, code):
    path = os.path.join(tmpdir, filename)
    # force LF newlines to avoid odd compiler behavior
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(code)
    return path

@shared_task
def compile_and_run(lang, source_code, input_data="", limits=None):
    """
    Compile (if needed) and run a single program with given stdin.
    limits = {"time": 2.0, "compile_time": 8.0, "memory": "256m", "cpus":"1.0"}
    """
    limits = limits or {}
    conf = LANGS.get(lang)
    if not conf:
        return {"ok": False, "stage": "init", "error": f"Unsupported language: {lang}"}

    tmpdir = tempfile.mkdtemp(prefix="oj_")
    try:
        _ = _write_source(tmpdir, conf["source"], source_code)

        # compile
        if conf["compile"]:
            rc, out, err = run_in_container(
                tmpdir,
                conf["compile"],
                timeout=float(limits.get("compile_time", 8.0)),
                memory=limits.get("memory", "256m"),
                cpus=str(limits.get("cpus", "1.0")),
            )
            if rc != 0:
                return {"ok": False, "stage": "compile", "exit_code": rc, "stdout": out, "stderr": err}

        # run
        rc, out, err = run_in_container(
            tmpdir,
            conf["run"],
            stdin=input_data or "",
            timeout=float(limits.get("time", 2.0)),
            memory=limits.get("memory", "256m"),
            cpus=str(limits.get("cpus", "1.0")),
        )

        return {
            "ok": rc == 0,
            "stage": "run",
            "exit_code": rc,
            "stdout": out,
            "stderr": err,
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

@shared_task
def judge_solution(submission_id, lang, source_code, tests, limits=None):
    """
    Run all testcases and update the Submission row.
    """
    submission = Submission.objects.get(id=submission_id)
    verdict = "AC"
    total_score = len(tests)
    passed = 0
    runtime = 0.0

    tmpdir = tempfile.mkdtemp(prefix="oj_")
    try:
        conf = LANGS[lang]
        _ = _write_source(tmpdir, conf["source"], source_code)

        # compile once
        if conf["compile"]:
            rc, out, err = run_in_container(
                tmpdir, conf["compile"],
                timeout=float((limits or {}).get("compile_time", 8.0)),
                memory=(limits or {}).get("memory", "256m"),
                cpus=str((limits or {}).get("cpus", "1.0")),
            )
            if rc != 0:
                submission.verdict = "CE"
                submission.save()
                return {"verdict": "CE", "stderr": err}

        # run all tests
        for idx, t in enumerate(tests, start=1):
            rc, out, err = run_in_container(
                tmpdir, conf["run"],
                stdin=t.get("in", ""),
                timeout=float((limits or {}).get("time", 2.0)),
                memory=(limits or {}).get("memory", "256m"),
                cpus=str((limits or {}).get("cpus", "1.0")),
            )

            if rc == 124:
                verdict = "TLE"
                break
            if rc != 0:
                verdict = "RE"
                break
            if out.strip() != t.get("out", "").strip():
                verdict = "WA"
                break

            passed += 1

        # final update
        if verdict == "AC" and passed == total_score:
            verdict = "AC"
        elif verdict == "AC":  # some tests passed but not all
            verdict = "Partial"

        submission.verdict = verdict
        submission.score = passed
        submission.total_score = total_score
        submission.runtime = runtime
        submission.save()

        return {"verdict": verdict, "passed": passed, "total": total_score}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
