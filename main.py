# main.py
from core.listen import Listener
from core.think import Brain
from core.speak import Speaker
from core.skills_manager import SkillManager
import config
import sys
import keyboard  # ← new

def main():
    print(f"========================================")
    print(f"   {config.ASSISTANT_NAME.upper()} SYSTEM ONLINE")
    print(f"========================================")
    
    try:
        ear = Listener()
        brain = Brain()
        mouth = Speaker()
        skills = SkillManager()
        
    except Exception as e:
        print(f"Critical Error during initialization: {e}")
        sys.exit(1)
    
    mouth.speak(f"{config.ASSISTANT_NAME} is online.")
    print(f">> Press SPACE to give a command.")

    while True:
        try:
            print(f">> Waiting for SPACE key...")
            keyboard.wait("space")  # ← waits for spacebar
            
            print(f">> {config.ASSISTANT_NAME} listening...")
            mouth.speak("Yes sir?")
            
            user_text = ear.listen()
            if not user_text:
                continue
            
            print(f"Heard: {user_text}")
            command = user_text.lower().strip()

            # Remove noise words
            noise_words = ["the", "a", "an", "hey", "okay", "so", "please"]
            for noise in noise_words:
                command = command.replace(f" {noise} ", " ").strip()
                if command == noise:
                    command = ""

            if command:
                print(f">> Processing: {command}")
                
                result = skills.run_skills(command)
                
                if result:
                    print(f"Skill Action: {result}")
                    mouth.speak(result)
                else:
                    reply = brain.think(command)
                    print(f"{config.ASSISTANT_NAME}: {reply}")
                    mouth.speak(reply)
            
        except KeyboardInterrupt:
            print(f"\n>> Shutting down {config.ASSISTANT_NAME}...")
            mouth.speak("Goodbye sir.")
            break

if __name__ == "__main__":
    main()