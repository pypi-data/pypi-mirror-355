from rich.console import Console
from rich.table import Table
from typing import Dict

# Pricing is per 1 million tokens (input/output)
# Source: https://openrouter.ai/models
MODEL_PRICING = {
    "qwen/qwen-2.5-72b-chat": {"input": 0.0, "output": 0.0}, # Free tier model
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Add other models as needed
}

class CostMonitor:
    """
    Tracks API token usage and estimates the cost of an analysis run.
    """
    def __init__(self):
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost = 0.0
        self.console = Console()

    def track_usage(self, model: str, usage):
        """
        Tracks the token usage and calculates the cost for a single API call.

        Args:
            model: The name of the model used.
            usage: The 'usage' object from the OpenAI API response.
        """
        if not usage:
            return

        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens

        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

        pricing = MODEL_PRICING.get(model)
        if pricing:
            input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
            output_cost = (completion_tokens / 1_000_000) * pricing["output"]
            self._total_cost += input_cost + output_cost

    def display_summary(self):
        """
        Displays a summary table of the total tokens used and the estimated cost.
        """
        table = Table(title="[bold]API Usage & Cost Analysis[/bold]", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")

        table.add_row("Prompt Tokens", f"{self._total_prompt_tokens:,}")
        table.add_row("Completion Tokens", f"{self._total_completion_tokens:,}")
        total_tokens = self._total_prompt_tokens + self._total_completion_tokens
        table.add_row("[bold]Total Tokens[/bold]", f"[bold]{total_tokens:,}[/bold]")
        table.add_row("[bold cyan]Estimated Cost[/bold cyan]", f"[bold cyan]${self._total_cost:.6f}[/bold cyan]")

        self.console.print(table)
        if self._total_cost == 0:
            self.console.print("[dim]Note: Analysis was run using a free-tier model, so no cost was incurred.[/dim]")
