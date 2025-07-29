import os
from collections import Counter
from typing import Optional, List

class LanguageDetector:
    """
    Detects the dominant programming language in a repository by analyzing
    project configuration files and file extensions.
    """
    # A simple mapping of common file extensions to languages
    EXTENSION_MAP = {
        # Python
        '.py': 'Python',
        # JavaScript / TypeScript
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
        # PHP
        '.php': 'PHP',
        # Java
        '.java': 'Java',
        # Ruby
        '.rb': 'Ruby',
        # Go
        '.go': 'Go',
        # C#
        '.cs': 'C#',
        # C/C++
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++',
    }

    # Mapping of project files to their likely language
    PROJECT_FILE_MAP = {
        'package.json': 'JavaScript',
        'requirements.txt': 'Python',
        'pyproject.toml': 'Python',
        'composer.json': 'PHP',
        'pom.xml': 'Java',
        'build.gradle': 'Java',
        'Gemfile': 'Ruby',
        'go.mod': 'Go',
    }

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect_language(self) -> Optional[str]:
        """
        Scans the repository and returns the most common programming language.
        It first checks for language-specific project files, then falls back
        to counting file extensions.
        """
        # 1. Check for project-specific files first
        for file, language in self.PROJECT_FILE_MAP.items():
            if os.path.exists(os.path.join(self.repo_path, file)):
                # If it's a JS project, distinguish between JS and TS
                if language == 'JavaScript':
                    return self._distinguish_js_vs_ts()
                return language

        # 2. If no project files found, fall back to file extension counting
        return self._detect_by_extension()

    def _distinguish_js_vs_ts(self) -> str:
        """
        If a package.json is found, determines whether TypeScript or
        JavaScript is dominant by comparing file counts.
        """
        extensions = self._get_all_extensions()
        ts_count = extensions.count('.ts') + extensions.count('.tsx')
        js_count = extensions.count('.js') + extensions.count('.jsx')
        return 'TypeScript' if ts_count > js_count else 'JavaScript'

    def _get_all_extensions(self) -> List[str]:
        """Scans the repo and returns a list of all found file extensions."""
        file_extensions = []
        for root, _, files in os.walk(self.repo_path):
            if '.git' in root.split(os.sep) or 'node_modules' in root.split(os.sep):
                continue

            for file in files:
                _, extension = os.path.splitext(file)
                if extension in self.EXTENSION_MAP:
                    file_extensions.append(extension)
        return file_extensions

    def _detect_by_extension(self) -> Optional[str]:
        """Counts file extensions to determine the dominant language."""
        file_extensions = self._get_all_extensions()
        if not file_extensions:
            return None

        extension_counts = Counter(file_extensions)
        most_common_extension = extension_counts.most_common(1)[0][0]
        return self.EXTENSION_MAP.get(most_common_extension)