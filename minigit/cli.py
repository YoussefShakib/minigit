import argparse
import sys

from minigit import data, llm


def main():
    parser = argparse.ArgumentParser(prog="minigit")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    p = sub.add_parser("hash-object")
    p.add_argument("file")

    p = sub.add_parser("cat-file")
    p.add_argument("oid")

    sub.add_parser("write-tree")

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

    p = sub.add_parser("merge")
    p.add_argument("other")
    p.add_argument("--suggest", action="store_true")

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
    elif args.command == "write-tree":
        print(data.write_tree())
    elif args.command == "commit":
        print(data.commit(args.message))
    elif args.command == "log":
        oid = data.resolve(args.oid)
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
    elif args.command == "merge":
        suggestions = {}

        def collect(path, base, ours, theirs):
            if not args.suggest:
                return
            try:
                suggestions[path] = llm.suggest_resolution(path, base, ours, theirs)
            except RuntimeError as e:
                print(f"No suggestion for {path}: {e}")

        conflicts = data.merge(data.resolve(args.other), on_conflict=collect)
        if conflicts:
            print("Merge finished with conflicts in:")
            for path in conflicts:
                print(f"  {path}")
            for path, text in suggestions.items():
                print(f"\n--- Suggested resolution for {path} (not applied) ---")
                print(text)
            print("Fix the files, then run: minigit commit -m 'Merge'")
        else:
            print("Merged cleanly. Run: minigit commit -m 'Merge'")


if __name__ == "__main__":
    main()