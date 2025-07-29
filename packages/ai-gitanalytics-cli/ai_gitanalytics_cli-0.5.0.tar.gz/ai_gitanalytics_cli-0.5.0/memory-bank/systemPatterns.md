# System Patterns: Git Analytics CLI

## System Architecture

The tool is designed with a modular architecture, separating concerns into distinct layers.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │   Core Engine    │    │  External APIs  │
│                 │    │                  │    │                 │
├─ Argument Parse │◄──►├─ Git Analyzer    │◄──►├─ OpenAI API     │
├─ Progress UI    │    ├─ AI Summarizer   │    ├─ Anthropic API  │
├─ Error Handler │    ├─ Report Builder  │    └─────────────────┘
└─────────────────┘    ├─ Analytics Track │
                       ├─ Cost Monitor    │    ┌─────────────────┐
┌─────────────────┐    ├─ Cache Manager   │    │  Data Storage   │
│   Output Layer  │    └──────────────────┘    │                 │
│                 │                             ├─ Local Cache    │
├─ Markdown Gen   │◄───────────────────────────├─ Usage Logs     │
├─ JSON Gen       │                             ├─ Config Files   │
├─ Progress Track │                             └─────────────────┘
└─────────────────┘
```

## Module Structure

The project will follow a standard Python source layout.

```
git-analytics/
├── src/
│   ├── gitanalytics/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── git_analyzer.py
│   │   ├── ai_summarizer.py
│   │   ├── model_selector.py
│   │   ├── report_builder.py
│   │   ├── analytics.py
│   │   ├── cost_monitor.py
│   │   ├── cache_manager.py
│   │   ├── config.py
│   │   └── utils.py
│   └── templates/
│       ├── report.md.j2
│       └── report.json.j2
├── tests/
├── docs/
├── requirements.txt
├── uv.lock
└── README.md
```
*Note: Using `requirements.txt` as requested for dependency management.*