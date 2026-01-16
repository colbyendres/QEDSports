"""Tests for Flask app routes and API."""
from unittest.mock import patch

class TestFlaskApp:
    """Test suite for Flask app routes."""

    def test_home_route(self, client):
        """Test that the home route returns 200 and contains team names."""
        rsp = client.get("/")
        assert rsp.status_code == 200
        assert b"Alabama" in rsp.data
        assert b"Georgia" in rsp.data

    def test_api_path_valid_teams(self, client):
        """Test API path endpoint with valid teams."""
        payload = {"from": "Alabama", "to": "Auburn"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 200
        data = rsp.get_json()
        assert "path" in data
        assert "edges" in data
        assert data["path"] == ["Alabama", "Georgia", "Auburn"]
        assert len(data["edges"]) == 2

    def test_api_path_unknown_team(self, client):
        """Test API path endpoint with unknown team."""
        payload = {"from": "Unknown Team", "to": "Alabama"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 400
        data = rsp.get_json()
        assert "error" in data

    def test_api_path_same_team(self, client):
        """Test API path endpoint with same team for both inputs."""
        payload = {"from": "Alabama", "to": "Alabama"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 400
        data = rsp.get_json()
        assert "error" in data
        assert "different teams" in data["error"].lower()

    def test_api_path_no_path_no_llm(self, client):
        """Test API path endpoint when no path exists and no LLM is configured."""
        payload = {"from": "Alabama", "to": "Tufts"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 400
        data = rsp.get_json()
        assert "error" in data
        assert "llm service not configured" in data["error"].lower()

    def test_api_path_no_path_with_llm(self, client, monkeypatch, mock_llm_service):
        """Test API path endpoint with LLM fallback."""
        monkeypatch.setattr("config.Config.GEMINI_API_KEY", "test-key")
        
        # Recreate app with mocked LLM
        with patch("graph_service.LLMService", return_value=mock_llm_service):
            from app import create_app
            test_app = create_app()
            test_app.config["TESTING"] = True
            test_client = test_app.test_client()
            
            payload = {"from": "Alabama", "to": "Tufts"}
            rsp = test_client.post(
                "/api/path",
                json=payload,
                content_type="application/json",
            )
            assert rsp.status_code == 200
            data = rsp.get_json()
            assert "llm_text" in data
            assert "path" in data
            assert "edges" in data

    def test_api_path_empty_payload(self, client):
        """Test API path endpoint with empty payload."""
        rsp = client.post(
            "/api/path",
            json={},
            content_type="application/json",
        )
        assert rsp.status_code == 400

    def test_api_path_case_insensitive(self, client):
        """Test that API path endpoint is case-insensitive."""
        payload = {"from": "alabama", "to": "auburn"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 200
        data = rsp.get_json()
        assert "path" in data

    def test_api_path_includes_logos(self, client):
        """Test that API path rsp includes logos."""
        payload = {"from": "Alabama", "to": "Auburn"}
        rsp = client.post(
            "/api/path",
            json=payload,
            content_type="application/json",
        )
        assert rsp.status_code == 200
        data = rsp.get_json()
        for edge in data["edges"]:
            assert "fromLogo" in edge
            assert "toLogo" in edge
            # Just check that links exist, not that they necessarily match the team
            assert edge["fromLogo"]
            assert edge["toLogo"]
