"""Tests for GraphService."""

from unittest.mock import patch

import pytest

from graph_service import GraphService, PathResult


class TestGraphService:
    """Test suite for GraphService class."""

    def test_init_loads_graph_and_teams(self, temp_graph_file, temp_teams_file):
        """Test that GraphService properly initializes with graph and teams data."""
        service = GraphService(temp_graph_file, temp_teams_file)
        assert len(service.team_names) == 5
        assert "Alabama" in service.team_names
        assert "Georgia" in service.team_names
        assert service.get_num_teams() == 5

    def test_init_missing_graph_file(self, tmp_path, temp_teams_file):
        """Test that FileNotFoundError is raised when graph file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.gexf"
        with pytest.raises(FileNotFoundError):
            GraphService(nonexistent, temp_teams_file)

    def test_find_path_same_team(self, temp_graph_file, temp_teams_file):
        """Test that requesting a path from a team to itself returns an error."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Alabama", "Alabama")
        assert result.error == "Choose two different teams."
        assert result.path_names == ["Alabama"]
        assert not result.edges

    def test_find_path_unknown_team(self, temp_graph_file, temp_teams_file):
        """Test that unknown teams return an error."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Unknown Team", "Alabama")
        assert result.error == "Unknown team name provided."
        assert not result.path_names
        assert not result.edges

    def test_find_path_current_season(self, temp_graph_file, temp_teams_file):
        """Test finding a path that exists in the current season."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Alabama", "Auburn")
        assert result.error is None
        assert result.path_names == ["Alabama", "Georgia", "Auburn"]
        assert len(result.edges) == 2
        assert result.edges[0]["from"] == "Alabama"
        assert result.edges[0]["to"] == "Georgia"
        assert result.edges[1]["from"] == "Georgia"
        assert result.edges[1]["to"] == "Auburn"

    def test_find_path_includes_logos(self, temp_graph_file, temp_teams_file):
        """Test that path results include logos."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Alabama", "Auburn")
        for edge in result.edges:
            assert "fromLogo" in edge
            assert "toLogo" in edge
            assert edge["fromLogo"]  # Should not be empty
            assert edge["toLogo"]  # Should not be empty

    def test_find_path_case_insensitive(self, temp_graph_file, temp_teams_file):
        """Test that team name lookup is case-insensitive."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("alabama", "auburn")
        assert result.error is None
        assert len(result.edges) >= 1

    def test_find_path_no_path_no_llm(
        self, temp_graph_file, temp_teams_file, monkeypatch
    ):
        """Test that no path with no LLM service returns appropriate error."""
        monkeypatch.setattr("config.Config.GEMINI_API_KEY", None)
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Alabama", "Tufts")
        assert result.error == "LLM service not configured."
        assert result.llm_text is None
        assert not result.edges

    def test_find_path_no_path_with_llm(
        self, temp_graph_file, temp_teams_file, mock_llm_service, monkeypatch
    ):
        """Test that no path triggers LLM fallback when service is available."""
        monkeypatch.setattr("config.Config.GEMINI_API_KEY", "test-key")
        with patch("graph_service.LLMService", return_value=mock_llm_service):
            service = GraphService(temp_graph_file, temp_teams_file)
            result = service.find_path("Georgia", "Tufts")
            assert result.error is None
            assert result.llm_text is not None
            assert "sheer ferocity" in result.llm_text
            assert len(result.edges) == 1
            assert "fromLogo" in result.edges[0]
            assert "toLogo" in result.edges[0]

    def test_find_path_llm_exception_handling(
        self, temp_graph_file, temp_teams_file, mock_llm_service, monkeypatch
    ):
        """Test that LLM exceptions are handled gracefully."""
        monkeypatch.setattr("config.Config.GEMINI_API_KEY", "test-key")
        mock_llm_service.generate_response.side_effect = Exception("API Error")
        with patch("graph_service.LLMService", return_value=mock_llm_service):
            service = GraphService(temp_graph_file, temp_teams_file)
            result = service.find_path("Alabama", "Tufts")
            assert result.error is not None
            assert "Error generating LLM response" in result.error
            assert result.llm_text is None

    def test_path_with_persistence(self, temp_graph_file, temp_teams_file):
        """Test that historical games (with years) are included in paths."""
        service = GraphService(temp_graph_file, temp_teams_file)
        result = service.find_path("Georgia", "Alabama")

        assert result.error is None
        assert result.path_names == ["Georgia", "Auburn", "Alabama"]
        assert len(result.edges) == 2
        assert "(2024)" in result.edges[1]["label"]

    def test_path_result_dataclass(self):
        """Test PathResult dataclass structure."""
        result = PathResult(
            path_names=["A", "B", "C"],
            edges=[{"from": "A", "to": "B"}],
            error=None,
            llm_text=None,
        )
        assert result.path_names == ["A", "B", "C"]
        assert len(result.edges) == 1
        assert result.error is None
        assert result.llm_text is None
