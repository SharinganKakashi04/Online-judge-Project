LANGS = {
    "cpp": {
        "source": "Main.cpp",
        "compile": ["bash", "-lc", "g++ -O2 -std=c++17 -pipe -static -s Main.cpp -o Main"],
        "run": ["bash", "-lc", "./Main"],
    },
    "c": {
        "source": "main.c",
        "compile": ["bash", "-lc", "gcc -O2 -std=c17 -pipe -static -s main.c -o main"],
        "run": ["bash", "-lc", "./main"],
    },
    "python": {
        "source": "main.py",
        "compile": None,
        "run": ["python3", "main.py"],
    },
    "java": {
        "source": "Main.java",
        "compile": ["bash", "-lc", "javac Main.java"],
        "run": ["bash", "-lc", "java Main"],
    },
}
