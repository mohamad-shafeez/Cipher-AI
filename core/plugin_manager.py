import os
import sys
import importlib.util
import py_compile

class PluginManager:
    @classmethod
    def synthesize_and_load_skill(cls, skill_name: str, python_code: str, base_workspace: str = "D:/Visual Studio/Cipher-AI") -> dict:
        """
        Takes raw LLM-synthesized python string text, compiles it into a runtime skill module on disk,
        and dynamically registers it inside the system's memory spaces without drops or restarts.
        """
        result = {"success": False, "error": "", "module_object": None}
        
        # Standardize the file naming system inside the active skills folder
        safe_name = "".join([c for c in skill_name if c.isalnum() or c == '_']).lower()
        if not safe_name.endswith("_skill"):
            safe_name += "_skill"
            
        skills_dir = os.path.join(base_workspace, "skills")
        os.makedirs(skills_dir, exist_ok=True)
        filepath = os.path.join(skills_dir, f"dynamic_{safe_name}.py").replace("\\", "/")

        try:
            # 1. Output the freshly synthesized plugin tool to disk storage
            print(f"🛠️ [TOOL SYNTHESIS]: Writing dynamic runtime script to {filepath}...")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(python_code)

            # 2. Force an isolated compilation token analysis step to assert syntax correctness
            py_compile.compile(filepath, doraise=True)
            print(f"✅ [TOOL SYNTHESIS]: Script compilation check passed. Injecting into memory context...")

            # 3. Clear Python's file finder caches to guarantee it sees the newly added disk file
            importlib.invalidate_caches()

            # 4. Dynamically mount the custom class objects directly into runtime memory namespaces
            module_name = f"skills.dynamic_{safe_name}"
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to generate module specifications mapping layout for {filepath}")
                
            new_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = new_module
            spec.loader.exec_module(new_module)

            # 5. Extract the class reference blueprint cleanly from the newly allocated namespace
            # Expects standard CamelCase formatting (e.g., dynamic_database_skill -> DatabaseSkill)
            class_name = "".join([part.capitalize() for part in safe_name.split("_")])
            skill_class = getattr(new_module, class_name, None)

            if not skill_class:
                # Fallback if specific naming rules aren't completely matched by smaller models
                # Grab the first available attribute matching a traditional class layout
                for attr in dir(new_module):
                    if attr.endswith("Skill") and attr != "BaseSkill":
                        skill_class = getattr(new_module, attr)
                        break

            if skill_class:
                print(f"✨ [HOT-RELOAD SUCCESS]: Registered dynamic tool token class: '{skill_class.__name__}'")
                result["success"] = True
                result["module_object"] = skill_class()
            else:
                result["error"] = f"Code compiled successfully, but could not resolve custom Skill subclass entrypoint."

        except py_compile.PyCompileError as compile_err:
            result["error"] = f"Syntax verification rejected runtime compilation payload: {str(compile_err)}"
            print(f"🛑 [SYNTHESIS BLOCKER]: Dynamic module rejected by compiler line tests.")
            if os.path.exists(filepath):
                os.remove(filepath)  # Clean up the malformed file
        except Exception as e:
            result["error"] = f"Run-time registration exception event caught: {str(e)}"
            print(f"❌ [HOT-RELOAD FAILURE]: {result['error']}")

        return result
