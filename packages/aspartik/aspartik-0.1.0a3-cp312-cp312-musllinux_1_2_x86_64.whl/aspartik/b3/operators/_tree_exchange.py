from math import log
from dataclasses import dataclass

from .. import Tree, Proposal, Operator
from ..tree import Internal, Node
from ...rng import RNG


@dataclass
class NarrowExchange(Operator):
    """Exchanges the parents of two neighbouring nodes

    This operator is analogous to BEAST2's `Exchange` operator with `isNarrow`
    set to true.  It finds a grandparent (internal node both of whose children
    are also internal) with two kids: `parent` and `uncle` (uncle is younger
    than the parent).  And one of the children of `parent` is swapped with
    `uncle`.
    """

    tree: Tree
    rng: RNG
    weight: float = 1

    def propose(self) -> Proposal:
        tree = self.tree

        if tree.num_internals < 2:
            return Proposal.Reject()

        num_grandparents_before = tree.num_grandparents()
        if num_grandparents_before == 0:
            # no grandparents to pick `grandparent` from
            return Proposal.Reject()

        while True:
            grandparent = tree.random_internal(self.rng)
            if tree.is_grandparent(grandparent):
                break

        left, right = tree.children_of(grandparent)
        if tree.weight_of(left) > tree.weight_of(right):
            parent, uncle = left, right
        elif tree.weight_of(right) > tree.weight_of(left):
            parent, uncle = right, left
        else:
            return Proposal.Reject()

        # guaranteed because `grandparent` is a grandparent
        assert isinstance(parent, Internal)
        assert isinstance(uncle, Internal)

        before = int(tree.is_grandparent(parent)) + int(tree.is_grandparent(uncle))

        if self.rng.random_bool(0.5):
            child = tree.children_of(parent)[0]
        else:
            child = tree.children_of(parent)[1]

        tree.swap_parents(uncle, child)

        after = int(tree.is_grandparent(parent)) + int(tree.is_grandparent(uncle))
        num_grandparents_after = num_grandparents_before - before + after
        ratio = log(num_grandparents_before / num_grandparents_after)

        return Proposal.Hastings(ratio)


@dataclass
class WideExchange(Operator):
    """Exchanges the parent of two random nodes

    This operator is analogous to BEAST2's `Exchange` operator with `isNarrow`
    set to false.  It picks two random nodes in the tree (they could be either
    leaves or internals) and swaps their parents.

    If a randomly selected move is impossible (a parent would be younger than
    its child) the operator aborts with `Proposal.Reject`.
    """

    tree: Tree
    rng: RNG
    weight: float = 1

    def propose(self) -> Proposal:
        tree = self.tree

        root = tree.root()

        i = tree.random_node(self.rng)
        while i == root:
            i = tree.random_node(self.rng)

        j = None
        while j is None or j == i or j == root:
            j = tree.random_node(self.rng)
        assert isinstance(j, Node)

        i_parent = tree.parent_of(i)
        if i_parent is None:
            return Proposal.Reject()
        j_parent = tree.parent_of(j)
        if j_parent is None:
            return Proposal.Reject()

        # Abort if j and i are parent-child or if one of the parents would be
        # younger than its new child or if the two selected nodes.
        if (
            j != i_parent
            and i != j_parent
            and tree.weight_of(j) < tree.weight_of(i_parent)
            and tree.weight_of(i) < tree.weight_of(j_parent)
        ):
            tree.swap_parents(i, j)

            return Proposal.Hastings(0.0)
        else:
            return Proposal.Reject()
