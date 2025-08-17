import os, subprocess, uuid, shutil

RUNNER_IMAGE = os.environ.get("OJ_RUNNER_IMAGE", "oj-runner")

def _win_abspath(p: str) -> str:
    # Docker on Windows accepts plain absolute paths; ensure normalized
    return os.path.abspath(p)

def run_in_container(mount_dir, cmd, stdin="", timeout=2.0, memory="256m", cpus="1.0"):
    """
    Run a command inside an ephemeral container with /sandbox mounted.
    Returns (exit_code, stdout, stderr).
    """
    mount_dir = _win_abspath(mount_dir)
    name = f"oj-{uuid.uuid4().hex[:12]}"
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", name,
        "--network", "none",
        "-m", memory,
        "--cpus", str(cpus),
        "-v", f"{mount_dir}:/sandbox",
        "-w", "/sandbox",
        RUNNER_IMAGE,
        *cmd
    ]
    try:
        completed = subprocess.run(
            docker_cmd,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as e:
        # Kill the container just in case
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return 124, (e.stdout or ""), (e.stderr or "Time limit exceeded")
