import hashlib
import os
from collections import namedtuple

GIT_DIR = ".minigit"
IGNORED = {GIT_DIR, ".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache"}


def init():
    os.makedirs(os.path.join(GIT_DIR, "objects"), exist_ok=True)
    set_HEAD("main", symbolic=True)


def hash_object(data: bytes, type_: str = "blob") -> str:
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    with open(os.path.join(GIT_DIR, "objects", oid), "wb") as f:
        f.write(obj)
    return oid


def get_object(oid: str, expected: str | None = "blob") -> bytes:
    with open(os.path.join(GIT_DIR, "objects", oid), "rb") as f:
        obj = f.read()
    type_, _, content = obj.partition(b"\x00")
    if expected is not None and type_.decode() != expected:
        raise ValueError(f"expected {expected}, got {type_.decode()}")
    return content


def write_tree(directory: str = ".") -> str:
    entries = []
    with os.scandir(directory) as it:
        for entry in sorted(it, key=lambda e: e.name):
            if entry.name in IGNORED:
                continue
            path = os.path.join(directory, entry.name)
            if entry.is_file(follow_symlinks=False):
                with open(path, "rb") as f:
                    oid = hash_object(f.read(), "blob")
                entries.append(("blob", oid, entry.name))
            elif entry.is_dir(follow_symlinks=False):
                oid = write_tree(path)
                entries.append(("tree", oid, entry.name))
    tree = "".join(f"{t} {o} {n}\n" for t, o, n in entries).encode()
    return hash_object(tree, "tree")


# ---- refs, HEAD, branches, tags ----


def set_HEAD(value: str, symbolic: bool = False) -> None:
    text = f"ref: refs/heads/{value}" if symbolic else value
    with open(os.path.join(GIT_DIR, "HEAD"), "w") as f:
        f.write(text)


def _read_HEAD() -> str | None:
    path = os.path.join(GIT_DIR, "HEAD")
    if os.path.isfile(path):
        with open(path) as f:
            return f.read().strip()
    return None


def current_branch() -> str | None:
    head = _read_HEAD()
    if head and head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/"):]
    return None


def get_ref(path: str) -> str | None:
    full = os.path.join(GIT_DIR, path)
    if os.path.isfile(full):
        with open(full) as f:
            return f.read().strip()
    return None


def set_ref(path: str, oid: str) -> None:
    full = os.path.join(GIT_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(oid)


def get_HEAD() -> str | None:
    branch = current_branch()
    if branch:
        return get_ref(f"refs/heads/{branch}")
    return _read_HEAD()


def move_HEAD(oid: str) -> None:
    branch = current_branch()
    if branch:
        set_ref(f"refs/heads/{branch}", oid)
    else:
        set_HEAD(oid)


def resolve(name: str) -> str:
    if name == "HEAD":
        return get_HEAD()
    for prefix in ("", "refs/tags/", "refs/heads/"):
        oid = get_ref(prefix + name)
        if oid:
            return oid
    return name


def create_tag(name: str, oid: str) -> None:
    set_ref(f"refs/tags/{name}", oid)


def create_branch(name: str, oid: str) -> None:
    set_ref(f"refs/heads/{name}", oid)


def list_branches() -> list[str]:
    path = os.path.join(GIT_DIR, "refs", "heads")
    return sorted(os.listdir(path)) if os.path.isdir(path) else []


# ---- commits ----

Commit = namedtuple("Commit", ["tree", "parent", "message"])


def commit(message: str) -> str:
    text = f"tree {write_tree()}\n"
    head = get_HEAD()
    if head:
        text += f"parent {head}\n"
    text += f"\n{message}\n"
    oid = hash_object(text.encode(), "commit")
    move_HEAD(oid)
    return oid


def get_commit(oid: str) -> Commit:
    raw = get_object(oid, "commit").decode()
    header, _, message = raw.partition("\n\n")
    tree = parent = None
    for line in header.splitlines():
        key, _, value = line.partition(" ")
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
    return Commit(tree, parent, message.strip())


# ---- reading trees back / checkout ----


def _tree_entries(oid: str):
    text = get_object(oid, "tree").decode()
    for line in text.splitlines():
        type_, entry_oid, name = line.split(" ", 2)
        yield type_, entry_oid, name


def get_tree(oid: str, base: str = "") -> dict[str, str]:
    result = {}
    for type_, entry_oid, name in _tree_entries(oid):
        path = base + name
        if type_ == "blob":
            result[path] = entry_oid
        else:
            result.update(get_tree(entry_oid, path + "/"))
    return result


def _empty_directory(directory: str = ".") -> None:
    with os.scandir(directory) as it:
        entries = list(it)
    for e in entries:
        if e.name in IGNORED:
            continue
        if e.is_dir(follow_symlinks=False):
            _empty_directory(e.path)
            try:
                os.rmdir(e.path)
            except OSError:
                pass
        else:
            os.remove(e.path)


def read_tree(tree_oid: str) -> None:
    _empty_directory()
    for path, oid in get_tree(tree_oid).items():
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(get_object(oid))