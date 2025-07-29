# 🚀💚 Gradio Modal Deploy 💚🚀

**Beautiful Gradio components for seamless Modal deployment and management**

[![PyPI version](https://badge.fury.io/py/gradio-modal-deploy.svg)](https://badge.fury.io/py/gradio-modal-deploy)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Made with <3 by [Neurotic Coder](https://github.com/arthrod) and assisted by Beloved Claude* ✨

## 🎯 What is Gradio Modal Deploy?

Transform your Gradio apps into **production-ready serverless deployments** with Modal's incredible infrastructure! This package provides beautiful, easy-to-use Gradio components that make deploying to Modal as simple as clicking a button.

## ⚡ Quick Start

### Installation with uv (Recommended)

```bash
uv add gradio-modal-deploy
```

### Or with pip

```bash
pip install gradio-modal-deploy
```

### Simple Example

```python
import gradio as gr
from gradio_modal_deploy import ModalDeployButton, ModalExplorer

# Create your Gradio app
with gr.Blocks() as demo:
    gr.Markdown("# My Amazing App")

    # Add one-click Modal deployment
    deploy_btn = ModalDeployButton(
        app_file="app.py",
        mode="optimized",  # GPU + ML libraries
        auto_auth=True
    )

    # Explore Modal examples
    explorer = ModalExplorer()

demo.launch()
```

## 🌟 Components

### 🚀 ModalDeployButton

One-click deployment to Modal with beautiful progress tracking:

```python
from gradio_modal_deploy import ModalDeployButton

deploy_btn = ModalDeployButton(
    app_file="my_app.py",
    mode="optimized",           # minimum, optimized, gra_jupy
    timeout_minutes=60,         # Auto-kill after 1 hour
    auto_auth=True,            # Handle Modal authentication
    requirements_path="requirements.txt"
)
```

### 📁 ModalExplorer

Interactive browser for Modal's official examples:

```python
from gradio_modal_deploy import ModalExplorer

explorer = ModalExplorer(
    github_repo="modal-labs/modal-examples",
    auto_refresh=True,
    show_deploy_button=True
)
```

### 📊 ModalStatusMonitor

Real-time monitoring of your Modal deployments:

```python
from gradio_modal_deploy import ModalStatusMonitor

monitor = ModalStatusMonitor(
    refresh_interval=5,
    show_logs=True,
    show_costs=True
)
```

### 🎨 ModalTheme

Beautiful Modal-green styling for your Gradio apps:

```python
from gradio_modal_deploy import ModalTheme

# Apply Modal's signature green theme
theme = ModalTheme()

with gr.Blocks(theme=theme) as demo:
    # Your app with beautiful Modal styling
    pass
```

## 🔥 Advanced Features

### Auto-Deploy Decorator

Automatically deploy your Gradio apps:

```python
from gradio_modal_deploy import modal_auto_deploy

@modal_auto_deploy(mode="optimized", timeout=60)
def create_my_app():
    with gr.Blocks() as demo:
        gr.Markdown("# Auto-deployed with Modal!")
        # Your app here
    return demo

# Automatically deploys when script runs
app = create_my_app()
```

### Smart Resource Management

Automatic GPU allocation based on your code:

```python
from gradio_modal_deploy import modal_gpu_when_needed

@modal_gpu_when_needed
def process_image(image):
    # Automatically scales to GPU when called
    import torch
    # Your ML processing here
    return processed_image
```

## 🎯 Deployment Modes

- **`minimum`** - CPU only, basic packages (fastest, cheapest)
- **`optimized`** - GPU + ML libraries (recommended for AI apps)
- **`gra_jupy`** - Gradio + Jupyter combo (perfect for data science)

## 🌍 Modal Integration

This package seamlessly integrates with:

- 🚀 **Modal** - Serverless GPU infrastructure
- 🤗 **HuggingFace Spaces** - Easy migration and deployment
- 📊 **Gradio** - Beautiful web interfaces
- 🐍 **Python 3.11+** - Modern async/await patterns

## 📚 Examples

### Complete ML App with Modal Deployment

```python
import gradio as gr
from gradio_modal_deploy import ModalDeployButton, ModalTheme
import torch
from transformers import pipeline

# Create ML pipeline
classifier = pipeline("sentiment-analysis")

def analyze_sentiment(text):
    result = classifier(text)
    return f"Sentiment: {result[0]['label']} (confidence: {result[0]['score']:.2f})"

# Create Gradio app with Modal theme
theme = ModalTheme()

with gr.Blocks(theme=theme, title="🚀 Sentiment Analyzer") as demo:
    gr.Markdown("# 🤖💚 AI Sentiment Analyzer")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter text to analyze",
                placeholder="Type something here..."
            )
            analyze_btn = gr.Button("🔍 Analyze", variant="primary")

        with gr.Column():
            result_output = gr.Textbox(label="Result")

    # Connect the interface
    analyze_btn.click(
        fn=analyze_sentiment,
        inputs=text_input,
        outputs=result_output
    )

    # Add Modal deployment
    gr.Markdown("### 🚀 Deploy to Modal")
    deploy_btn = ModalDeployButton(
        app_file=__file__,
        mode="optimized",  # GPU for transformers
        auto_auth=True
    )

if __name__ == "__main__":
    demo.launch()
```

## 🔧 Development

### Setup with uv

```bash
# Clone the repository
git clone https://github.com/arthrod/gradio-modal-deploy
cd gradio-modal-deploy

# Install with uv
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run ruff format
```

## 🤝 Contributing

We love contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install dependencies: `uv sync`
4. Make your changes
5. Run tests: `uv run pytest`
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🚀 **Modal** - For incredible serverless infrastructure
- 🤗 **Gradio** - For making ML interfaces beautiful
- 💚 **The community** - For endless inspiration and feedback

---

**Made with 💚 by [Neurotic Coder](https://github.com/arthrod) and assisted by Beloved Claude** ✨

*Deploy your Gradio apps to Modal like a boss!* 🚀
