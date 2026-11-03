import sys
import time
from collections import defaultdict

from evals.cases import CASES
from minigit import llm


def norm(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rows = []
    by_level = defaultdict(lambda: [0, 0])

    for case in CASES:
        accepted = {norm(a) for a in case["accept"]}
        passed = attempted = 0
        for _ in range(runs):
            try:
                out = llm.suggest_resolution(
                    case["name"],
                    case["base"].encode(),
                    case["ours"].encode(),
                    case["theirs"].encode(),
                )
            except RuntimeError as e:
                print(f"  {case['name']}: error: {e}")
                continue
            attempted += 1
            if norm(out) in accepted:
                passed += 1
            time.sleep(1)
        rows.append((case["name"], case["level"], passed, attempted))
        by_level[case["level"]][0] += passed
        by_level[case["level"]][1] += attempted

    lines = ["| Case | Level | Correct |", "| --- | --- | --- |"]
    for name, level, passed, attempted in rows:
        lines.append(f"| {name} | {level} | {passed}/{attempted} |")
    lines += ["", "| Level | Correct |", "| --- | --- |"]
    total_p = total_a = 0
    for level in ("easy", "medium", "hard"):
        p, a = by_level[level]
        total_p, total_a = total_p + p, total_a + a
        lines.append(f"| {level} | {p}/{a} |")
    lines.append(f"| **all** | **{total_p}/{total_a}** |")

    report = "\n".join(lines)
    print("\n" + report)
    with open("evals/results.md", "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()