import openai
import json
import os
from typing import List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .git_analyzer import Commit
from .config import settings
from .cache_manager import CacheManager
from .cost_monitor import CostMonitor

# Initialize a Rich Console for beautiful output
console = Console()

# Define categories with descriptions to guide the AI
CATEGORIES_WITH_DESC = {
    "Features": "New user-facing features or major enhancements.",
    "Bug Fixes": "Fixing a bug, crash, or an issue in the code.",
    "Documentation": "Changes to README, guides, or code comments.",
    "Code Refactoring": "Improving code structure without changing its external behavior.",
    "Tests": "Adding or improving automated tests.",
    "Build System": "Changes to build scripts, CI/CD, or dependencies.",
    "Performance Improvements": "Code changes that specifically improve performance.",
    "Chores": "Routine tasks, maintenance, setup, or other non-functional changes."
}
CATEGORIES = list(CATEGORIES_WITH_DESC.keys())

class AISummarizer:
    """
    Handles interaction with the AI model for summarization and classification.
    """
    def __init__(self, cache_manager: CacheManager, cost_monitor: CostMonitor):
        """
        Initializes the AISummarizer.
        """
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        self.model = settings.AI_MODEL
        self.cache_manager = cache_manager
        self.cost_monitor = cost_monitor

        if not self.client.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")
        if not self.model:
            raise ValueError("OPENROUTER_MODEL_NAME environment variable not set.")

    def summarize_and_classify_commits(self, commits: List[Commit]) -> List[Dict[str, Any]]:
        """
        Generates a summary and classification for a list of commits.
        It uses a cache to avoid re-processing commits.

        Args:
            commits: A list of Commit objects.

        Returns:
            A list of dictionaries, where each dictionary contains the commit hash,
            category, summary, and original commit object.
        """
        cached_results = []
        commits_to_process = []

        for commit in commits:
            cached = self.cache_manager.get(commit.commit_hash)
            if cached:
                cached_results.append(cached)
            else:
                commits_to_process.append(commit)

        if cached_results:
            console.print(f"Found {len(cached_results)} summaries in cache.")

        if not commits_to_process:
            return cached_results

        console.print(f"🤖 Processing {len(commits_to_process)} commits with AI...")

        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Summarizing...", total=len(commits_to_process))

            for commit in commits_to_process:
                try:
                    max_diff_length = 4000
                    truncated_diff = commit.diff[:max_diff_length]

                    prompt = f"""
                    Analyze the git commit message and code diff below.

                    **Your Tasks:**
                    1.  **Summarize:** Write a detailed, one-sentence summary. The summary MUST explain the change's purpose and impact, focusing on WHAT was changed and WHY.
                    2.  **Classify:** Choose ONE category for the commit from the list provided.

                    **Category Definitions:**
                    {json.dumps(CATEGORIES_WITH_DESC, indent=2)}

                    **Output Format:**
                    You MUST respond with a single, valid JSON object with two keys: "summary" (string) and "category" (string).

                    **Commit Data:**

                    Commit Message:
                    ---
                    {commit.message}
                    ---

                    Code Diff:
                    ---
                    {truncated_diff}
                    ---
                    """
                    response = self.client.chat.completions.create(
                        model=self.model,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": "You are an expert software engineer who provides detailed, code-aware summaries and accurate classifications of git commits. You must respond with a valid JSON object."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.1, # Reduced for more deterministic output
                        max_tokens=250,  # Increased for potentially longer summaries
                    )
                    self.cost_monitor.track_usage(self.model, response.usage)

                    response_data = json.loads(response.choices[0].message.content)
                    summary = response_data.get("summary", "No summary provided.")
                    category = response_data.get("category", "Chores")

                    # Ensure the AI returns a valid category
                    if category not in CATEGORIES:
                        category = "Chores" # Default to Chores if AI hallucinates a category

                    # Add original commit data to the result
                    result_data = {
                        "commit_hash": commit.commit_hash,
                        "category": category,
                        "summary": summary,
                        "commit": commit.model_dump(mode='json')
                    }
                    results.append(result_data)
                    self.cache_manager.set(commit.commit_hash, result_data)

                except (openai.APIError, json.JSONDecodeError) as e:
                    console.print(f"[bold red]Error processing commit {commit.commit_hash[:7]}:[/] {e}")
                    results.append({'commit': commit, 'summary': 'Error processing commit.', 'category': 'Chores'})

                progress.update(task, advance=1)

        console.print(f"   - Processed {len(commits_to_process)} commits.")
        return cached_results + results

    def generate_executive_summary(self, commit_summaries: List[str]) -> str:
        """
        Generates a high-level executive summary from a list of commit summaries.
        """
        console.print(f"\n[bold yellow]✨ Generating high-level executive summary...[/bold yellow]")

        summaries_text = "\n".join(f"- {s}" for s in commit_summaries)
        prompt = f"""
        Based on the following list of commit summaries, please provide a high-level,
        three-sentence executive summary.

        Commit Summaries:
        ---
        {summaries_text}
        ---

        Executive Summary (3 sentences):
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a CTO who provides high-level summaries of development progress."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=200,
            )
            self.cost_monitor.track_usage(self.model, response.usage)
            executive_summary = response.choices[0].message.content.strip()
            console.print("   - [green]Executive summary created.[/]")
            return executive_summary
        except openai.APIError as e:
            console.print(f"[bold red]Error during executive summary generation:[/] {e}")
            return "Could not generate executive summary due to an API error."
