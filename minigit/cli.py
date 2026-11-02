import argparse
import sys

from minigit import data


def main():
    parser = argparse.ArgumentParser(prog="minigit")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    p = sub.add_parser("hash-object")
    p.add_argument("file")

    p = sub.add_parser("cat-file")
    p.add_argument("oid")

    p = sub.add_parser("commit")
    p.add_argument("-m", "--message", required=True)

    p = sub.add_parser("log")
    p.add_argument("oid", nargs="?", default="HEAD")

    p = sub.add_parser("checkout")
    p.add_argument("oid")

    p = sub.add_parser("tag")
    p.add_argument("name")
    p.add_argument("oid", nargs="?", default="HEAD")

    p = sub.add_parser("branch")
    p.add_argument("name", nargs="?")
    p.add_argument("oid", nargs="?", default="HEAD")

    args = parser.parse_args()

    if args.command == "init":
        data.init()
        print("Initialized empty minigit repository in .minigit")
    elif args.command == "hash-object":
        with open(args.file, "rb") as f:
            print(data.hash_object(f.read()))
    elif args.command == "cat-file":
        sys.stdout.flush()
        sys.stdout.buffer.write(data.get_object(args.oid, expected=None))
    elif args.command == "commit":
        print(data.commit(args.message))
    elif args.command == "log":
        oid = data.resolve(args.oid) if hasattr(args, "oid") else data.get_HEAD()
        while oid:
            c = data.get_commit(oid)
            print(f"commit {oid}\n\n    {c.message}\n")
            oid = c.parent
    elif args.command == "checkout":
        branch_oid = data.get_ref(f"refs/heads/{args.oid}")
        oid = data.resolve(args.oid)
        c = data.get_commit(oid)
        data.read_tree(c.tree)
        if branch_oid:
            data.set_HEAD(args.oid, symbolic=True)
        else:
            data.set_HEAD(oid)
    elif args.command == "tag":
        data.create_tag(args.name, data.resolve(args.oid))
    elif args.command == "branch":
        if not args.name:
            current = data.current_branch()
            for b in data.list_branches():
                print(f"{'*' if b == current else ' '} {b}")
        else:
            data.create_branch(args.name, data.resolve(args.oid))