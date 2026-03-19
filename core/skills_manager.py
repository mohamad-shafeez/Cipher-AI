# core/skills_manager.py
import os
import importlib
import inspect

class SkillManager:
    def __init__(self):
        self.skills = []
        self._load_all_skills()

    def _load_all_skills(self):
        # Load in priority order — mobile and system first
        priority_order = [
            "mobile", "system", "apps", "window", 
            "file", "coding", "research", "hello", "browser"
        ]
        
        skills_dir = "skills"
        if not os.path.exists(skills_dir):
            os.makedirs(skills_dir)

        # Load priority skills first
        loaded = []
        for priority in priority_order:
            for filename in os.listdir(skills_dir):
                name = filename[:-3]  # remove .py
                if name == priority and filename.endswith(".py"):
                    self._load_skill(filename)
                    loaded.append(filename)

        # Load remaining skills
        for filename in os.listdir(skills_dir):
            if filename.endswith(".py") and filename != "__init__.py" and filename not in loaded:
                self._load_skill(filename)

    def _load_skill(self, filename):
        module_name = f"skills.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            import config
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and not name.startswith("__"):
                    self.skills.append(obj())
                    print(f">> {config.ASSISTANT_NAME} learned skill: {name}")
        except Exception as e:
            print(f"Error loading {module_name}: {e}")

    def run_skills(self, command):
        for skill in self.skills:
            if hasattr(skill, "execute"):
                result = skill.execute(command)
                if result:
                    return result
        return None