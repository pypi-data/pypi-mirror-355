import click
import sys
from rich.console import Console
from collections import defaultdict
from datetime import datetime
from .git_analyzer import GitAnalyzer
from .ai_summarizer import AISummarizer
from .report_builder import ReportBuilder
from .cache_manager import CacheManager
from .cost_monitor import CostMonitor
from .complexity_analyzer import ComplexityAnalyzer
from .security_analyzer import SecurityAnalyzer
import git

# Initialize a Rich Console for beautiful output
console = Console()

def run_analysis(repo_path, branch, start_date, end_date, output, no_cache, by_author, code_health, trend_analysis, security, baseline_name):
    """Core logic for the analysis, separated for clarity and testability."""
    console.print(f"[bold green]🚀 Starting analysis for repository:[/] [cyan]{repo_path}[/]")
    if branch:
        console.print(f"   - [bold]Branch:[/] {branch}")
    console.print(f"   - [bold]Date Range:[/] {start_date or 'First Commit'} to {end_date or 'Latest Commit'}")
    console.print(f"   - [bold]Output Format:[/] {output}")

    cache_manager = CacheManager(repo_path)
    cost_monitor = CostMonitor()
    if no_cache:
        cache_manager.clear()
        console.print("\n[yellow]Cache has been cleared for this run.[/yellow]")

    try:
        analyzer = GitAnalyzer(repo_path)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        console.print(f"[bold red]Error: {repo_path} is not a valid Git repository.[/]")
        sys.exit(1)

    # --- Historical Trend Analysis ---
    trend_data = None
    baseline_comparison = None
    if trend_analysis:
        console.print("\n[bold yellow]📈 Analyzing historical trends...[/bold yellow]")

        # Collect current metrics
        current_metrics = analyzer.collect_historical_metrics(branch)

        # Get trend analysis
        trend_data = analyzer.historical_metrics.get_trend_analysis(
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None
        )

        # Get baseline comparison if specified
        if baseline_name:
            baseline_comparison = analyzer.historical_metrics.compare_with_baseline(baseline_name)

        console.print("   - [green]Historical trend analysis complete.[/]")

    # --- Code Health Analysis ---
    code_health_summary = None
    if code_health:
        console.print("\n[bold yellow]🩺 Analyzing code health...[/bold yellow]")
        churn_data = analyzer.calculate_churn(branch, start_date, end_date)

        # Get top 5 most changed files
        top_churn_files = sorted(churn_data.items(), key=lambda item: item[1], reverse=True)[:5]

        if top_churn_files:
            complexity_analyzer = ComplexityAnalyzer()
            file_paths_to_analyze = [item[0] for item in top_churn_files]
            complexity_data = complexity_analyzer.analyze_files(repo_path, file_paths_to_analyze)

            # Combine churn and complexity data
            code_health_summary = []
            for file_path, churn_count in top_churn_files:
                # The complexity_data for a file now contains the detailed structure
                file_complexity_data = complexity_data.get(file_path, {"average_complexity": 0, "functions": []})
                code_health_summary.append({
                    "file_path": file_path,
                    "churn_count": churn_count,
                    "complexity": file_complexity_data
                })
            console.print("   - [green]Code health analysis complete.[/]")
        else:
            console.print("   - [yellow]No Python file changes found to analyze for code health.[/]")

    # --- Security Analysis ---
    security_results = None
    if security:
        console.print("\n[bold yellow]🛡️  Performing security analysis...[/bold yellow]")
        security_analyzer = SecurityAnalyzer(repo_path)
        security_results = security_analyzer.analyze()

        # --- DEBUG PRINT ---
        console.print("[bold cyan]-- DEBUG: Security Results from Analyzer --[/]")
        console.print(security_results)
        console.print("[bold cyan]-- END DEBUG --[/]")

        if security_results and security_results.get("error"):
            console.print(f"   - [bold red]Error:[/] {security_results['error']}")
        elif security_results:
            console.print(f"   - [green]Security analysis complete (using {security_results['tool']}).[/]")
        else:
            console.print("   - [yellow]Skipped security analysis: unsupported language or no findings.[/yellow]")

    commits = analyzer.get_commits(branch, start_date, end_date)

    if not commits:
        console.print("\n[yellow]No commits found for the specified criteria.[/yellow]")
        sys.exit(0)

    console.print(f"\n[bold green]✅ Found {len(commits)} commits.[/bold green]")

    summarizer = AISummarizer(cache_manager, cost_monitor)
    analysis_results = summarizer.summarize_and_classify_commits(commits)

    if not analysis_results:
        console.print("\n[yellow]Could not generate analysis. This may be due to an API error or empty commits.[/yellow]")
        return

    console.print("\n[bold yellow]📊 Categorizing results...[/bold yellow]")
    categorized_commits = defaultdict(list)
    for result in analysis_results:
        categorized_commits[result['category']].append(result)

    sorted_categorized_commits = dict(sorted(categorized_commits.items()))
    console.print("   - [green]Categorization complete.[/]")

    all_summaries = [result['summary'] for result in analysis_results]
    executive_summary = summarizer.generate_executive_summary(all_summaries)

    author_summary = None
    if by_author:
        console.print("\n[bold yellow]📊 Generating contributor summary...[/bold yellow]")
        author_summary = defaultdict(lambda: defaultdict(int))
        for result in analysis_results:
            author = result['commit']['author_name']
            category = result['category']
            author_summary[author][category] += 1
        console.print("   - [green]Contributor summary complete.[/]")

    builder = ReportBuilder(repo_path, start_date, end_date)
    if output == 'markdown':
        report_file = builder.generate_markdown_report(
            sorted_categorized_commits,
            executive_summary,
            author_summary,
            code_health_summary,
            security_results,
            trend_analysis=trend_data,
            baseline_comparison=baseline_comparison,
            baseline_name=baseline_name
        )
    else:
        report_file = builder.generate_json_report(
            sorted_categorized_commits,
            executive_summary,
            author_summary,
            code_health_summary,
            security_results,
            trend_analysis=trend_data,
            baseline_comparison=baseline_comparison,
            baseline_name=baseline_name
        )

    console.print(f"\n[bold green]✅ Report successfully generated![/bold green]")
    console.print(f"   - [bold]File:[/] {report_file}")

    cost_monitor.display_summary()

@click.group()
def cli():
    """Git Analytics CLI - Analyze your Git repository with AI-powered insights."""
    pass

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--branch', help='Branch to analyze (defaults to current branch)')
@click.option('--start-date', help='Start date for analysis (YYYY-MM-DD)')
@click.option('--end-date', help='End date for analysis (YYYY-MM-DD)')
@click.option('--output', type=click.Choice(['markdown', 'json']), default='markdown', help='Output format')
@click.option('--no-cache', is_flag=True, help='Disable caching of AI results')
@click.option('--no-by-author', is_flag=True, help='Disable contributor summary')
@click.option('--no-code-health', is_flag=True, help='Disable code health analysis')
@click.option('--no-trend-analysis', is_flag=True, help='Disable historical trend analysis')
@click.option('--no-security', is_flag=True, help='Disable security analysis')
@click.option('--baseline', 'baseline_name', help='Compare with a specific baseline')
def analyze(repo_path, branch, start_date, end_date, output, no_cache, no_by_author, no_code_health, no_trend_analysis, no_security, baseline_name):
    """Analyze a Git repository and generate insights."""
    # If no specific analysis is disabled, run all by default.
    # The logic inside run_analysis will check the boolean flags.
    run_analysis(
        repo_path,
        branch,
        start_date,
        end_date,
        output,
        no_cache,
        not no_by_author,  # Invert the logic
        not no_code_health, # Invert the logic
        not no_trend_analysis, # Invert the logic
        not no_security, # Invert the logic
        baseline_name
    )

@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.argument('name')
@click.argument('commit_hash')
def set_baseline(repo_path, name, commit_hash):
    """Set a baseline for historical trend analysis using a specific commit."""
    try:
        analyzer = GitAnalyzer(repo_path)
        analyzer.set_milestone_baseline(name, commit_hash)
        console.print(f"[bold green]✅ Successfully set baseline '{name}' at commit {commit_hash}[/]")
    except Exception as e:
        console.print(f"[bold red]Error setting baseline: {e}[/]")
        sys.exit(1)

def main():
    """Entry point for CLI and test runner compatibility."""
    cli()

if __name__ == '__main__':
    main()
