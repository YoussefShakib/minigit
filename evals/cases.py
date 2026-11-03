CASES = [
    # ---- easy: edits on different lines, keep both ----
    {
        "name": "config.ini",
        "level": "easy",
        "base": "name = app\nport = 8000\ndebug = false\n",
        "ours": "name = app\nport = 9000\ndebug = false\n",
        "theirs": "name = app\nport = 8000\ndebug = true\n",
        "accept": ["name = app\nport = 9000\ndebug = true\n"],
    },
    {
        "name": "greet.py",
        "level": "easy",
        "base": "def greet():\n    print('hi')\n\n\ndef bye():\n    print('bye')\n",
        "ours": "def greet():\n    print('hello')\n\n\ndef bye():\n    print('bye')\n",
        "theirs": "def greet():\n    print('hi')\n\n\ndef bye():\n    print('goodbye')\n",
        "accept": [
            "def greet():\n    print('hello')\n\n\ndef bye():\n    print('goodbye')\n"
        ],
    },
    {
        "name": "fruit.txt",
        "level": "easy",
        "base": "apple\nbanana\ncherry\n",
        "ours": "apple\nbanana\ncherry\ndate\n",
        "theirs": "avocado\napple\nbanana\ncherry\n",
        "accept": ["avocado\napple\nbanana\ncherry\ndate\n"],
    },
    # ---- medium: same lines, changes that are compatible ----
    {
        "name": "total.py",
        "level": "medium",
        "base": "total = price * qty\nprint(total)\n",
        "ours": "amount = price * qty\nprint(amount)\n",
        "theirs": "total = price * qty * 1.14\nprint(total)\n",
        "accept": ["amount = price * qty * 1.14\nprint(amount)\n"],
    },
    {
        "name": "add.py",
        "level": "medium",
        "base": "def add(a, b):\n    return a + b\n",
        "ours": "def add(a: int, b: int) -> int:\n    return a + b\n",
        "theirs": 'def add(a, b):\n    """Add two numbers."""\n    return a + b\n',
        "accept": [
            'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'
        ],
    },
    {
        "name": "settings.py",
        "level": "medium",
        "base": "TIMEOUT = 30\nRETRIES = 3\n",
        "ours": "TIMEOUT = 60\nRETRIES = 3\n",
        "theirs": "TIMEOUT = 30  # seconds\nRETRIES = 3\n",
        "accept": ["TIMEOUT = 60  # seconds\nRETRIES = 3\n"],
    },
    {
        "name": "imports.py",
        "level": "medium",
        "base": "import os\n\nprint(os.getcwd())\n",
        "ours": "import os\nimport sys\n\nprint(os.getcwd())\n",
        "theirs": "import os\nimport json\n\nprint(os.getcwd())\n",
        "accept": [
            "import os\nimport sys\nimport json\n\nprint(os.getcwd())\n",
            "import os\nimport json\nimport sys\n\nprint(os.getcwd())\n",
        ],
    },
    # ---- hard: needs reasoning, or the sides truly contradict ----
    {
        "name": "adult.py",
        "level": "hard",
        "base": "def is_adult(age):\n    return age >= 18\n",
        "ours": "def is_adult(age):\n    return age >= 21\n",
        "theirs": (
            "def is_adult(age):\n    if age < 0:\n"
            "        raise ValueError('bad age')\n    return age >= 18\n"
        ),
        "accept": [
            (
                "def is_adult(age):\n    if age < 0:\n"
                "        raise ValueError('bad age')\n    return age >= 21\n"
            )
        ],
    },
    {
        "name": "old.py",
        "level": "hard",
        "base": "def old():\n    return 1\n\n\ndef keep():\n    return 2\n",
        "ours": "def keep():\n    return 2\n",
        "theirs": "def old():\n    return 10\n\n\ndef keep():\n    return 2\n",
        # genuine contradiction: either side is a defensible answer
        "accept": [
            "def keep():\n    return 2\n",
            "def old():\n    return 10\n\n\ndef keep():\n    return 2\n",
        ],
    },
    {
        "name": "version.py",
        "level": "hard",
        "base": "version = '1.0'\nname = 'tool'\n",
        "ours": "version = '1.1'\nname = 'tool'\n",
        "theirs": "version = '1.2'\nname = 'tool'\n",
        # genuine contradiction: either side is a defensible answer
        "accept": [
            "version = '1.1'\nname = 'tool'\n",
            "version = '1.2'\nname = 'tool'\n",
        ],
    },
]