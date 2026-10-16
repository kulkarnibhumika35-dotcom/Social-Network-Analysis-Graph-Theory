"""
Graph Operations Module

Handles NetworkX undirected graph construction, safe mutations,
vertex metrics, mutual friendship discovery, component analysis,
cycle detection, and consistent adjacency matrix generation.
"""

from collections import deque
from typing import Any, Iterable, Optional
import networkx as nx
import pandas as pd


def _extract_person_name(person: Any) -> str:
    """Extract and validate a person's name identifier."""
    if isinstance(person, dict):
        name = person.get("name") or person.get("id") or person.get("username")
        if not name:
            raise ValueError(f"Person object missing 'name' or 'id' key: {person}")
        person_str = str(name).strip()
    elif isinstance(person, str):
        person_str = person.strip()
    else:
        person_str = str(person).strip()

    if not person_str:
        raise ValueError("Person name cannot be empty.")
    return person_str


def _extract_friendship_pair(friendship: Any) -> tuple[str, str]:
    """Extract and validate a friendship pair from a dict, list, or tuple."""
    if isinstance(friendship, dict):
        p1 = friendship.get("person1") or friendship.get("source") or friendship.get("user1")
        p2 = friendship.get("person2") or friendship.get("target") or friendship.get("user2")
        if not p1 or not p2:
            raise ValueError(f"Friendship object missing person endpoints: {friendship}")
        return str(p1).strip(), str(p2).strip()

    if isinstance(friendship, (list, tuple)):
        if len(friendship) != 2:
            raise ValueError(
                f"Friendship pair must contain exactly 2 elements, got {len(friendship)}: {friendship}"
            )
        p1, p2 = friendship
        if not p1 or not p2:
            raise ValueError(f"Friendship endpoints cannot be empty: {friendship}")
        return str(p1).strip(), str(p2).strip()

    raise ValueError(f"Unsupported friendship format: {friendship}")


# ---------------------------------------------------------------------------
# 1. Graph Construction
# ---------------------------------------------------------------------------

def build_graph(
    people: Optional[Iterable[Any]] = None,
    friendships: Optional[Iterable[Any]] = None,
    ignore_invalid: bool = False,
) -> nx.Graph:
    """
    Build an undirected social network graph from people and friendships.

    Parameters:
        people: Iterable of person identifiers (strings or dicts with 'name'/'id').
        friendships: Iterable of friendship pairs (tuples, lists, or dicts).
        ignore_invalid: If True, skips invalid friendships (missing users, self-loops,
                        duplicates) without raising an exception.

    Returns:
        nx.Graph: An undirected NetworkX graph.
    """
    graph = nx.Graph()

    if people:
        for p in people:
            name = _extract_person_name(p)
            if not graph.has_node(name):
                graph.add_node(name)
            elif not ignore_invalid:
                raise ValueError(f"Duplicate person '{name}' found in people list.")

    if friendships:
        for f in friendships:
            try:
                p1, p2 = _extract_friendship_pair(f)
                add_friendship(graph, p1, p2)
            except ValueError:
                if not ignore_invalid:
                    raise

    return graph


# ---------------------------------------------------------------------------
# 2. Add / Remove Operations
# ---------------------------------------------------------------------------

def add_person(graph: nx.Graph, person: str, **attrs: Any) -> None:
    """
    Add a person (vertex) to the graph safely.

    Raises:
        ValueError: If person name is empty or already exists.
    """
    name = _extract_person_name(person)
    if graph.has_node(name):
        raise ValueError(f"Person '{name}' already exists in the graph.")
    graph.add_node(name, **attrs)


def remove_person(graph: nx.Graph, person: str) -> None:
    """
    Remove a person and all their incident friendships from the graph safely.

    Raises:
        ValueError: If person does not exist in the graph.
    """
    name = _extract_person_name(person)
    if not graph.has_node(name):
        raise ValueError(f"Person '{name}' does not exist in the graph.")
    graph.remove_node(name)


def add_friendship(graph: nx.Graph, person1: str, person2: str, **attrs: Any) -> None:
    """
    Add an undirected friendship (edge) between two existing people safely.

    Validates:
    - Missing users (both must already exist in graph).
    - Self-friendships (person cannot friend themselves).
    - Duplicate friendships (edge must not already exist).

    Raises:
        ValueError: On validation failure.
    """
    p1 = _extract_person_name(person1)
    p2 = _extract_person_name(person2)

    if p1 == p2:
        raise ValueError(f"Self-friendship is not allowed: '{p1}' cannot be friends with themselves.")

    if not graph.has_node(p1):
        raise ValueError(f"User '{p1}' does not exist in the graph.")
    if not graph.has_node(p2):
        raise ValueError(f"User '{p2}' does not exist in the graph.")

    if graph.has_edge(p1, p2):
        raise ValueError(f"Friendship between '{p1}' and '{p2}' already exists.")

    graph.add_edge(p1, p2, **attrs)


def remove_friendship(graph: nx.Graph, person1: str, person2: str) -> None:
    """
    Remove an undirected friendship (edge) between two people safely.

    Raises:
        ValueError: If either person is not in graph or the friendship does not exist.
    """
    p1 = _extract_person_name(person1)
    p2 = _extract_person_name(person2)

    if not graph.has_node(p1) or not graph.has_node(p2):
        raise ValueError(f"Cannot remove friendship: one or both users ('{p1}', '{p2}') do not exist.")

    if not graph.has_edge(p1, p2):
        raise ValueError(f"Friendship between '{p1}' and '{p2}' does not exist.")

    graph.remove_edge(p1, p2)


# ---------------------------------------------------------------------------
# 3. Vertex Degrees and Most-Connected People
# ---------------------------------------------------------------------------

def get_vertex_degrees(graph: nx.Graph) -> dict[str, int]:
    """
    Calculate vertex degrees (number of friends) for all people in the network.

    Returns:
        dict[str, int]: Mapping of person name to their degree, sorted alphabetically.
    """
    return {node: graph.degree(node) for node in sorted(graph.nodes())}


get_degrees = get_vertex_degrees  # convenient alias


def get_most_connected_people(graph: nx.Graph) -> list[str]:
    """
    Identify all people with the highest degree (handles ties).

    Returns:
        list[str]: Sorted list of person names with maximum connections.
                   Returns an empty list if graph has no nodes.
    """
    if not graph.nodes:
        return []
    degrees = get_vertex_degrees(graph)
    max_deg = max(degrees.values())
    return [person for person, deg in degrees.items() if deg == max_deg]


def get_max_degree(graph: nx.Graph) -> int:
    """Return the maximum degree across all vertices in the graph (0 if empty)."""
    if not graph.nodes:
        return 0
    return max(dict(graph.degree()).values())


# ---------------------------------------------------------------------------
# 4. Mutual Friends (Set Intersection)
# ---------------------------------------------------------------------------

def get_mutual_friends(graph: nx.Graph, person1: str, person2: str) -> set[str]:
    """
    Find mutual friends between two distinct people using set intersection.

    Parameters:
        graph: NetworkX graph.
        person1: First person's name.
        person2: Second person's name.

    Returns:
        set[str]: Set of mutual friend names.

    Raises:
        ValueError: If either user is missing or person1 == person2.
    """
    p1 = _extract_person_name(person1)
    p2 = _extract_person_name(person2)

    if not graph.has_node(p1):
        raise ValueError(f"Person '{p1}' does not exist in the graph.")
    if not graph.has_node(p2):
        raise ValueError(f"Person '{p2}' does not exist in the graph.")
    if p1 == p2:
        raise ValueError("Cannot calculate mutual friends with oneself.")

    friends1 = set(graph.neighbors(p1))
    friends2 = set(graph.neighbors(p2))

    return friends1.intersection(friends2)


# ---------------------------------------------------------------------------
# 5. Connected Components and Isolated Vertices
# ---------------------------------------------------------------------------

def get_connected_components(graph: nx.Graph) -> list[set[str]]:
    """
    Find all connected components in the graph.

    Returns:
        list[set[str]]: List of components (each as a set of person names),
                        sorted by component size descending, then alphabetically.
    """
    components = [set(c) for c in nx.connected_components(graph)]
    return sorted(components, key=lambda c: (-len(c), sorted(list(c))))


def get_isolated_vertices(graph: nx.Graph) -> list[str]:
    """
    Find all isolated vertices (people with 0 friends).

    Returns:
        list[str]: Sorted list of isolated person names.
    """
    return sorted(list(nx.isolates(graph)))


# ---------------------------------------------------------------------------
# 6. Cycle Detection
# ---------------------------------------------------------------------------

def has_cycle(graph: nx.Graph) -> bool:
    """
    Detect whether any cycle exists in the undirected graph.

    Returns:
        bool: True if at least one cycle exists, False otherwise.
    """
    return len(nx.cycle_basis(graph)) > 0


def find_cycle(graph: nx.Graph) -> Optional[list[tuple[str, str]]]:
    """
    Find and return one cycle in the graph if one exists, or None.

    Returns:
        list[tuple[str, str]] | None: Cycle edges or None if acyclic.
    """
    try:
        return nx.find_cycle(graph)
    except nx.NetworkXNoCycle:
        return None


# ---------------------------------------------------------------------------
# 7. Adjacency Matrix
# ---------------------------------------------------------------------------

def get_adjacency_matrix(
    graph: nx.Graph,
    nodelist: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Generate a binary adjacency matrix with consistent node ordering.

    Parameters:
        graph: NetworkX graph.
        nodelist: Optional list of nodes to specify ordering.
                  Defaults to sorted(graph.nodes()).

    Returns:
        pd.DataFrame: Adjacency matrix with nodes as rows and columns (0/1 ints).
    """
    if nodelist is None:
        nodelist = sorted(graph.nodes())
    else:
        for node in nodelist:
            if not graph.has_node(node):
                raise ValueError(f"Node '{node}' is not in the graph.")

    if not nodelist:
        return pd.DataFrame(dtype=int)

    return nx.to_pandas_adjacency(graph, nodelist=nodelist, dtype=int)


# ---------------------------------------------------------------------------
# 8. Breadth-First Search (BFS) Shortest Path
# ---------------------------------------------------------------------------

def find_shortest_path_bfs(
    graph: nx.Graph, source: str, destination: str
) -> Optional[list[str]]:
    """
    Find the shortest path between source and destination using Breadth-First Search (BFS).

    Parameters:
        graph: NetworkX undirected graph.
        source: Name of the starting person.
        destination: Name of the target person.

    Returns:
        list[str] | None: Shortest path as a list of person names [source, ..., destination],
                          or None if no path exists.

    Raises:
        ValueError: If source or destination person does not exist in the graph.
    """
    s = _extract_person_name(source)
    d = _extract_person_name(destination)

    if not graph.has_node(s):
        raise ValueError(f"Source person '{s}' does not exist in the graph.")
    if not graph.has_node(d):
        raise ValueError(f"Destination person '{d}' does not exist in the graph.")

    if s == d:
        return [s]

    queue: deque[str] = deque([s])
    visited: set[str] = {s}
    parent: dict[str, str] = {}

    while queue:
        current = queue.popleft()

        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

                if neighbor == d:
                    path: list[str] = []
                    curr: Optional[str] = d
                    while curr is not None:
                        path.append(curr)
                        curr = parent.get(curr)
                    return path[::-1]

    return None
