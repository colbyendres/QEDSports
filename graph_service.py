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

from llm_service import LLMService
from config import Config


@dataclass
class PathResult:
    path_names: list[str]
    edges: list[dict[str, str]]
    error: str | None = None
    llm_text: str | None = None


class GraphService:
    """Wraps graph loading and path finding."""

    def __init__(self, graph_path: Path, teams_path: Path):
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph file not found at {graph_path}")

        self.graph = nx.read_gexf(graph_path)
        # Build lookup: node_id -> team name from label attribute
        self._id_to_name = {
            node: data.get("label", node) for node, data in self.graph.nodes(data=True)
        }
        # Build reverse lookup: lowercased name -> node_id for search
        self._name_to_id = {
            name.lower().strip(): node_id for node_id, name in self._id_to_name.items()
        }
        self.team_names = sorted(set(self._id_to_name.values()))

        # Load team data with logos
        with open(teams_path, "rb") as f:
            teams_list = pickle.load(f)

        self._id_to_logo = {
            str(team["id"]): team.get("logo", "") for team in teams_list
        }
        self._id_to_mascot = {
            str(team["id"]): team.get("mascot", "") for team in teams_list
        }

        # Initialize LLM service for fallback explanations
        self._llm_service = (
            LLMService(Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None
        )

    def get_num_teams(self) -> int:
        return len(self._id_to_name)

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
            path_nodes = nx.shortest_path(self.graph, src, dst, weight="weight")
        except nx.NetworkXNoPath:
            msg, success = self.fallback_to_llm(src, dst)
            if success:
                # Include logos in the response for the frontend to use
                return PathResult(
                    [self._id_to_name[src], self._id_to_name[dst]],
                    [
                        {
                            "fromLogo": self._id_to_logo.get(str(src), ""),
                            "toLogo": self._id_to_logo.get(str(dst), ""),
                        }
                    ],
                    llm_text=msg,
                )
            return PathResult([], [], error=msg)
        except nx.NodeNotFound:
            return PathResult([], [], error="Unknown team name provided.")

        path_names = [self._id_to_name[node] for node in path_nodes]
        edges: list[dict[str, str]] = []
        for u, v in zip(path_nodes, path_nodes[1:]):
            edge_data = self.graph[u][v]
            label = (
                edge_data.get("label")
                or f"{self._id_to_name[u]} def. {self._id_to_name[v]}"
            )
            edges.append(
                {
                    "from": self._id_to_name[u],
                    "to": self._id_to_name[v],
                    "label": label,
                    "fromLogo": self._id_to_logo.get(str(u), ""),
                    "toLogo": self._id_to_logo.get(str(v), ""),
                }
            )

        return PathResult(path_names, edges)

    def fallback_to_llm(self, victor_id: int, loser_id: int) -> tuple[str, bool]:
        """Generate a fallback explanation using the LLM service."""
        if not self._llm_service:
            return "LLM service not configured.", False
        try:
            # Supply team names along with mascots
            victor = self._id_to_name[victor_id] + " " + self._id_to_mascot[victor_id]
            loser = self._id_to_name[loser_id] + " " + self._id_to_mascot[loser_id]
            return self._llm_service.generate_response(victor, loser), True
        except Exception as e:
            return f"Error generating LLM response: {str(e)}", False
