import subprocess, tempfile, time, os, re

def run_code(language, code, input_data):
    file_ext = get_file_extension(language)

    # For Java, match file name to public class name
    if language == "java":
        match = re.search(r'public\s+class\s+(\w+)', code)
        if not match:
            return {"output": "", "error": "No public class found", "runtime": 0}
        class_name = match.group(1)
        file_path = os.path.join(tempfile.gettempdir(), f"{class_name}.java")
    else:
        file_path = tempfile.mktemp(suffix=file_ext)

    # Save code
    with open(file_path, "w") as f:
        f.write(code)

    container_path = f"/sandbox/{os.path.basename(file_path)}"

    # Commands for each language
    if language == "python":
        cmd = [
            "docker", "run", "--rm",
            "-i",  # keep stdin open
            "-v", f"{file_path}:{container_path}",
            "oj-sandbox",
            "python3", container_path
        ]
    elif language == "cpp":
        cmd = [
            "docker", "run", "--rm",
            "-i",
            "-v", f"{file_path}:{container_path}",
            "oj-sandbox",
            "bash", "-c",
            f"g++ {container_path} -o /sandbox/a.out && /sandbox/a.out"
        ]
    elif language == "java":
        cmd = [
            "docker", "run", "--rm",
            "-i",
            "-v", f"{file_path}:{container_path}",
            "oj-sandbox",
            "bash", "-c",
            f"javac {container_path} && java -cp /sandbox {os.path.splitext(os.path.basename(file_path))[0]}"
        ]
    elif language == "javascript":
        cmd = [
            "docker", "run", "--rm",
            "-i",
            "-v", f"{file_path}:{container_path}",
            "oj-sandbox",
            "node", container_path
        ]
    else:
        return {"output": "", "error": "Language not supported", "runtime": 0}

    # Run inside Docker with input_data via stdin
    start_time = time.time()
    process = subprocess.run(
        cmd,
        input=input_data.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10
    )
    end_time = time.time()

    return {
        "output": process.stdout.decode(),
        "error": process.stderr.decode(),
        "runtime": end_time - start_time
    }

def get_file_extension(language):
    return {
        "python": ".py",
        "cpp": ".cpp",
        "java": ".java",
        "javascript": ".js"
    }.get(language, "")
