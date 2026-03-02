import sys
from pathlib import Path
import zlib


def get_branch_names(path: str):
    branch_names = []
    heads_dir = Path(path) / ".git" / "refs" / "heads"
    for object in heads_dir.iterdir():
        branch_names.append(object.name)
    return "\n".join(branch_names)


def get_last_commit(path: str, branch_name: str):
    with open(f"{path}/.git/refs/heads/{branch_name}", "r") as f:
        branch_hash = f.read().strip()

    commit_path = f"{path}/.git/objects/{branch_hash[:2]}/{branch_hash[2:]}"
    with open(commit_path, "rb") as f:
        commit_object = zlib.decompress(f.read())
    _, _, body = commit_object.partition(b'\x00')
    return body.decode()

def show_tree_object(path: str, branch_name: str):
    last_commit = get_last_commit(path, branch_name).split('\n')
    for line in last_commit:
        if line.startswith("tree"):
            tree_hash = line.split()[1]
            break
    
    tree_path = f"{path}/.git/objects/{tree_hash[:2]}/{tree_hash[2:]}"
    with open(tree_path, "rb") as f:
        tree_object = zlib.decompress(f.read())
    _, _, tree_body = tree_object.partition(b'\x00')

    remaining = tree_body
    while remaining:
        state_and_name, _, new_body = remaining.partition(b'\x00')
        state, name = state_and_name.decode().split()
        state = "tree" if state.startswith('4') else "blob"
        hash = new_body[:20].hex()
        print(f"{state} {hash} {name}")
        remaining = new_body[20:]


    


def main():
    path = sys.argv[1]
    if len(sys.argv) < 3:
        print(get_branch_names(path))
    else:
        branch_name = sys.argv[2]
        print(get_last_commit(path, branch_name))
        show_tree_object(path, branch_name)


if __name__ == "__main__":
    main()