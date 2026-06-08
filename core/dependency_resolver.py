import os
import re

class DependencyResolver:
    @staticmethod
    def extract_local_dependencies(file_path: str, base_workspace: str) -> dict:
        """
        Scans a file for local imports (e.g., 'import utils' or 'from helpers import run')
        and maps them to actual file text context if they exist in the workspace.
        """
        dependencies = {}
        if not os.path.exists(file_path):
            return dependencies

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find common import syntaxes:
            # 1. 'import module_name'
            # 2. 'from module_name import ...'
            import_patterns = [
                r'^\s*import\s+([\w\.]+)',
                r'^\s*from\s+([\w\.]+)\s+import'
            ]
            
            found_modules = []
            for line in content.splitlines():
                for pattern in import_patterns:
                    match = re.search(pattern, line)
                    if match:
                        # Extract the base module name (handles dots like core.utils)
                        mod_name = match.group(1).split('.')[0]
                        if mod_name not in found_modules:
                            found_modules.append(mod_name)

            # Check if those extracted modules exist as files in our workspace
            for mod in found_modules:
                # Exclude standard library/third-party targets by looking directly inside workspace
                possible_paths = [
                    os.path.join(base_workspace, f"{mod}.py"),
                    os.path.join(base_workspace, "..", f"{mod}.py"),  # check root level
                    os.path.join(base_workspace, mod, "__init__.py")
                ]

                for path in possible_paths:
                    normalized_path = os.path.abspath(path).replace("\\", "/")
                    if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                        # Ensure we don't accidentally read the current target file infinitely
                        if normalized_path != os.path.abspath(file_path).replace("\\", "/"):
                            try:
                                with open(normalized_path, "r", encoding="utf-8") as dep_f:
                                    dependencies[mod] = dep_f.read()
                                print(f"🔗 [SYNAPTIC LINK]: Loaded context from dependency module: {mod}")
                                break
                            except Exception:
                                pass
        except Exception as e:
            print(f"❌ [DEPENDENCY CRASH]: Failed parsing imports: {str(e)}")

        return dependencies
