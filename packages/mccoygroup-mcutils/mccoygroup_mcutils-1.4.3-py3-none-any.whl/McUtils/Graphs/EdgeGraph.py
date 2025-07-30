
import itertools, collections
import scipy.sparse as sparse, numpy as np
from .. import Numputils as nput
from .. import Iterators as itut

__all__ = [
    "EdgeGraph"
]

class EdgeGraph:
    __slots__ = ["labels", "edges", "graph", "map"]
    def __init__(self, labels, edges, graph=None, edge_map=None):
        self.labels = labels
        self.edges = np.asanyarray(edges)
        if graph is None:
            graph = self.adj_mat(len(labels), self.edges)
        self.graph = graph
        if edge_map is None:
            edge_map = self.build_edge_map(self.edges)
        self.map = edge_map

    @classmethod
    def adj_mat(cls, num_nodes, edges):
        adj = np.zeros((num_nodes, num_nodes), dtype=bool)
        rows,cols = edges.T
        adj[rows, cols] = 1
        adj[cols, rows] = 1

        return sparse.csr_matrix(adj)

    @classmethod
    def build_edge_map(cls, edge_list):
        map = {}
        for e1,e2 in edge_list:
            if e1 not in map: map[e1] = set()
            map[e1].add(e2)
            if e2 not in map: map[e2] = set()
            map[e2].add(e1)
        return map

    @classmethod
    def _remap(cls, labels, pos, rows, cols):
        if len(rows) == 0:
            edge_list = np.array([], dtype=int).reshape(-1, 2)
        else:
            new_mapping = np.zeros(len(labels), dtype=int)
            new_mapping[pos,] = np.arange(len(pos))
            new_row = new_mapping[rows,]
            new_col = new_mapping[cols,]
            edge_list = np.array([new_row, new_col]).T

        return [labels[p] for p in pos], edge_list
    @classmethod
    def _take(cls, pos, labels, adj_mat:sparse.compressed):
        rows, cols, _ = sparse.find(adj_mat)
        utri = cols >= rows
        rows = rows[utri]
        cols = cols[utri]
        row_cont, _, _ = nput.contained(rows, pos)
        col_cont, _, _ = nput.contained(cols, pos)
        cont = np.logical_and(row_cont, col_cont)

        labels, edge_list = cls._remap(labels, pos, rows[cont], cols[cont])
        return cls(labels, edge_list)

    def take(self, pos):
        return self._take(pos, self.labels, self.graph)

    def split(self, backbone_pos):
        new_adj = self.graph.copy()
        for n in backbone_pos:
            for i,j in self.map[n]:
                new_adj[i,j] = 0
        ncomp, labels = sparse.csgraph.connected_components(new_adj, directed=False, return_labels=True)
        groups, _ = nput.group_by(np.arange(len(labels)), labels)
        return [
            self._take(pos, self.labels, new_adj)
            for _, pos in groups
        ]

    @classmethod
    def _bfs(cls, test, root, edge_map, visited:set):
        if root in visited:
            return
        queue = collections.deque([root])
        while queue:
            head = queue.pop()
            visited.add(head)
            test(head)
            queue.extend(h for h in edge_map.get(head, []) if h not in visited)
    @classmethod
    def _subgraph_match(cls,
                        root1, labels1, edge_map1,
                        root2, labels2, edge_map2,
                        visited=None
                        ):
        if labels1[root1] != labels2[root2]:
            return False
        if len(edge_map1.get(root1, [])) != len(edge_map2.get(root2, [])):
            return False

        if visited is None:
            visited = (set(), set())
        visit1, visit2 = visited

        # queue1 = collections.deque([root1])
        tests1 = set(edge_map1.get(root1, [])) - visit1
        tests2 = set(edge_map2.get(root2, [])) - visit2
        for r1 in tests1:
            visit1.add(r1)
            for r2 in tests2:
                visit2.add(r2)
                # check if all the subgraphs match via DFS
                # we could do this without recursion, but it'd be
                # more annoying
                if cls._subgraph_match(
                    r1, labels1, edge_map1,
                    r2, labels2, edge_map2,
                    visited=(visit1, visit2)
                ):
                    tests2.remove(r2)
                    break
                else:
                    visit2.remove(r2)

        return len(tests2) == 0

    @classmethod
    def graph_match(cls, graph1:'EdgeGraph', graph2:'EdgeGraph'):
        # we do some quick prunes
        atoms1 = graph1.labels
        atoms2 = graph2.labels
        if (
                len(atoms1) != len(atoms2)
                or atoms1[0] != atoms2[0]
                or len(graph1.edges) != len(graph2.edges)
                or list(sorted(atoms1)) != list(sorted(atoms2))
                or list(sorted(len(v) for v in graph1.map.values())) != list(sorted(len(v) for v in graph2.map.values()))
        ):
            return False

        return cls._subgraph_match(
            0, graph1.labels, graph1.map,
            0, graph2.labels, graph2.map
        )

    def __eq__(self, other):
        return self.graph_match(self, other)

    @classmethod
    def build_neighborhood_graph(cls, node, labels, edge_map, ignored=None, num=1):
        edges = []
        visited = set()
        if ignored is None: ignored = []
        ignored = set(ignored)
        queue = [node]
        for i in range(num):
            new_queue = []
            for node in queue:
                visited.add(node)
                new_nodes = set(edge_map[node]) - visited - ignored
                edges.extend((node, e) for e in new_nodes)
                new_queue.extend(new_nodes)
            queue = new_queue

        edges = np.array(edges, dtype=int)
        if len(edges) == 0:
            edges = np.reshape(edges, (-1, 2))
        labels, edges = cls._remap(labels, list(visited), edges[:, 0], edges[:, 1])
        return cls(labels, edges)

    def neighbor_graph(self, root, ignored=None, num=1):
        return self.build_neighborhood_graph(root, self.labels, self.map, ignored=ignored, num=num)

    def get_rings(self):
        # use rdkit's cycles...not assured to be the smallest set ;_;
        from ..ExternalPrograms.RDKit import RDMolecule
        return RDMolecule.from_coords(
            ["C"]*len(self.labels),
            coords=np.zeros((len(self.labels), 3)),
            bonds=[[int(i), int(j), 1] for i,j in self.edges]
        ).rings

    def get_fragments(self):
        from scipy.sparse import csgraph
        _, labels = csgraph.connected_components(self.graph, directed=False, return_labels=True)
        _, groups = nput.group_by(np.arange(len(labels)), labels)[0]
        return groups

    @classmethod
    def get_maximum_overlap_permutation(cls, graph_1:'EdgeGraph', graph_2:'EdgeGraph'):
        syms_1 = graph_1.labels
        syms_2 = graph_2.labels

        if any(s_1 != s_2 for s_1, s_2 in zip(syms_1, syms_2)):
            if len(itut.dict_diff(itut.counts(syms_1), itut.counts(syms_2))) > 0:
                raise ValueError(f"graph labels must agree: {syms_1} != {syms_2}")
            ordering_1 = list(sorted(range(len(syms_1)), key=syms_1.__getitem__))
            ordering_2 = list(sorted(range(len(syms_2)), key=syms_2.__getitem__))
            perm_0 = np.array(ordering_2)[np.argsort(ordering_1)]
            graph_2 = graph_2.take(perm_0)
        else:
            perm_0 = None

        bond_set_1 = {tuple(sorted(e)) for e in graph_1.edges}
        bond_set_2 = {tuple(sorted(e)) for e in graph_2.edges}

        # initial bond difference
        test_bonds = np.unique(np.array(
            list(bond_set_1 - bond_set_2)
            + list(bond_set_2 - bond_set_1)
        ))

        # permutable groups
        sym_splits, _ = nput.group_by(np.arange(len(syms_1)), np.array([ord(s) for s in syms_1]))
        perm_blocks = []
        perm_atoms = []
        for _, atom_inds in zip(*sym_splits):
            atom_inds = nput.intersection(atom_inds, test_bonds)[0]  # only permute things in the original core
            if len(atom_inds) > 0:
                perm_atoms.append(atom_inds)
                perm_blocks.append(itertools.permutations(atom_inds))

        nsym = len(syms_1)
        core_size = len(test_bonds)
        perm = np.arange(nsym)
        for full_perm in itertools.product(*perm_blocks):
            reindexing = np.arange(nsym)
            for atom_inds, new_idx in zip(perm_atoms, full_perm):
                reindexing[atom_inds,] = new_idx
            new_bond_set_1 = {
                (reindexing[i], reindexing[j])
                for (i, j) in bond_set_1
            }
            new_core = np.unique(np.array(
                list(new_bond_set_1 - bond_set_2)
                + list(bond_set_2 - new_bond_set_1)
            ))
            if len(new_core) < core_size:
                perm = reindexing

        if perm_0 is not None:
            return perm_0[perm]
        else:
            return perm

    def get_reindexing(self, other_graph):
        return self.get_maximum_overlap_permutation(other_graph, self)
    def align_labels(self, other_graph):
        perm = self.get_reindexing(other_graph)
        return self.take(perm)