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