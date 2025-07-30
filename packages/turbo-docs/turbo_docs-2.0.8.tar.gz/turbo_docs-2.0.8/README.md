# turbo-docs

[![PyPI](https://img.shields.io/pypi/v/turbo-docs?color=blue)](https://pypi.org/project/turbo-docs/)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **turbo-docs**: AI-powered, automatic README.md generator for your code repository, powered by OpenAI.

---

## Table of Contents

- [What is turbo-docs?](#what-is-turbo-docs)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Supported Filetypes](#supported-filetypes)
- [Ignored Folders](#ignored-folders)
- [Configuration](#configuration)
- [Example Output](#example-output)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## What is turbo-docs?

**turbo-docs** is a command-line tool that uses OpenAI’s powerful LLMs to *automatically generate a comprehensive `README.md`* for your code project. It recursively analyzes your codebase, identifies important files, and crafts high-quality, context-aware project documentation—so you can focus on building.

---

## Features

- **Automatic README Generation:** Scans your code and produces a usable README.md using OpenAI.
- **Recursively Scans Your Codebase:** Finds source and config files, skipping irrelevant/large ones.
- **Smart Filtering:** Only includes meaningful files (by extension, size, and folder).
- **Chain-of-Thought Process:** Structures the README like an expert would think it through.
- **Streaming Generation:** Watch your README generated live as you run the tool.
- **Easy CLI Usage:** One simple command to generate documentation.
- **Safe:** Never includes sensitive environment files or your existing README.md.

---

## Installation

**Requirements:**
- Python **3.11** or newer
- [PDM](https://pdm.fming.dev/) for dependency management
- OpenAI API key

**Steps:**

1. **Clone or Download** this repository.

2. **Install dependencies**:
    ```bash
    pdm install
    ```

3. **Set your OpenAI API key** (required):
    - Add your API key to a `.env` file in your project root:
        ```
        OPENAI_API_KEY=sk-...
        ```
    - Or export it in your shell:
        ```bash
        export OPENAI_API_KEY=sk-...
        ```

4. **(Optional) Install CLI script globally:**
    ```bash
    pdm run pip install .
    ```

---

## Usage

From your project's root directory, **run:**

```bash
pdm run turbo-docs --readme
```

- This command will ingest your codebase, interact with OpenAI, and generate a `README.md` in the current directory.
- Alternatively, after pip installation, you can run:
    ```bash
    turbo-docs --readme
    ```

**Command-line options:**

- `--readme` &nbsp; Generate or overwrite the README.md for your repository.

---

## How It Works

1. **Recursively scans** the current directory for relevant files:
    - Skips ignored folders (see below).
    - Only includes files with allowed extensions.
    - Skips large files and files that are not text.
    - Ignores any existing `README.md`.

2. **Prepares the context**: Parses and combines relevant code/config into a single input.

3. **Invokes OpenAI LLM**:
    - Generates a detailed "chain-of-thought" for writing a great README.
    - Streams the final README content directly into `README.md`.

4. **Saves the generated README.md** for you to review, edit, or publish!

---

## Supported Filetypes

turbo-docs considers a broad range of files from various programming ecosystems. **Supported extensions include:**

- **Code:** `.py`, `.js`, `.ts`, `.tsx`, `.cpp`, `.java`, `.go`, `.rs`, `.rb`, `.php`, `.c`, `.cs`, `.swift`, `.kt`, `.scala`, `.dart`, `.lua`, `.r` etc.
- **Markup/Docs:** `.md`, `.mdx`, `.rst`, `.tex`, `.adoc`, `.org`, `.wiki`, `.textile`, etc.
- **Configs/Manifests:** `.json`, `.toml`, `.yaml`, `.yml`, `.ini`
- **Shell & Scripts:** `.sh`, `.bat`, `.cmd`, `.ps1`
- **Templates:** `.j2`, `.jinja`, `.tpl`, etc.

<details>
  <summary><strong>Full extension list</strong> (click to expand):</summary>

`.js`, `.jsx`, `.ts`, `.tsx`, `.vue`, `.svelte`, `.html`, `.css`, `.scss`, `.sass`, `.less`, `.py`, `.java`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.rb`, `.php`, `.scala`, `.kt`, `.kts`, `.groovy`, `.swift`, `.m`, `.h`, `.hpp`, `.cxx`, `.cc`, `.hh`, `.perl`, `.pl`, `.pm`, `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`, `.bat`, `.cmd`, `.toml`, `.ini`, `.json`, `.yaml`, `.yml`, `.j2`, `.jinja`, `.jinja2`, `.tmpl`, `.tpl`, `.md`, `.mdx`, `.rst`, `.tex`, `.adoc`, `.asciidoc`, `.wiki`, `.org`, `.pod`, `.rdoc`, `.textile`, `.creole`, `.dokuwiki`, `.mediawiki`, `.r`, `.lua`, `.dart`, `.elm`, `.ex`, `.exs`, `.erl`, `.hrl`, `.clj`, `.cls`, `.asm`, `.s`, `.nim`, `.cr`, `.ml`, `.mli`, `.fs`, `.fsx`
</details>

---

## Ignored Folders

turbo-docs intentionally *skips* standard folders that typically contain dependencies or build artifacts:

- `node_modules`
- `dist`
- `build`
- `public`
- `static`
- `templates`
- `vendor`
- `venv`
- `env`
- `cache`
- `tmp`
- `temp`

In addition, any folder or file starting with a dot (`.`) is ignored.

---

## Configuration

- **API Key:**  
  You must provide your `OPENAI_API_KEY` in your environment. Set it either in a `.env` file or export it using your shell, as shown in [Installation](#installation).

- **Customization:**  
  For now, turbo-docs has minimal CLI options (just `--readme`). Future versions may support more config options!

---

## Example Output

*Here’s an excerpt from a README generated by turbo-docs running on itself:*

```
# turbo-docs

turbo-docs is a command-line utility that generates high-quality README.md files for your code repository using OpenAI's LLMs. It recursively scans your codebase, selects important files by type and size, excludes irrelevant folders, and synthesizes a professional project overview auto-magically.

## Features

- Automatic README generation using AI
- Supports dozens of code, config, and markup file types
- Excludes large or generated files and folders
- CLI-driven, easy to use

## Installation

...
```

<sub>(Real output will be more complete—give it a try!)</sub>

---

## Troubleshooting

**Common Issues:**

- `OPENAI_API_KEY` not set:
    - Make sure your API key is in your `.env` or exported in your environment.
    - If you see an error like:  
      `Looks like you are missing the OPENAI_API_KEY environment variable.`  
      Follow the [Installation](#installation) instructions to set it.
- **Wrong Python version:** Python 3.11+ is required.
- **No README generated:** Ensure you are in your project root and that your code files use supported extensions.

If issues persist, check error messages printed by the tool.

---

## Contributing

Pull requests, issues, and suggestions are welcome!

- Author: [voynow](mailto:voynow99@gmail.com)
- Please ensure your code adheres to the style guide and is well-documented.
- Open a GitHub issue for any bug, or feature request.

---

## License

MIT License  
Copyright (c) voynow

---

Enjoy blazing-fast, AI-powered docs with turbo-docs! 🚀