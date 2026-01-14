"""Minimal Flask app to expose transitive win chains between teams.

This loads the precomputed victory graph (graph.gexf), normalizes team
names, and provides a small API plus a template-backed UI for browsing
paths. Tailwind is pulled from a CDN; client JS handles the form +
rendering.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

@dataclass
class PathResult:
    path_names: list[str]
    edges: list[dict[str, str]]
    error: str | None = None


class GraphService:
    """Wraps graph loading and path finding."""

    def __init__(self, graph_path: Path, teams_path: Path):
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph file not found at {graph_path}")

        self.graph = nx.read_gexf(graph_path)
        # Build lookup: node_id -> team name from label attribute
        self._id_to_name = {node: data.get(
            "label", node) for node, data in self.graph.nodes(data=True)}
        # Build reverse lookup: lowercased name -> node_id for search
        self._name_to_id = {name.lower().strip(
        ): node_id for node_id, name in self._id_to_name.items()}
        self.team_names = sorted(set(self._id_to_name.values()))

        # Load team data with logos
        with open(teams_path, "rb") as f:
            teams_list = pickle.load(f)
        self._id_to_logo = {str(team["id"]): team.get(
            "logo", "") for team in teams_list}

    def find_path(self, start_name: str, end_name: str) -> PathResult:
        key_a = (start_name or "").strip().lower()
        key_b = (end_name or "").strip().lower()

        src = self._name_to_id.get(key_a)
        dst = self._name_to_id.get(key_b)

        if not src or not dst:
            return PathResult([], [], error="Unknown team name provided.")
        if src == dst:
            disp = self._id_to_name[src]
            return PathResult([disp], [], error="Choose two different teams.")

        try:
            path_nodes = nx.shortest_path(
                self.graph, src, dst, weight="weight")
        except nx.NetworkXNoPath:
            return PathResult([], [], error="No transitive path found.")
        except nx.NodeNotFound:
            return PathResult([], [], error="Unknown team name provided.")

        path_names = [self._id_to_name[node] for node in path_nodes]
        edges: list[dict[str, str]] = []
        for u, v in zip(path_nodes, path_nodes[1:]):
            edge_data = self.graph[u][v]
            label = edge_data.get(
                "label") or f"{self._id_to_name[u]} def. {self._id_to_name[v]}"
            edges.append({
                "from": self._id_to_name[u],
                "to": self._id_to_name[v],
                "label": label,
                "fromLogo": self._id_to_logo.get(u, ""),
                "toLogo": self._id_to_logo.get(v, ""),
            })

        return PathResult(path_names, edges)
