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

    sub.add_parser("log")

    p = sub.add_parser("checkout")
    p.add_argument("oid")

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
        oid = data.get_HEAD()
        while oid:
            c = data.get_commit(oid)
            print(f"commit {oid}\n\n    {c.message}\n")
            oid = c.parent
    elif args.command == "checkout":
        c = data.get_commit(args.oid)
        data.read_tree(c.tree)
        data.set_HEAD(args.oid)