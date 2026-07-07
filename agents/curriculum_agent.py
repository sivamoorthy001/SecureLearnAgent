import os
import json
import google.generativeai as genai

class CurriculumAgent:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')

    def generate_curriculum(self, topic: str) -> str:
        """
        Generates a structured beginner-to-advanced learning path for a given cybersecurity topic.
        """
        if self.demo_mode:
            demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "demo_responses.json")
            with open(demo_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["curriculum"]

        prompt = f"""
        You are an expert Cybersecurity Education AI.
        Create a structured, beginner-to-advanced learning path for the following topic: "{topic}".
        
        The curriculum must include:
        1. A brief introduction to the topic.
        2. Beginner concepts and foundational knowledge required.
        3. Intermediate concepts with practical applications or lab ideas.
        4. Advanced concepts, including real-world scenarios or complex attacks/defenses.
        5. A list of high-quality resources to study (e.g., specific CVEs, standard tools, documentation).
        
        Format the response in clear Markdown.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
