"""
Data Manager Module

Handles loading, validating, and saving social network data
persistently to and from social_network.json.
"""

from pathlib import Path
from typing import Any, Dict, List, Union
import json
import networkx as nx

import graph_operations as go

DEFAULT_DATA_PATH = Path(__file__).parent / "social_network.json"


def graph_to_dict(graph: nx.Graph) -> Dict[str, Any]:
    """
    Convert a NetworkX graph into a serializable dictionary structure.

    Returns:
        dict: {"people": sorted_nodes_list, "friendships": sorted_edge_pairs_list}
    """
    people: List[str] = sorted(list(graph.nodes()))
    friendships: List[List[str]] = sorted(
        [sorted([str(u), str(v)]) for u, v in graph.edges()]
    )
    return {
        "people": people,
        "friendships": friendships,
    }


def dict_to_graph(data: Dict[str, Any]) -> nx.Graph:
    """
    Build and return a NetworkX graph from a data dictionary.

    Parameters:
        data: Dict containing 'people' and 'friendships' lists.

    Returns:
        nx.Graph: Constructed undirected graph.
    """
    people = data.get("people", []) if isinstance(data, dict) else []
    friendships = data.get("friendships", []) if isinstance(data, dict) else []
    return go.build_graph(people=people, friendships=friendships, ignore_invalid=True)


def load_data(file_path: Union[str, Path] = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    """
    Load network data safely from a JSON file.

    Parameters:
        file_path: Path to the JSON data file.

    Returns:
        dict: Dictionary with 'people' and 'friendships' lists.
    """
    path = Path(file_path)
    if not path.exists():
        return {"people": [], "friendships": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"people": [], "friendships": []}
            data = json.loads(content)
            if not isinstance(data, dict):
                return {"people": [], "friendships": []}
            if "people" not in data or not isinstance(data["people"], list):
                data["people"] = []
            if "friendships" not in data or not isinstance(data["friendships"], list):
                data["friendships"] = []
            return data
    except Exception as err:
        raise ValueError(f"Failed to load network data from '{path}': {err}") from err


def save_data(
    data: Dict[str, Any], file_path: Union[str, Path] = DEFAULT_DATA_PATH
) -> None:
    """
    Save raw network data dictionary persistently to a JSON file.

    Parameters:
        data: Dict containing 'people' and 'friendships'.
        file_path: Path to the target JSON file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    people = data.get("people", [])
    friendships = data.get("friendships", [])

    clean_data = {
        "people": sorted(list(people)),
        "friendships": sorted([sorted(list(f)) for f in friendships]),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2)


def load_graph(file_path: Union[str, Path] = DEFAULT_DATA_PATH) -> nx.Graph:
    """
    Load network from JSON file directly into a NetworkX graph.

    Parameters:
        file_path: Path to the JSON file.

    Returns:
        nx.Graph: Constructed graph.
    """
    data = load_data(file_path)
    return dict_to_graph(data)


def save_graph(
    graph: nx.Graph, file_path: Union[str, Path] = DEFAULT_DATA_PATH
) -> None:
    """
    Save a NetworkX graph persistently to the JSON file.

    Parameters:
        graph: NetworkX graph to serialize.
        file_path: Target JSON file path.
    """
    data = graph_to_dict(graph)
    save_data(data, file_path)
