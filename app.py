from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from graph_service import GraphService
from config import Config
import os


def create_app() -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)  # type: ignore[assignment]

    graph_service = GraphService(Config.GRAPH_PATH, Config.TEAMS_PATH)

    @app.route("/")
    def home():
        return render_template("index.html", team_names=graph_service.team_names)

    @app.post("/api/path")
    def api_path():
        payload = request.get_json(silent=True) or {}
        team_a = payload.get("from")
        team_b = payload.get("to")

        result = graph_service.find_path(team_a, team_b)
        if result.error:
            return jsonify({"error": result.error}), 400

        return jsonify({"path": result.path_names, "edges": result.edges, "llm_text": result.llm_text})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
