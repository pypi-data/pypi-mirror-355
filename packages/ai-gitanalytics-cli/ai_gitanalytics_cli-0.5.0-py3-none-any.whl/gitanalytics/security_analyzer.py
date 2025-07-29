import os
import subprocess
import json
import sys
from typing import List, Dict, Any, Optional
from .language_detector import LanguageDetector

class SecurityAnalyzer:
    """
    Performs security analysis on a repository, selecting the appropriate tool
    based on the detected programming language.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.language_detector = LanguageDetector(repo_path)

    def analyze(self) -> Optional[Dict[str, Any]]:
        """
        Runs the security analysis.

        Returns:
            A dictionary containing the security analysis results, or None if
            the language is not supported.
        """
        language = self.language_detector.detect_language()

        if language == 'Python':
            return self._run_bandit()
        elif language in ['JavaScript', 'TypeScript']:
            return self._run_npm_audit()

        # In the future, other languages can be added here
        # e.g., if language == 'JavaScript': return self._run_npm_audit()

        return None

    def _run_bandit(self) -> Dict[str, Any]:
        """
        Runs bandit to perform static security analysis on Python code.
        """
        result_file = 'bandit_results.json'
        try:
            # Run bandit using the current python executable
            process = subprocess.run(
                [
                    sys.executable, '-m', 'bandit',
                    '-r', self.repo_path,
                    '-f', 'json',
                    '-o', result_file,
                    '-x', './.venv', # Exclude the virtual environment
                    '-q' # Run in quiet mode to reduce noise
                ],
                capture_output=True,
                text=True
            )

            with open(result_file, 'r') as f:
                results = json.load(f)

            os.remove(result_file)

            # Process results to group by severity
            findings = {"HIGH": [], "MEDIUM": [], "LOW": []}
            for issue in results.get('results', []):
                severity = issue.get('issue_severity')
                if severity in findings:
                    findings[severity].append({
                        "file": issue.get('filename'),
                        "line": issue.get('line_number'),
                        "issue": issue.get('issue_text')
                    })

            return {
                "tool": "bandit",
                "language": "Python",
                "findings": findings
            }

        except subprocess.CalledProcessError as e:
            # Capture and log the specific error from the subprocess
            error_message = (
                "Bandit analysis failed.\n"
                f"STDOUT: {e.stdout}\n"
                f"STDERR: {e.stderr}"
            )
            return {
                "tool": "bandit",
                "language": "Python",
                "findings": {},
                "error": error_message
            }
        except FileNotFoundError:
            return {
                "tool": "bandit",
                "language": "Python",
                "findings": {},
                "error": "Bandit command not found. Ensure it is installed in the current environment."
            }
        except Exception as e:
            # Catch other potential errors
            return {
                "tool": "bandit",
                "language": "Python",
                "findings": {},
                "error": f"An unexpected error occurred: {str(e)}"
            }

    def _run_npm_audit(self) -> Dict[str, Any]:
        """
        Runs `npm audit` to find vulnerabilities in a JavaScript/TypeScript project.
        """
        package_lock_path = os.path.join(self.repo_path, 'package-lock.json')
        if not os.path.exists(package_lock_path):
            return {
                "tool": "npm audit",
                "language": "JavaScript/TypeScript",
                "findings": {},
                "error": "package-lock.json not found. Cannot run npm audit."
            }

        try:
            # We run npm audit in the directory containing package-lock.json
            process = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            # npm audit exits with a non-zero code if vulnerabilities are found,
            # so we can't use check=True. We inspect the JSON output instead.
            results = json.loads(process.stdout)

            findings = {"HIGH": [], "MEDIUM": [], "LOW": []}
            vulnerabilities = results.get('vulnerabilities', {})

            for name, details in vulnerabilities.items():
                severity = details.get('severity').upper()
                if severity in findings:
                    findings[severity].append({
                        "file": "package-lock.json",
                        "line": f"dependency: {name}",
                        "issue": f"{details.get('via')[0]['title']} in `{name}`. More info: {details.get('via')[0]['url']}"
                    })

            return {
                "tool": "npm audit",
                "language": "JavaScript/TypeScript",
                "findings": findings
            }
        except FileNotFoundError:
            return {
                "tool": "npm audit",
                "language": "JavaScript/TypeScript",
                "findings": {},
                "error": "npm command not found. Please ensure Node.js and npm are installed."
            }
        except (json.JSONDecodeError, Exception) as e:
            return {
                "tool": "npm audit",
                "language": "JavaScript/TypeScript",
                "findings": {},
                "error": f"An unexpected error occurred during npm audit: {str(e)}"
            }