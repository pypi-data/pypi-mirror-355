# Tech Context: Git Analytics CLI

## Core Technologies

- **Language:** Python 3.9+
- **Package Manager:** `uv`
- **Virtual Environment:** Managed by `uv venv`

## Core Dependencies

The project relies on the following key Python libraries, managed in `requirements.txt`:

- `click`: For building the command-line interface.
- `gitpython`: For programmatic interaction with Git repositories.
- `openai`: As the client for the OpenRouter API (which is OpenAI-compatible).
- `jinja2`: For rendering the final reports from templates.
- `rich`: For creating beautiful and informative terminal UIs.
- `pydantic`: For data validation and settings management.
- `requests`: For any direct HTTP calls if needed.
- `psutil`: For gathering system performance metrics.

## AI Model Strategy

- **Integration:** All AI calls will be routed through OpenRouter to allow for flexible model selection.
- **Free Tier:** Will utilize high-quality free models like Qwen2.5-72B and Gemini Flash 1.5.
- **Paid Tier:** Will provide access to more powerful or cost-effective models like GPT-4o-mini and Claude 3 Haiku.

## Development Setup

1.  Clone the repository.
2.  Install `uv` using `curl -LsSf https://astral.sh/uv/install.sh | sh`.
3.  Create the virtual environment: `uv venv`.
4.  Activate the environment: `source .venv/bin/activate`.
5.  Install dependencies: `uv pip install -r requirements.txt`.