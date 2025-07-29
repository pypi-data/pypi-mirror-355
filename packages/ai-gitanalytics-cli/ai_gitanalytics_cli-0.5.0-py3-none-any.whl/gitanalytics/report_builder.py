import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path

from .git_analyzer import Commit

class ReportBuilder:
    """
    Builds reports from analysis data in various formats.
    """
    def __init__(self, repo_path: str, start_date: str, end_date: str):
        """
        Initializes the ReportBuilder.
        """
        self.repo_path = os.path.abspath(repo_path)
        self.start_date = start_date or "First Commit"
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def _generate_report_filename(self, extension: str) -> str:
        """Creates a unique report filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"git_analytics_report_{timestamp}.{extension}"

    def _format_date(self, date_obj) -> str:
        """Helper to format date objects or date strings consistently."""
        if isinstance(date_obj, str):
            # Attempt to parse ISO format string
            return datetime.fromisoformat(date_obj).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        return "Unknown Date"

    def _prepare_context(
        self,
        categorized_commits: Dict[str, List[Dict]],
        executive_summary: str,
        author_summary: Optional[Dict] = None,
        code_health_summary: Optional[List[Dict]] = None,
        security_results: Optional[Dict] = None,
        trend_analysis: Optional[Dict] = None,
        baseline_comparison: Optional[Dict] = None,
        baseline_name: Optional[str] = None
    ) -> Dict:
        """Prepares the context dictionary for rendering templates."""
        # Process commits to ensure dates are strings for the template
        for category, results in categorized_commits.items():
            for result in results:
                # The commit data is now nested under the 'commit' key
                commit_data = result['commit']
                commit_data['date_str'] = self._format_date(commit_data['date'])

        return {
            "repo_path": self.repo_path,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "categorized_commits": categorized_commits,
            "executive_summary": executive_summary,
            "author_summary": author_summary,
            "code_health_summary": code_health_summary,
            "security_results": security_results,
            "trend_analysis": trend_analysis,
            "baseline_comparison": baseline_comparison,
            "baseline_name": baseline_name
        }

    def generate_markdown_report(
        self,
        categorized_commits: Dict[str, List[Dict]],
        executive_summary: str,
        author_summary: Optional[Dict] = None,
        code_health_summary: Optional[List[Dict]] = None,
        security_results: Optional[Dict] = None,
        trend_analysis: Optional[Dict] = None,
        baseline_comparison: Optional[Dict] = None,
        baseline_name: Optional[str] = None
    ) -> str:
        """
        Generates a Markdown report from the analyzed data.
        """
        context = self._prepare_context(
            categorized_commits,
            executive_summary,
            author_summary,
            code_health_summary,
            security_results,
            trend_analysis,
            baseline_comparison,
            baseline_name
        )
        template = self.env.get_template('report.md.j2')
        rendered_report = template.render(context)

        filename = self._generate_report_filename("md")
        with open(filename, "w") as f:
            f.write(rendered_report)
        return filename

    def generate_json_report(
        self,
        categorized_commits: Dict[str, List[Dict]],
        executive_summary: str,
        author_summary: Optional[Dict] = None,
        code_health_summary: Optional[List[Dict]] = None,
        security_results: Optional[Dict] = None,
        trend_analysis: Optional[Dict] = None,
        baseline_comparison: Optional[Dict] = None,
        baseline_name: Optional[str] = None
    ) -> str:
        """
        Generates a JSON report from the analyzed data.
        """
        context = self._prepare_context(
            categorized_commits,
            executive_summary,
            author_summary,
            code_health_summary,
            security_results,
            trend_analysis,
            baseline_comparison,
            baseline_name
        )

        # Convert datetime objects to strings
        for category, results in context['categorized_commits'].items():
            for result in results:
                commit_data = result['commit']
                commit_data['date'] = self._format_date(commit_data['date'])

        filename = self._generate_report_filename("json")
        with open(filename, "w") as f:
            json.dump(context, f, indent=2)
        return filename
