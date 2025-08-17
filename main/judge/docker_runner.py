# judge/docker_runner.py
import os, tempfile, subprocess, json, shlex, textwrap, uuid

class RunResult:
    def __init__(self, status, stdout, stderr, time_ms, memory_kb, exit_code):
        self.status = status          # "OK" | "CE" | "RE" | "TLE" | "MLE" | "SE"
        self.stdout = stdout
        self.stderr = stderr
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.exit_code = exit_code

def _docker_base_cmd(image, workdir, mem_mb, cpu=1.0):
    return [
        "docker","run","--rm",
        "--network","none",
        "--cpus", str(cpu),
        "--pids-limit","256",
        "--memory", f"{mem_mb}m",
        "--memory-swap", f"{mem_mb}m",
        "--ulimit","stack=67108864:67108864",
        "--read-only",
        "--tmpfs","/tmp:rw,exec,nosuid,size=64m",
        "-v", f"{workdir}:/sandbox",
        "-w","/sandbox",
        image
    ]

def run_in_sandbox(spec, source_code:str, stdin:str, time_limit_ms:int, mem_limit_mb:int):
    # temp workspace
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, spec.filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        # 1) compile if needed
        if spec.compile_cmd:
            compile_cmd = _docker_base_cmd(spec.image, tmp, mem_limit_mb) + spec.compile_cmd
            c = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=max(10, time_limit_ms/1000+5))
            if c.returncode != 0:
                return RunResult("CE", c.stdout, c.stderr, 0, 0, c.returncode)

        # 2) run
        # use timeout inside container + docker kill-switch from host
        runtime = _docker_base_cmd(spec.image, tmp, mem_limit_mb) + spec.run_cmd
        try:
            p = subprocess.run(
                runtime,
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=max(1, time_limit_ms/1000 + 1),
            )
            status = "OK" if p.returncode == 0 else "RE"
            return RunResult(status, p.stdout, p.stderr, time_limit_ms, mem_limit_mb*1024, p.returncode)
        except subprocess.TimeoutExpired as e:
            # container timed out → TLE
            return RunResult("TLE", e.stdout or "", e.stderr or "Time limit exceeded", time_limit_ms, mem_limit_mb*1024, -1)
        except Exception as e:
            return RunResult("SE", "", str(e), 0, 0, -1)
