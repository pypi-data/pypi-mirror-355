# LLM CLI
A CLI for LLMs.
<p align="center">English | <a href="README.zh_CN.md">简体中文</a></p>

# Installation
**Before installing LLM CLI, you need to install [Python](https://www.python.org/downloads/).**

**You may need to configure your PATH environment variable.**

Install via `pip` (pip may not work by default on MacOS and Linux):
```bash
pip install llm_ya_cli
```

Install via [`pipx`](https://pipx.pypa.io/):
```bash
pipx install llm_ya_cli
```

Install via [`uv`](https://docs.astral.sh/uv/getting-started/installation/):
```bash
uv tool install llm_ya_cli
```

# Licenses
This project incorporates code from these following third-party projects:
- **[Rich](https://github.com/Textualize/rich)** 
([live_render.py](src/llm_cli/utils/live_render.py)) 
([LICENSE](licenses/LICENSE-Rich))
**Copyright (c) 2020 Will McGugan**
- **[Chatlas](https://github.com/posit-dev/chatlas)** 
([live_render.py](src/llm_cli/utils/live_render.py), modified from Rich's code) 
([LICENSE](licenses/LICENSE-Chatlas))
**Copyright (c) 2022-2025 Posit Software, PBC**
