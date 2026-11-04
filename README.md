# minigit

A Git clone in Python, built from scratch to learn how Git works internally,
with an optional LLM that suggests resolutions for merge conflicts.

## What it does

- Content-addressed object store (blobs, trees, commits) using SHA-1
- `init`, `hash-object`, `cat-file`, `write-tree`, `commit`, `log`, `checkout`
- Branches and tags as named pointers to commits, and a symbolic `HEAD`
- Three-way `merge` with fast-forward and conflict markers
- `merge --suggest`: sends the base, ours and theirs versions of each
  conflicted file to an LLM and prints a proposed resolution. It is never
  applied automatically.

## Run it

```
git clone https://github.com/YoussefShakib/minigit
cd minigit
python -m minigit init
echo "hello" > a.txt
python -m minigit commit -m "first"
python -m minigit log
```

Requires Python 3.10 or newer and has no runtime dependencies.

For `--suggest`, set `MINIGIT_API_KEY`, `MINIGIT_MODEL` and `MINIGIT_BASE_URL`
(any OpenAI-compatible endpoint).

## How it works

Every object is stored under the SHA-1 of its content, so identical content is
stored once and any change produces a new ID. A tree lists `type hash name`
for each entry. A commit points to one tree and one parent. Branches and tags
are files containing a commit hash, and `HEAD` points to the current branch.

Merge finds the common ancestor by walking parent chains, then compares the
base, ours and theirs versions of each file. If only one side changed a file,
that side wins. If both changed it differently, the file gets conflict markers.

## LLM conflict suggestions

Idea taken from: [Can Pre-trained Language Models be Used to Resolve Textual
and Semantic Merge Conflicts?](https://arxiv.org/abs/2111.11904) (Zhang et al.,
2021), which prompts a language model with conflict context and compares it to
a heuristic baseline.

Evaluation: 16 hand-written conflicts (easy, medium, hard, harder), each run
3 times with `gemini-3.5-flash-lite` at temperature 0. A suggestion counts as
correct only if it matches an accepted answer after trimming trailing
whitespace.

| Level | Correct |
| --- | --- |
| easy | 9/9 |
| medium | 12/12 |
| hard | 9/9 |
| harder | 18/18 |
| **LLM, all cases** | **48/48** |
| Baseline: always take "ours" | 3/16 |

Read this carefully:

- Temperature 0 makes repeated runs nearly identical, so the effective sample
  is 16 cases, not 48.
- Three cases are genuine contradictions where either side is accepted.
- Published benchmarks on real repositories report much lower rates: the best
  models resolve under 60% of real conflicts
  ([Merge-Bench](https://arxiv.org/abs/2605.25890)). My 16 short, hand-written
  cases are far easier than that.
- This shows the pipeline works. It does not show how the model performs on
  real repositories.

## Limitations

- Merge works per file, not per line, so two edits to different lines of the
  same file conflict.
- The merge commit has one parent, so a later merge can pick the wrong base.
- Small hand-written evaluation set and a single model.
- Suggestions can be wrong, which is why they are printed and never applied.
- Suggestions are not validated. A next step is a deterministic check (no
  leftover conflict markers, the file parses) before showing a suggestion, as
  in [this study](https://arxiv.org/abs/2607.27674).

## Tests

```
pip install pytest ruff
ruff check . && pytest
python -m evals.run_eval 3   # calls the LLM, needs an API key
```

CI runs `ruff` and `pytest` on every push. It never calls the LLM.