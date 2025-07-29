from radon.visitors import ComplexityVisitor
from radon.raw import analyze as analyze_raw
import os
from typing import Dict, List, Any

class ComplexityAnalyzer:
    """
    Analyzes the cyclomatic complexity of Python files, providing both an
    average for the file and a breakdown per function.
    """

    def analyze_files(self, repo_path: str, file_paths: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Calculates cyclomatic complexity for a list of Python files.

        Args:
            repo_path: The absolute path to the repository.
            file_paths: A list of file paths relative to the repository root.

        Returns:
            A dictionary mapping file paths to their complexity data, including
            average complexity and a list of functions with their complexities.
            Returns a default structure for files that cannot be parsed.
        """
        complexity_data = {}
        for file_path in file_paths:
            full_path = os.path.join(repo_path, file_path)

            default_result = {"average_complexity": 0, "functions": []}

            if not os.path.exists(full_path):
                complexity_data[file_path] = default_result
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    complexity_data[file_path] = default_result
                    continue

                visitor = ComplexityVisitor.from_code(content)

                functions_data = [
                    {"name": f.name, "complexity": f.complexity}
                    for f in visitor.functions
                ]

                # Sort functions by complexity, descending
                functions_data.sort(key=lambda x: x['complexity'], reverse=True)

                total_complexity = sum(f['complexity'] for f in functions_data)
                num_functions = len(functions_data)
                average_complexity = total_complexity / num_functions if num_functions > 0 else 0

                complexity_data[file_path] = {
                    "average_complexity": round(average_complexity, 2),
                    "functions": functions_data
                }

            except Exception:
                # If radon fails to parse the file, assign a default result
                complexity_data[file_path] = default_result

        return complexity_data