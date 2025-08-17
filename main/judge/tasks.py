import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from celery import shared_task

# Adjust images to what you have locally if different.
LANG_IMAGES = {
    "cpp":  {"image": "gcc:13",        "ext": "cpp"},
    "c":    {"image": "gcc:13",        "ext": "c"},
    "py":   {"image": "python:3.11-slim", "ext": "py"},
    "java": {"image": "openjdk:21-slim","ext": "java"},
    "js":   {"image": "node:20-slim",   "ext": "js"},
}

# Hard limits to contain submissions. Tweak as needed.
DEFAULT_LIMITS = {
    "time": 2.0,        # seconds of wall time
    "memory": "256m",   # Docker memory
    "cpus": "1.0",      # Docker CPUs
    "pids": 64,         # process count limit
}

def _docker_run(cmd, cwd, image, limits, network_off=True):
    """
    Runs `cmd` inside a transient container with the given image and resource limits.
    Mounts `cwd` to /work. Returns (exit_code, stdout, stderr).
    """
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{cwd}:/work",
        "-w", "/work",
        "--memory", limits.get("memory", DEFAULT_LIMITS["memory"]),
        "--cpus", limits.get("cpus", DEFAULT_LIMITS["cpus"]),
        "--pids-limit", str(limits.get("pids", DEFAULT_LIMITS["pids"])),
    ]

    if network_off:
        docker_cmd += ["--network", "none"]

    # Optional: prevent file growth attacks
    docker_cmd += ["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"]

    docker_cmd += [image]
    docker_cmd += cmd

    # We do a plain subprocess and capture output.
    # If you want a hard wall-time kill, wrap with `timeout` here or in the image.
    proc = subprocess.Popen(
        docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        stdout, stderr = proc.communicate(timeout=limits.get("time", DEFAULT_LIMITS["time"]))
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        return 124, "", "Time Limit Exceeded"

def _build_and_run(language, code, stdin_data="", limits=None):
    limits = limits or DEFAULT_LIMITS
    if language not in LANG_IMAGES:
        return {"ok": False, "error": f"Unsupported language: {language}"}

    meta = LANG_IMAGES[language]
    image = meta["image"]
    ext = meta["ext"]

    workdir = Path(tempfile.mkdtemp(prefix="oj_"))
    try:
        # Write source file
        src_name = f"Main.{ext}"
        (workdir / src_name).write_text(code, encoding="utf-8")

        # Optional input file
        if stdin_data:
            (workdir / "input.txt").write_text(stdin_data, encoding="utf-8")

        # Build & run per language
        if language in ("c", "cpp"):
            out_bin = "a.out"
            compile_cmd = ["bash", "-lc", f"g++ -O2 -std=c++17 -static -s -o {out_bin} {src_name} 2> compile.err"]
            if language == "c":
                compile_cmd = ["bash", "-lc", f"gcc -O2 -std=c17 -static -s -o {out_bin} {src_name} 2> compile.err"]

            # Compile
            code_c, out_c, err_c = _docker_run(compile_cmd, str(workdir), image, limits)
            # Read compiler diagnostics (from file, stderr might be empty due to redirect)
            compile_err_path = workdir / "compile.err"
            compile_err = compile_err_path.read_text(encoding="utf-8") if compile_err_path.exists() else err_c

            if code_c != 0 or compile_err.strip():
                return {
                    "ok": False,
                    "stage": "compile",
                    "exit_code": code_c,
                    "stderr": compile_err.strip()
                }

            # Run
            run_cmd = ["bash", "-lc", f"./{out_bin} < input.txt 2> run.err || true"] if stdin_data else \
                      ["bash", "-lc", f"./{out_bin} 2> run.err || true"]

            code_r, out_r, err_r = _docker_run(run_cmd, str(workdir), image, limits)
            run_err_path = workdir / "run.err"
            run_err = run_err_path.read_text(encoding="utf-8") if run_err_path.exists() else err_r

            return {
                "ok": True,
                "exit_code": code_r,
                "stdout": out_r,
                "stderr": run_err.strip(),
            }

        if language == "py":
            # No compile; just run
            run_cmd = ["bash", "-lc", f"python -OO {src_name} < input.txt 2> run.err || true"] if stdin_data else \
                      ["bash", "-lc", f"python -OO {src_name} 2> run.err || true"]
            code_r, out_r, err_r = _docker_run(run_cmd, str(workdir), image, limits)
            run_err_path = workdir / "run.err"
            run_err = run_err_path.read_text(encoding="utf-8") if run_err_path.exists() else err_r
            return {"ok": True, "exit_code": code_r, "stdout": out_r, "stderr": run_err.strip()}

        if language == "java":
            # Compile
            compile_cmd = ["bash", "-lc", f"javac {src_name} 2> compile.err"]
            code_c, out_c, err_c = _docker_run(compile_cmd, str(workdir), image, limits)
            compile_err_path = workdir / "compile.err"
            compile_err = compile_err_path.read_text(encoding="utf-8") if compile_err_path.exists() else err_c
            if code_c != 0 or compile_err.strip():
                return {"ok": False, "stage": "compile", "exit_code": code_c, "stderr": compile_err.strip()}
            # Run (Main class)
            run_cmd = ["bash", "-lc", f"java Main < input.txt 2> run.err || true"] if stdin_data else \
                      ["bash", "-lc", f"java Main 2> run.err || true"]
            code_r, out_r, err_r = _docker_run(run_cmd, str(workdir), image, limits)
            run_err_path = workdir / "run.err"
            run_err = run_err_path.read_text(encoding="utf-8") if run_err_path.exists() else err_r
            return {"ok": True, "exit_code": code_r, "stdout": out_r, "stderr": run_err.strip()}

        if language == "js":
            run_cmd = ["bash", "-lc", f"node {src_name} < input.txt 2> run.err || true"] if stdin_data else \
                      ["bash", "-lc", f"node {src_name} 2> run.err || true"]
            code_r, out_r, err_r = _docker_run(run_cmd, str(workdir), image, limits)
            run_err_path = workdir / "run.err"
            run_err = run_err_path.read_text(encoding="utf-8") if run_err_path.exists() else err_r
            return {"ok": True, "exit_code": code_r, "stdout": out_r, "stderr": run_err.strip()}

        return {"ok": False, "error": f"Unhandled language: {language}"}

    finally:
        # Clean working directory
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass


@shared_task(bind=True)
def compile_and_run(self, language, source_code, stdin_data="", limits=None):
    """
    Celery task: compile and run code within a container with resource limits.
    Returns a JSON-ish dict you can store on your Submission model.
    """
    try:
        result = _build_and_run(language, source_code, stdin_data, limits)
        return result
    except Exception as e:
        return {"ok": False, "error": f"internal-error: {e!r}"}
