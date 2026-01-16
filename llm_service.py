from google import genai
from google.genai import types


class LLMService:
    """Service to interact with the LLM for generating responses."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash-lite"
        self.system_prompt = (
            "You are an expert college football analyst in a parallel universe where games are decided by competitions between the teams' mascots. "
            "The parameters of the contest are as follows: Each mascot has a unique set of skills and attributes that reflect the spirit and culture of their respective teams."
            "The mascots will engage in a series of challenges that test their agility, strength, intelligence, and teamwork. "
            "Your analysis should consider these factors and provide a clear rationale for your prediction. "
            "Given two college football teams, provide a prediction as to why one team would defeat the other in under 150 words"
        )

    def generate_response(self, victor: str, loser: str) -> str:
        prompt = (
            f"Explain why {victor} would defeat {loser} in a college football game."
        )
        rsp = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
            ),
            contents=prompt,
        )
        return rsp.text
