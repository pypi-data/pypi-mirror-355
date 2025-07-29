# 🚀 modal-for-noobs

**Async-first, idiot-proof Gradio deployment CLI for Modal**

Deploy your Gradio apps to Modal with zero configuration. Perfect for noobs who just want things to work! 🎯

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## ✨ Features

- 🚀 **Zero-config deployment** - Just point at your Gradio app and go!
- ⚡ **--time-to-get-serious** - Migrate HuggingFace Spaces to Modal in seconds
- 🔄 **Async-first** - Built with modern Python async/await patterns using uvloop
- 🎯 **Three modes**: Minimum (CPU), Optimized (GPU + ML), Gra-Jupy (Jupyter + Gradio)
- 🔐 **Auto-authentication** - Handles Modal setup automatically
- 🪝 **Smart detection** - Finds your Gradio interface automatically
- 📦 **Dependency magic** - Auto-installs requirements from HF Spaces or drop folder
- 🧙‍♂️ **Interactive wizard** - Step-by-step deployment guidance
- 🥛 **Log milking** - Beautiful log viewing with --milk-logs
- 💀 **Deployment killer** - Easy cleanup with --kill-a-deployment
- 🌐 **Modal Examples Explorer** - Browse and deploy Modal's example gallery
- 💚 **Beautiful UI** - Modal's signature green theme throughout
- 🇧🇷 **Modo brasileiro** - Brazilian Portuguese support with --br-huehuehue

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and install
git clone https://github.com/arthrod/modal-for-noobs.git
cd modal-for-noobs
uv sync

# Or install directly (future)
pip install modal-for-noobs
```

### 2. Deploy Your Gradio App

```bash
# 🚀 SUPER EASY MODE - Just use our launcher scripts!

# Unix/Linux/macOS
./mn.sh app.py                    # Quick deploy (CPU)
./mn.sh app.py --optimized        # GPU + ML libraries
./mn.sh                           # Wizard mode (default)

# Windows
mn.bat app.py                     # Quick deploy (CPU)
mn.bat app.py --optimized         # GPU + ML libraries
mn.bat                            # Wizard mode (default)

# 💡 Install permanent 'mn' alias to use from anywhere!
./mn.sh --install-alias           # Unix/Linux/macOS
mn.bat --install-alias            # Windows

# Then just use 'mn' from anywhere:
mn app.py --optimized
mn --milk-logs                    # View deployment logs

# Alternative: Direct CLI usage (if installed via pip)
modal-for-noobs deploy my_app.py --dry-run
modal-for-noobs deploy my_app.py --wizard          # Interactive wizard
modal-for-noobs deploy my_app.py --gra-jupy        # Jupyter + Gradio combo

# Configuration commands
modal-for-noobs config               # Show configuration (new command)
modal-for-noobs config-info          # Legacy alias (backward compatible)

# MCP Server for IDE integration
modal-for-noobs mcp                  # Start MCP server on port 8000
modal-for-noobs mcp --port 9000      # Use custom port
```

## 📖 Detailed Examples

### 🎯 Simple Gradio App
Create a file `my_app.py`:
```python
import gradio as gr

def greet(name):
    return f"Hello {name}! 🚀"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    demo.launch()
```

Deploy it:
```bash
./mn.sh my_app.py --optimized
```

### 🧠 ML Model App with Custom Requirements
1. Create `drop-ur-precious-stuff-here/requirements.txt`:
```
transformers==4.35.0
torch>=2.0.0
accelerate
```

2. Create your ML app:
```python
import gradio as gr
from transformers import pipeline

# The wizard will automatically detect and include your requirements!
classifier = pipeline("sentiment-analysis")

def analyze_sentiment(text):
    result = classifier(text)
    return f"Sentiment: {result[0]['label']} ({result[0]['score']:.2f})"

demo = gr.Interface(
    fn=analyze_sentiment,
    inputs="text",
    outputs="text",
    title="🧠 Sentiment Analysis with Modal-for-noobs!"
)

if __name__ == "__main__":
    demo.launch()
```

3. Deploy with wizard:
```bash
./mn.sh ml_app.py --wizard
```

### 🇧🇷 Modo Brasileiro (Brazilian Mode)
```bash
./mn.sh meu_app.py --optimized --br-huehuehue
# Outputs everything in Portuguese with Brazilian humor! 😄
```

## 🛠️ Advanced Commands

### 🥛 Milk the Logs (View Deployment Logs)
```bash
mn --milk-logs                           # List all apps
mn --milk-logs my-app                    # View logs for specific app
mn --milk-logs my-app --follow           # Follow logs in real-time
mn --milk-logs my-app --br-huehuehue     # Brazilian mode logs! 🇧🇷
```

### 💀 Kill Deployments
```bash
mn --kill-a-deployment                   # List active deployments
mn --kill-a-deployment my-app-id         # Kill specific deployment
mn --kill-a-deployment --br-huehuehue    # Brazilian terminator mode! 💀
```

### 🔍 Sanity Check
```bash
mn --sanity-check                        # Check what's deployed
mn --sanity-check --br-huehuehue         # Brazilian sanity check! 🧠
```

### 💪 Time to Get SERIOUS! (HuggingFace Migration)

```bash
# The nuclear option - migrate HuggingFace Spaces! 🚀
modal-for-noobs time-to-get-serious https://huggingface.co/spaces/user/space-name

# With dry run (see what happens first)
modal-for-noobs time-to-get-serious https://huggingface.co/spaces/user/space-name --dry-run
```

### 4. Authentication (auto-setup!)

```bash
# If no Modal keys found, it automatically starts auth setup!
# But you can also manually trigger it:
modal-for-noobs auth
```

### CLI Commands

- `deploy` - deploy a Gradio app
- `mn` - quick deploy alias for `deploy`
- `time-to-get-serious` - migrate a HuggingFace Space
- `auth` - configure Modal credentials
- `kill-a-deployment` - stop a running deployment
- `sanity-check` - list active deployments
- `config` - show configuration info
- `mcp` - start a local MCP server for Claude, Cursor, Roo and VSCode

The MCP server exposes several core RPC methods:

- `list_tools`
- `call_tool`
- `list_resources`
- `read_resource`
- `list_prompts`
- `get_prompt`

## 🛠️ Development

### Adding Dependencies

```bash
uv add requests              # Add runtime dependency
uv add pytest --dev         # Add development dependency
```

### Code Quality

```bash
uv run ruff check           # Lint code
uv run ruff format          # Format code
uv run mypy src/            # Type check
uv run pytest              # Run tests
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- Trailing whitespace removal
- YAML/TOML/JSON validation
- Ruff linting and formatting
- MyPy type checking
- Bandit security checks

## 👥 Contributing

- 🍴 Fork the repository
- 🌿 Create your feature branch (git checkout -b feature/amazing-feature)
- 💾 Commit your changes (git commit -m 'Add some amazing feature')
- 🚢 Push to the branch (git push origin feature/amazing-feature)
- 🔍 Open a Pull Request

## ⚠️ Trusted publishing failure

That's good news!

You are not able to publish to PyPI unless you have registered your project
on PyPI. You get the following message:

```bash
Trusted publishing exchange failure:

Token request failed: the server refused the request for
the following reasons:

invalid-publisher: valid token, but no corresponding
publisher (All lookup strategies exhausted)
This generally indicates a trusted publisher
configuration error, but could
also indicate an internal error on GitHub or PyPI's part.

The claims rendered below are for debugging purposes only.
You should not
use them to configure a trusted publisher unless they
already match your expectations.
```

Please register your repository. The 'release.yml' flow is
publishing from the 'release' environment. Once you have
registered your new repo it should all work.

---

## 💚 Credits

**Made with <3 by [Neurotic Coder](https://github.com/arthrod) and assisted by Beloved Claude** ✨

*This project represents the beautiful chaos of neurotic coding meets AI assistance - resulting in something absolutely AMAZING!* 🚀💚
