# judge/judge_core.py
from .languages import LANGS
from .docker_runner import run_in_sandbox
import re

def _normalize(s: str) -> str:
    # Trim trailing spaces, normalize newlines, collapse trailing newline
    lines = [re.sub(r'[ \t]+$', '', ln) for ln in s.replace('\r\n','\n').split('\n')]
    s2 = '\n'.join(lines).strip('\n')
    return s2

def judge_submission(language: str, source: str, tests, time_limit_ms: int, memory_limit_mb: int):
    if language not in LANGS:
        return {"verdict":"SE", "message":f"Unsupported language: {language}"}

    spec = LANGS[language]
    total_time = 0
    peak_mem = 0

    # compile once by running an empty input (compile step happens inside runner)
    # compile errors are returned on first run; to avoid recompiling for each test,
    # you can refactor docker_runner to compile once and reuse a container. This is
    # simple & reliable for now.

    for idx, t in enumerate(tests, 1):
        res = run_in_sandbox(spec, source, t.input_data, time_limit_ms, memory_limit_mb)
        if res.status == "CE":
            return {"verdict":"CE", "message":res.stderr[:8000]}
        if res.status == "TLE":
            return {"verdict":"TLE", "message":f"Test #{idx} exceeded time limit"}
        if res.status == "SE":
            return {"verdict":"SE", "message":res.stderr[:8000]}
        if res.status == "RE":
            return {"verdict":"RTE", "message":f"Test #{idx} runtime error:\n{res.stderr[:2000]}"}

        exp = _normalize(t.output_data)
        got = _normalize(res.stdout)
        total_time += res.time_ms
        peak_mem = max(peak_mem, res.memory_kb)

        if exp != got:
            # Helpful diff
            return {
                "verdict":"WA",
                "message":f"Wrong Answer on test #{idx}\nExpected:\n{exp}\nGot:\n{got}"
            }

    return {
        "verdict":"AC",
        "time_ms":total_time,
        "memory_kb":peak_mem,
        "message":"Accepted"
    }
