# judge/languages.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LangSpec:
    image: str
    filename: str
    compile_cmd: Optional[List[str]]
    run_cmd: List[str]

LANGS = {
    "cpp17": LangSpec(
        image="gcc:13.2",                    # has g++
        filename="main.cpp",
        compile_cmd=["bash", "-lc", "g++ -std=gnu++17 -O2 -pipe -static -s -o main main.cpp"],
        run_cmd=["bash", "-lc", "./main"]
    ),
    "c": LangSpec(
        image="gcc:13.2",
        filename="main.c",
        compile_cmd=["bash", "-lc", "gcc -std=gnu11 -O2 -pipe -static -s -o main main.c"],
        run_cmd=["bash", "-lc", "./main"]
    ),
    "py3": LangSpec(
        image="python:3.11-slim",
        filename="main.py",
        compile_cmd=None,
        run_cmd=["python3", "main.py"]
    ),
    "java": LangSpec(
        image="eclipse-temurin:17-jdk",
        filename="Main.java",
        compile_cmd=["bash", "-lc", "javac -encoding UTF-8 Main.java"],
        run_cmd=["bash", "-lc", "java -Xss256m -Xms64m -Xmx256m Main"]
    ),
}
