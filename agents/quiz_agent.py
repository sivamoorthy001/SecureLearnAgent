import os
import json
import google.generativeai as genai

class QuizAgent:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')

    def generate_quiz(self, topic: str, num_questions: int = 3) -> list:
        """
        Generates a multiple choice quiz on the specified cybersecurity topic and returns it as a parsed JSON list.
        """
        if self.demo_mode:
            demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "demo_responses.json")
            with open(demo_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["quiz"]["questions"]

        prompt = f"""
        You are a Cybersecurity Instructor.
        Generate a multiple choice quiz about "{topic}" with exactly {num_questions} questions.
        Return ONLY a raw JSON object (no markdown, no ```json wrapper) with this structure:
        {{
            "questions": [
                {{
                    "question": "Question text",
                    "options": {{ "A": "...", "B": "...", "C": "...", "D": "..." }},
                    "correct_answer": "A",
                    "explanation": "Why this option is correct"
                }}
            ]
        }}
        """
        
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        try:
            parsed = json.loads(text)
            return parsed.get("questions", [])
        except Exception:
            return []
