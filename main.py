import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from profile_manager import ProfileManager
from agents.curriculum_agent import CurriculumAgent
from agents.ctf_hint_agent import CTFHintAgent
from agents.quiz_agent import QuizAgent
from agents.personalization_agent import PersonalizationAgent

def main():
    load_dotenv()
    
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    if demo_mode:
        print("\n=== DEMO MODE === Using sample responses. Set DEMO_MODE=false to use live AI.\n")
    else:
        if not os.getenv("GEMINI_API_KEY"):
            print("Warning: GEMINI_API_KEY is not set in the environment variables.")
            print("Please copy .env.example to .env and add your API key, or set DEMO_MODE=true.")
            return

    # Initialize Profile & Session Memory
    print("Loading student profile...")
    profile_mgr = ProfileManager()
    session_topics = set()

    print(f"\nWelcome back to SecureLearnAgent!")
    print(f"Current Study Streak: {profile_mgr.profile['study_streak']} day(s) 🔥")
    
    while True:
        print("\n=== Main Menu ===")
        print("1. Start Learning Path")
        print("2. Get CTF Hint")
        print("3. Take Quiz")
        print("4. Get My Recommendation")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            topic = input("Enter a cybersecurity topic: ").strip()
            if not topic: continue
            
            agent = CurriculumAgent()
            print("\nGenerating Curriculum...\n")
            result = agent.generate_curriculum(topic)
            print(result)
            
            os.makedirs("learning_paths", exist_ok=True)
            filename = f"learning_paths/{topic.replace(' ', '_').lower()}_path.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result)
            
            # Update Trackers
            session_topics.add(topic)
            profile_mgr.mark_topic_studied(topic)
            print(f"\n[+] '{topic}' added to studied topics and saved to profile.")

        elif choice == '2':
            category = input("Enter CTF Category (e.g., web, crypto): ")
            description = input("Enter the CTF challenge description: ")
            agent = CTFHintAgent()
            print("\nGenerating Hints...\n")
            print(agent.generate_hints(description, category))
            
        elif choice == '3':
            topic = input("Enter a topic for the quiz: ").strip()
            if not topic: continue
            
            agent = QuizAgent()
            print(f"\nGenerating 3 questions on {topic}...\n")
            questions = agent.generate_quiz(topic, num_questions=3)
            
            if not questions:
                print("Failed to generate quiz. Please try again.")
                continue
                
            correct_count = 0
            for i, q in enumerate(questions, 1):
                print(f"\nQuestion {i}: {q['question']}")
                for key, val in q['options'].items():
                    print(f"  {key}) {val}")
                
                answer = input("Your answer (A/B/C/D): ").strip().upper()
                if answer == q.get('correct_answer', '').upper():
                    print("Correct! ✅")
                    print(f"Explanation: {q.get('explanation', '')}")
                    correct_count += 1
                else:
                    print(f"Incorrect. ❌ The correct answer was {q.get('correct_answer', '')}.")
                    print(f"Explanation: {q.get('explanation', '')}")
                    
            score_percentage = (correct_count / len(questions)) * 100
            print(f"\nQuiz Complete! Your score: {correct_count}/{len(questions)} ({score_percentage:.1f}%)")
            
            # Update Trackers
            session_topics.add(topic)
            profile_mgr.record_quiz_score(topic, score_percentage)
            print(f"[+] Quiz score for '{topic}' recorded in your profile.")

        elif choice == '4':
            agent = PersonalizationAgent()
            print("\nAnalyzing your profile and session history...\n")
            profile_data_str = profile_mgr.get_profile_summary()
            
            recommendation = agent.recommend_next_topic(profile_data_str, list(session_topics))
            print("=== Personalized Recommendation ===")
            print(recommendation)
            
        elif choice == '5':
            print("Saving profile and exiting. Happy Hacking!")
            profile_mgr.save_profile()
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
