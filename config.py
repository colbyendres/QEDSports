import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    load_dotenv()    
    GRAPH_PATH = Path(__file__).parent / "data/graph.gexf"
    TEAMS_PATH = Path(__file__).parent / "data/teams.pkl"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    