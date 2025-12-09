from pathlib import Path
import os

def find_child(target, cur=os.getcwd()):
    cur_path = Path(cur)

    children = os.listdir(cur_path)

    if not children:
        return False
        
    for child in children:
        if child == target:
            return str(cur_path / child)
        else:
            if os.path.isdir(cur_path / child):
                return find_child(target, str(cur_path / child))
            else:
                return False

def get_parent(target, cur=os.getcwd()):
    cur_path = Path(cur)

    while cur_path != cur_path.root:
        if (cur_path / target).exists():
            return str(cur_path)
        else:
            cur_path = cur_path.parent
    else:
        raise Exception(f"Not correct target[{target}]")
