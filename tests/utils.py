import uuid
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from path_tmpl_worker.db.orm import Node


def get_ancestors(
    session: Session, node_id: uuid.UUID, include_self: bool = True
) -> List[Tuple[uuid.UUID, str]]:
    """Returns all ancestors of the node, ordered from root to node."""

    # Base case: the starting node
    base = (
        select(
            Node.id,
            Node.title,
            Node.parent_id,
        )
        .where(Node.id == node_id)
        .cte(name="tree", recursive=True)
    )

    # Recursive case: join with parent
    tree_alias = base.alias()
    recursive = select(
        Node.id,
        Node.title,
        Node.parent_id,
    ).join(tree_alias, Node.id == tree_alias.c.parent_id)

    # Combine base and recursive
    cte = base.union_all(recursive)

    # Final query
    if include_self:
        stmt = select(cte.c.id, cte.c.title)
    else:
        stmt = select(cte.c.id, cte.c.title).where(cte.c.id != node_id)

    result = session.execute(stmt)

    # Build list and reverse to get root-to-node order
    items = [(row.id, row.title) for row in result]
    items.reverse()

    return items
