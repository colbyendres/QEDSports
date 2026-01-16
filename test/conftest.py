"""Fixtures for testing."""

import pickle
from unittest.mock import MagicMock

import networkx as nx
import pytest


@pytest.fixture
def mock_graph():
    """Create a small test graph with known structure."""
    graph = nx.DiGraph()

    # Add nodes with labels
    nodes = {
        "0": "Alabama",
        "1": "Georgia",
        "2": "Auburn",
        "3": "Vanderbilt",
        "4": "Tufts",
    }
    for node_id, label in nodes.items():
        graph.add_node(node_id, label=label)

    # Add edges with weights and labels
    # Current season games (high weight priority)
    graph.add_edge("0", "1", weight=1, label="Alabama def. Georgia")
    graph.add_edge("1", "2", weight=1, label="Georgia def. Auburn")
    graph.add_edge("2", "3", weight=1, label="Auburn def. Vanderbilt")

    # Historical games (lower weight priority)
    graph.add_edge("2", "0", weight=2025, label="Auburn def. Alabama (2024)")

    # Tufts is isolated (no path exists)

    return graph


@pytest.fixture
def mock_teams_data():
    """Create mock team data with logos and mascots."""
    return [
        {
            "id": 0,
            "name": "Alabama",
            "mascot": "Crimson Tide",
            "logo": "https://a.espncdn.com/media/college/alabama-logo.png",
            "wins": 12,
            "losses": 1,
        },
        {
            "id": 1,
            "name": "Georgia",
            "mascot": "Bulldogs",
            "logo": "https://a.espncdn.com/media/college/georgia-logo.png",
            "wins": 11,
            "losses": 2,
        },
        {
            "id": 2,
            "name": "Auburn",
            "mascot": "Tigers",
            "logo": "https://a.espncdn.com/media/college/auburn-logo.png",
            "wins": 9,
            "losses": 4,
        },
        {
            "id": 3,
            "name": "Vanderbilt",
            "mascot": "Commodores",
            "logo": "https://a.espncdn.com/media/college/vanderbilt-logo.png",
            "wins": 6,
            "losses": 7,
        },
        {
            "id": 4,
            "name": "Tufts",
            "mascot": "Jumbos",
            "logo": "https://a.espncdn.com/media/college/tufts-logo.png",
            "wins": 8,
            "losses": 5,
        },
    ]


@pytest.fixture
def temp_graph_file(tmp_path, mock_graph):
    """Write a temporary GEXF graph file."""
    graph_path = tmp_path / "test_graph.gexf"
    nx.write_gexf(mock_graph, graph_path)
    return graph_path


@pytest.fixture
def temp_teams_file(tmp_path, mock_teams_data):
    """Write a temporary teams pickle file."""
    teams_path = tmp_path / "test_teams.pkl"
    with open(teams_path, "wb") as fp:
        pickle.dump(mock_teams_data, fp)
    return teams_path


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock_service = MagicMock()
    mock_service.generate_response.return_value = (
        "The Georgia Bulldogs would defeat Tufts because the sheer "
        "ferocity and size of the mascot would overwhelm the Jumbo. "
        "A bulldog would never back down from a fight."
    )
    return mock_service


@pytest.fixture
def mock_config(monkeypatch):
    """Mock the Config class."""
    monkeypatch.setattr("config.Config.GEMINI_API_KEY", "test-key")


@pytest.fixture
def app(temp_graph_file, temp_teams_file, monkeypatch):
    """Create a test Flask app."""
    # Mock Config to use temporary files
    # Disable LLM functionality by default
    monkeypatch.setattr("config.Config.GRAPH_PATH", temp_graph_file)
    monkeypatch.setattr("config.Config.TEAMS_PATH", temp_teams_file)
    monkeypatch.setattr("config.Config.GEMINI_API_KEY", None)

    from app import create_app

    test_app = create_app()
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()
