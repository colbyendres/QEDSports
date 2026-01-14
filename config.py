import os
from pathlib import Path

class Config:
    GRAPH_PATH = Path(__file__).parent / "data/graph.gexf"
    TEAMS_PATH = Path(__file__).parent / "data/teams.pkl"
    