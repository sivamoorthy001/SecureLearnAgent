import os
import json
import google.generativeai as genai

class PersonalizationAgent:
    def __init__(self):
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        if not self.demo_mode:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')

    def recommend_next_topic(self, profile_data: str, session_topics: list) -> str:
        """
        Recommends the next best topic based on the student's profile and current session history.
        """
        if self.demo_mode:
            demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "demo_responses.json")
            with open(demo_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["personalization"]

        prompt = f"""
        You are a Cybersecurity Mentorship AI. Your goal is to recommend ONE specific cybersecurity topic for the student to study next.
        
        Here is the student's current profile (JSON format):
        {profile_data}
        
        Here are the topics they have ALREADY discussed in the current study session:
        {session_topics}
        
        Rules for recommendation:
        1. Look at "weak_areas". If there are weak areas, prioritize reviewing them.
        2. Look at "topics_studied". Recommend something that builds logically upon what they already know (Difficulty progression).
        3. DO NOT recommend any topic that is in the "session_topics" list (they just did it).
        4. Do not jump to advanced topics if they haven't covered basics.
        
        Respond in Markdown format. 
        Provide the recommended topic clearly at the top, and explain why you chose it based on their profile. Include a brief summary of what they will learn.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
