import os
import json
import google.generativeai as genai

class CTFHintAgent:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')

    def generate_hints(self, description: str, category: str) -> str:
        """
        Provides progressive hints for a CTF challenge based on its description and category.
        """
        if self.demo_mode:
            demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "demo_responses.json")
            with open(demo_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["ctf_hints"]

        prompt = f"""
        You are a CTF (Capture The Flag) mentor and coach.
        A student is stuck on a challenge.
        
        Category: {category}
        Challenge Description: {description}
        
        Provide 3 progressive hints to help the student solve the challenge.
        Important Rules:
        - Do NOT give the flag or the complete solution.
        - Hint 1 should be a gentle nudge regarding what to look at first.
        - Hint 2 should introduce the required tool or technique.
        - Hint 3 should be a strong push towards the vulnerability or method of exploitation, but still require the student to execute it.
        
        Format the response with clear headings for each Hint.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
