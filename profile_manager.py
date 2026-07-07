import os
import json
from datetime import datetime, timedelta

class ProfileManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.profile_path = os.path.join(self.data_dir, "student_profile.json")
        self.profile = self.load_profile()
        self.update_streak()

    def _default_profile(self):
        return {
            "topics_studied": [],
            "quiz_scores": {},  # Format: "topic": score_percentage (e.g. 75.0)
            "weak_areas": [],
            "study_streak": 1,
            "last_active_date": datetime.now().strftime("%Y-%m-%d")
        }

    def load_profile(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.profile_path):
            return self._default_profile()
            
        with open(self.profile_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return self._default_profile()

    def save_profile(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile, f, indent=4)

    def update_streak(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        last_active_str = self.profile.get("last_active_date", today_str)
        
        if last_active_str != today_str:
            last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            if today - last_active == timedelta(days=1):
                # Consecutive day
                self.profile["study_streak"] = self.profile.get("study_streak", 0) + 1
            else:
                # Streak broken
                self.profile["study_streak"] = 1
                
            self.profile["last_active_date"] = today_str
            self.save_profile()

    def mark_topic_studied(self, topic):
        topic_lower = topic.lower()
        if topic_lower not in [t.lower() for t in self.profile["topics_studied"]]:
            self.profile["topics_studied"].append(topic)
            self.save_profile()

    def record_quiz_score(self, topic, score_percentage):
        topic_lower = topic.lower()
        self.profile["quiz_scores"][topic_lower] = score_percentage
        
        # Recalculate weak areas (below 70%)
        self.profile["weak_areas"] = [
            t for t, score in self.profile["quiz_scores"].items() if score < 70.0
        ]
        self.save_profile()

    def get_profile_summary(self):
        return json.dumps(self.profile, indent=2)
