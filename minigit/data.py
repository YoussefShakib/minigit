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

# ---- merge ----


def merge_base(a: str, b: str) -> str | None:
    ancestors = set()
    oid = a
    while oid:
        ancestors.add(oid)
        oid = get_commit(oid).parent
    oid = b
    while oid:
        if oid in ancestors:
            return oid
        oid = get_commit(oid).parent
    return None


def _blob(oid: str | None) -> bytes | None:
    return get_object(oid) if oid else None


def merge_contents(
    base: bytes | None, ours: bytes | None, theirs: bytes | None
) -> tuple[bytes | None, bool]:
    if ours == theirs:
        return ours, False
    if base == ours:
        return theirs, False
    if base == theirs:
        return ours, False
    ours_text = ours or b""
    theirs_text = theirs or b""
    if ours_text and not ours_text.endswith(b"\n"):
        ours_text += b"\n"
    if theirs_text and not theirs_text.endswith(b"\n"):
        theirs_text += b"\n"
    merged = (
        b"<<<<<<< ours\n" + ours_text + b"=======\n" + theirs_text + b">>>>>>> theirs\n"
    )
    return merged, True


def merge(other_oid: str, on_conflict=None) -> list[str]:
    head = get_HEAD()
    base = merge_base(head, other_oid)

    if base == other_oid:
        return []  # already up to date

    if base == head:  # fast-forward
        read_tree(get_commit(other_oid).tree)
        move_HEAD(other_oid)
        return []

    base_tree = get_tree(get_commit(base).tree) if base else {}
    our_tree = get_tree(get_commit(head).tree)
    their_tree = get_tree(get_commit(other_oid).tree)

    result = {}
    conflicts = []
    for path in sorted(set(base_tree) | set(our_tree) | set(their_tree)):
        base_blob = _blob(base_tree.get(path))
        our_blob = _blob(our_tree.get(path))
        their_blob = _blob(their_tree.get(path))
        content, conflict = merge_contents(base_blob, our_blob, their_blob)
        if conflict:
            conflicts.append(path)
            if on_conflict:
                on_conflict(path, base_blob, our_blob, their_blob)
        if content is not None:
            result[path] = content

    _empty_directory()
    for path, content in result.items():
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
    return conflicts