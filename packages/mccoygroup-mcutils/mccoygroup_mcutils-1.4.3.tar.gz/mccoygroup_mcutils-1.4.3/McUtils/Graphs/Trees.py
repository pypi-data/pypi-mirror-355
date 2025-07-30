
import pprint, collections, enum

from .. import Devutils as dev
from .. import Numputils as nput

__all__ = ["TreeWrapper", "tree_traversal"]

class TreeTraversalOrder(enum.Enum):
    BreadthFirst = 'bfs'
    DepthFirst = 'dfs'

def _get_tree_children(tree):
    if hasattr(tree, 'keys'):
        return list(enumerate(tree.keys()))
    else:
        return list(enumerate(tree))
def _get_tree_item(tree, item):
    return tree[item[1]]
def tree_traversal(tree, callback,
                   root=None,
                   get_item=None,
                   get_children=None,
                   visited:set=None,
                   check_visited=None,
                   traversal_ordering='bfs'
                   ):
    if get_children is None and get_item is None:
        get_children, get_item = _get_tree_children, _get_tree_item
    elif get_children is not None:
        raise ValueError("`get_children` must be implemented if `get_item` is provided")
    elif get_item is not None:
        raise ValueError("`get_item` must be implemented if `get_children` is provided")

    if root is dev.default:
        root = get_children(tree)[0]
    if root in visited:
        return

    if check_visited is None:
        check_visited = visited is not None
    if check_visited and visited is None:
        visited = set()

    queue = collections.deque([root])
    if isinstance(traversal_ordering, str):
        traversal_ordering = TreeTraversalOrder(traversal_ordering)
    if traversal_ordering is traversal_ordering.BreadthFirst:
        pop = queue.pop
        extend = queue.extend
    else:
        pop = queue.popleft
        extend = queue.extendleft

    while queue:
        head = pop()
        if check_visited:
            visited.add(head)
        callback(head)

        if check_visited:
            extend(
                get_item(head, h)
                for h in get_children(head)
                if h not in visited
            )
        else:
            extend(
                get_item(head, h)
                for h in get_children(head)
            )

class TreeWrapper:
    def __init__(self, tree):
        self.tree = tree

    def __repr__(self):
        fmt_tree = pprint.pformat(self.tree)
        cls = type(self)
        return f"{cls.__name__}({fmt_tree})"
    def __len__(self):
        return len(self.tree)
    def keys(self):
        if hasattr(self.tree, 'keys'):
            return self.tree.keys()
        else:
            return None
    def values(self):
        if hasattr(self.tree, 'values'):
            return self.tree.values()
        else:
            return self.tree
    def __getitem__(self, item):
        if nput.is_atomic(item):
            item = [item]
        t = self.tree
        base_exception = None
        for k in item:
            if not isinstance(k, str) and hasattr(t, 'keys'):
                woof = []
                for n,v in enumerate(t.keys()):
                    woof.append(v)
                    if n >= k:
                        break
                else:
                    base_exception = IndexError("index {} not valid for subtree with keys {}".format(
                        k, t.keys()
                    ))
                    break
                k = woof[-1]
            try:
                t = t[k]
            except (IndexError, KeyError) as e:
                base_exception = e
                break

        if base_exception is not None:
            raise IndexError(f"{item} not found in tree") from base_exception


        return t
    def bfs(self, callback, **opts):
        #TODO: support most sophsticated children/item indexing
        return tree_traversal(self.tree, callback, traversal_ordering='bfs', **opts)
    def dfs(self, callback, **opts):
        return tree_traversal(self.tree, callback, traversal_ordering='dfs', **opts)