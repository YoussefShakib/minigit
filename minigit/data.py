import hashlib
import os

GIT_DIR = ".minigit"


def init():
    os.makedirs(os.path.join(GIT_DIR, "objects"), exist_ok=True)


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
            if entry.name in (GIT_DIR, ".venv", ".git", "__pycache__"):
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