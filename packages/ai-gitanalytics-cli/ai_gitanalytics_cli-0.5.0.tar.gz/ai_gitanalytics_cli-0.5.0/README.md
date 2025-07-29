# Git Analytics CLI

[![Tests](https://github.com/your-username/your-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/your-repo/actions)
[![PyPI version](https://badge.fury.io/py/gitanalytics.svg)](https://badge.fury.io/py/gitanalytics)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Git Analytics** is a powerful, AI-driven command-line tool that transforms your Git repository history into insightful, easy-to-read reports. It intelligently summarizes commits, groups them by theme, and provides high-level executive summaries, helping you understand project progress at a glance.

---

## Features

-   **🤖 AI-Powered Summaries:** Uses advanced AI models to generate detailed, code-aware summaries for each commit.
-   **🧩 Thematic Analysis:** Automatically categorizes commits into themes like `Features`, `Bug Fixes`, `Documentation`, and `Refactoring`.
-   **📄 Executive Summaries:** Generates a high-level, multi-sentence summary of the entire analysis period, perfect for reports and stakeholder updates.
-   **📊 Contributor Analysis:** Generate reports summarizing work by author to see who is contributing what.
-   **🩺 Code Health Insights:** Identify high-churn files and analyze their complexity to flag potential technical debt.
-   **🌿 Branch Selection:** Analyze any branch in your repository, not just the one you have checked out, using the `--branch` option.
-   **⚡️ Smart Caching:** Caches results to provide near-instantaneous reports on subsequent runs and to minimize API calls.
-   **💰 Cost Monitoring:** Tracks API token usage and provides an estimated cost for each analysis run, giving you full visibility.
-   **📝 Multiple Formats:** Generate reports in both Markdown and JSON formats.

## Installation

This project is managed with `uv`, a fast and modern Python package manager.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/gitanalytics.git
    cd gitanalytics
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the package:**
    ```bash
    uv pip install -e .
    ```
    The tool is now available as the `gitanalytics` command.

## Configuration

The tool requires an API key from an OpenAI-compatible service like OpenRouter.

1.  **Create a `.env` file** in the root of the project by copying the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** and add your API key:
    ```
    # .env
    OPENROUTER_API_KEY="your-secret-key-goes-here"
    OPENROUTER_MODEL_NAME="qwen/qwen-2.5-72b-chat"
    ```

## Usage

The main command is `analyze`. It analyzes the repository in the current directory by default.

```bash
gitanalytics analyze [OPTIONS] [REPO_PATH]
```

### Examples

-   **Analyze the current repository:**
    ```bash
    gitanalytics analyze
    ```

-   **Analyze a specific repository path:**
    ```bash
    gitanalytics analyze /path/to/your/repo
    ```

-   **Analyze a specific branch:**
    ```bash
    gitanalytics analyze --branch feature/new-login
    ```

-   **Analyze commits within a date range:**
    ```bash
    gitanalytics analyze --start-date 2023-01-01 --end-date 2023-01-31
    ```

-   **Generate a JSON report:**
    ```bash
    gitanalytics analyze --output json
    ```

-   **Force a fresh analysis by ignoring the cache:**
    ```bash
    gitanalytics analyze --no-cache
    ```

-   **Generate a report summarized by author:**
    ```bash
    gitanalytics analyze --by-author
    ```

-   **Include a code health summary in the report:**
    ```bash
    gitanalytics analyze --code-health
    ```

## Development

To set up a development environment with all testing dependencies, run:

```bash
uv pip install -e ".[dev]"
```

To run the automated test suite:

```bash
pytest
```