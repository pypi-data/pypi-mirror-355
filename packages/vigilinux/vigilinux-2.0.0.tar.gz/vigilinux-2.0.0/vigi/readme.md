# Vigi - Your Versatile AI-Powered CLI Assistant 🤖✨

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/vigilinux.svg)](https://badge.fury.io/py/vigilinux) <!-- Assuming this will be the PyPI name -->
<!-- Add other badges like License (e.g., MIT) once decided -->

**Vigi** is an intelligent command-line assistant designed to supercharge your productivity. It leverages cutting-edge generative AI to understand natural language, helping you with shell commands, code generation, Docker operations, and much more, directly from your terminal.

**Core Capabilities:**

*   🗣️ **Natural Language Understanding:** Interact with Vigi using plain English.
*   🐚 **Advanced Shell Assistance:**
    *   Generate tailored shell commands for your OS (Linux, macOS, Windows) and shell (Bash, Zsh, PowerShell, CMD).
    *   Get concise explanations of complex commands.
    *   Execute commands safely with interactive prompts.
    *   🚀 **Vigi Shell (`.shell`, `.memshell`):** An intelligent, context-aware interactive shell environment powered by LangGraph. It can help with complex tasks, manage dependencies (with approval), and remember session context.
*   💻 **Code Generation & Development:**
    *   Generate Python code snippets on the fly.
    *   🤖 **DeveloperCH (`.dev`):** An AI software development agent that can plan, generate, and modify entire software projects based on your prompts.
*   🐳 **Docker Operations Simplified:**
    *   Interact with Docker using natural language (e.g., "pull ubuntu", "list my containers").
    *   Interactively create Dockerfiles and `.dockerignore` files for your projects.
    *   Search Docker Hub, inspect images for compatibility, pull images, and run containers.
*   🎭 **Customizable AI Personas:**
    *   Switch between pre-defined AI personas (General Assistant, Shell Command Generator, Code Generator, Shell Command Descriptor).
    *   Create and manage your own custom Vigi personas tailored to specific tasks or roles.
*   💬 **Interactive Chat Mode (`.talk`, `.prs`):**
    *   Engage in extended conversations with Vigi for general assistance or to work through complex problems.
    *   Supports Markdown rendering for rich AI responses.
    *   Execute generated Python code directly within the chat REPL when using the `Code Generator` persona.
*   🛠️ **Extensible Tooling:**
    *   Define custom Python functions (Procedures) that Vigi's AI can intelligently call to perform specific actions or retrieve information.
*   ⚙️ **Configuration & Caching:**
    *   Customize Vigi's behavior through a simple configuration file.
    *   Cache AI responses and chat history for improved speed and efficiency.

---

## 📋 Table of Contents

1.  [🚀 Features](#-features)
2.  [🧩 Core Modules](#-core-modules)
3.  [⚙️ Installation](#️-installation)
4.  [🔑 API Key Setup](#-api-key-setup)
5.  [🛠️ Configuration](#️-configuration)
6.  [💡 Usage](#-usage)
    *   [General CLI Invocation](#general-cli-invocation)
    *   [🐚 Shell Assistance](#-shell-assistance)
    *   [💻 Code Generation (DeveloperCH & Snippets)](#-code-generation-developerch--snippets)
    *   [🐳 Docker Module](#-docker-module)
    *   [🎭 Personas & Interactive Chat](#-personas--interactive-chat)
    *   [🛠️ Custom Procedures (Tool Calling)](#️-custom-procedures-tool-calling)
7.  [🌟 Module Deep Dives](#-module-deep-dives)
    *   [🚀 Vigi Shell (Shell Smart)](#-vigi-shell-shell-smart)
    *   [🐳 Docker Assistant Module](#-docker-assistant-module)
    *   [🤖 DeveloperCH Module](#-developerch-module)
8.  [🆘 Troubleshooting](#-troubleshooting)
9.  [🤝 Contributing (Placeholder)](#-contributing-placeholder)
10. [📜 License (Placeholder)](#-license-placeholder)

---

## 🚀 Features

*   **Shell Command Generation:**
    *   OS-specific commands (Linux, macOS, Windows).
    *   Shell-specific syntax (Bash, Zsh, PowerShell, CMD).
    *   Handles complex multi-step tasks by chaining commands (`&&`).
    *   Infers commands from vague requests, providing the most logical solution.
*   **Shell Command Description:**
    *   Provides concise explanations of shell commands, their arguments, and options.
*   **Python Code Generation:**
    *   Generates Python code snippets directly using the `Code Generator` persona.
    *   The **DeveloperCH** module (`.dev`) can generate entire project structures, including multiple files and directories.
*   **Interactive REPL/Chat:**
    *   Persistent chat sessions with history (`--repl-id`).
    *   Rich Markdown rendering for AI responses in the terminal.
    *   Execute generated Python code snippets directly within the REPL when using the `Code Generator` persona.
*   **Persona Management:**
    *   Pre-defined personas: `Vigi` (default), `Shell Command Generator`, `Shell Command Descriptor`, `Code Generator`.
    *   Interactively create new personas or select existing ones using the `.prs` command.
    *   Load personas from custom JSON files stored in `~/Desktop/VIGI/roles/`.
*   **Extensible Tooling (Procedures):**
    *   Define custom Python functions ("Procedures") in the `~/Desktop/VIGI/functions/` directory.
    *   Vigi's AI can understand when to use these tools and call them with appropriate arguments derived from your query.
*   **Docker Assistance (`--docker`):**
    *   Interactive Dockerfile and `.dockerignore` generation for Python, Node.js, Static HTML/CSS/JS, or generic projects.
    *   Search Docker Hub for images.
    *   Inspect image compatibility with your system architecture.
    *   Pull Docker images.
    *   Run existing local Docker images with custom options.
    *   List local images and containers (running or all).
*   **DeveloperCH - AI Software Developer (`.dev`):**
    *   Generates complete project structures from a high-level prompt.
    *   Plans development steps and file paths.
    *   Generates code for multiple files within the project.
    *   Engages in conversational interaction (`.dev .talk`) to modify code, answer questions about the codebase, or add features.
    *   Stores project context (plan, files, history) in a `.vigi_dev_meta` folder within the generated project.
*   **Vigi Shell - Intelligent Interactive Shell (`.shell`, `.memshell`):**
    *   An AI-powered interactive shell session.
    *   Context-aware command generation.
    *   Command explanation and safety validation before execution.
    *   Optional command execution with output summarization.
    *   Error handling and retry suggestions.
    *   Automatic dependency checking and (with approval) installation for required tools.
    *   Session memory for conversation history (with `.memshell` or within `.shell` sessions).
*   **Configuration & Caching:**
    *   Global configuration via `~/Desktop/VIGI/.vigirc`.
    *   Caching for chat history and AI model responses to improve speed and reduce API calls.
*   **User-Friendly CLI:**
    *   Rich formatting for enhanced readability using `rich`.
    *   Interactive prompts and selections using `questionary` and `typer`.
    *   Helpful command examples in `--help` output.

---

## 🧩 Core Modules

Vigi is composed of several key Python modules:

*   **`vigi.start`**: The main entry point for the CLI (`vg` command). Handles argument parsing and dispatches tasks to various handlers and sub-modules.
*   **`vigi.config`**: Manages application configuration, loading settings from `~/Desktop/VIGI/.vigirc` and environment variables.
*   **`vigi.tools_and_personas`**: Handles the loading, creation, and management of AI "Personas" and custom "Procedures" (functions for tool calling).
*   **`vigi.handler`, `vigi.base_manage`, `vigi.chat_manage`, `vigi.convo_manage`**: Core logic for interacting with the AI model, managing conversation history, and processing user prompts in different modes (single-shot, REPL/chat).
*   **`vigi.shell_smart`**: Implements the advanced AI-powered interactive shell (invoked via `.shell`). It uses LangGraph for its agentic behavior.
*   **`vigi.shell_part`**: Implements an older version of the interactive shell (invoked via `.memshell`).
*   **`vigi.docker_part`**: Provides Docker-related assistance (invoked via `--docker`). It features an interactive workflow for Docker tasks.
*   **`vigi.developerch`**: The AI software development agent (invoked via `.dev`) capable of creating and modifying entire software projects.
*   **`vigi.consoleUI`**: Manages the `rich`-based rendering of Markdown and text in the console for AI responses.
*   **`vigi.corefunctions`**: Contains utility functions like opening an editor for prompts and running shell commands.
*   **`vigi.hold_data`**: Implements a generic caching decorator for API responses.

---

## ⚙️ Installation

1.  **Prerequisites:**
    *   Python 3.9 or higher.
    *   `pip` (Python package installer).
    *   Docker Desktop (or Docker Engine on Linux) installed and running if you plan to use the Docker module or Vigi Shell's Docker-related features.

2.  **Install Vigi:**
    Open your terminal and run:
    ```bash
    pip install vigilinux
    ```
    This will install Vigi and its dependencies. The command to run Vigi will typically be `vg`.

3.  **Verify Installation:**
    After installation, you can verify it by running:
    ```bash
    vg --help
    ```

---

## 🔑 API Key Setup

Vigi requires API keys to communicate with generative AI models. These **must** be set as environment variables.

*   **Primary AI (Google Gemini):**
    This is used for most core features, including shell assistance, code generation, personas, and the DeveloperCH module.
    Set the `GEMINI_API_KEY` environment variable:
    ```bash
    export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    *(On Windows, use `set GEMINI_API_KEY=YOUR_GEMINI_API_KEY` for the current session, or set it permanently via System Properties.)*
    Vigi will prompt you to set this key on the first run if it's not found and AI features are invoked.

*   **Docker Module LLM (Optional - Groq):**
    The Docker module can use Gemini (default) or Groq. If you wish to use Groq for Docker assistance:
    Set the `GROQ_API_KEY` environment variable:
    ```bash
    export GROQ_API_KEY="YOUR_GROQ_API_KEY"
    ```
    *(The LLM provider for the Docker module can be selected when you first run `vg --docker`.)*



    ⚠️ **Important:** The `config.py` file contains a placeholder API key (`VIGI_API_KEY`). **This key is non-functional and should NOT be relied upon.** Always use your own API keys set via the environment variables mentioned above.

---

## 🛠️ Configuration

Vigi's behavior can be customized through a configuration file and environment variables.

*   **Configuration File:** `~/Desktop/VIGI/.vigirc`
    This file is automatically created on the first run if it doesn't exist. It stores key-value pairs for various settings.
*   **Project Directory:** Vigi creates a directory at `~/Desktop/VIGI/` to store:
    *   `roles/`: Custom personas in JSON format.
    *   `functions/`: Custom Python procedures (tools).
    *   `chat_cache/`: Chat history for persistent sessions.
    *   `cache/`: General API response cache.
*   **Environment Variables:** Many settings in `.vigirc` can be overridden by environment variables (e.g., `DEFAULT_MODEL`, `REQUEST_TIMEOUT`).

**Key Configuration Options (from `config.py` & `.vigirc`):**

| Setting                   | Environment Variable      | Default (`.vigirc`)                                  | Description                                                                          |
| ------------------------- | ------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Chat Cache Path           | `CHAT_CACHE_PATH`         | `~/Desktop/VIGI/chat_cache`                          | Path to store chat session histories.                                                |
| General Cache Path        | `CACHE_PATH`              | `~/Desktop/VIGI/cache`                               | Path for general AI response caching.                                                |
| Chat Cache Length         | `CHAT_CACHE_LENGTH`       | `100`                                                | Max number of message turns (user + assistant) to keep in cached chat history.     |
| Request Timeout           | `REQUEST_TIMEOUT`         | `350`                                                | Timeout in seconds for API requests to the AI model.                                 |
| Default AI Model          | `DEFAULT_MODEL`           | `gemini-1.5-flash`                                   | Default model for most AI interactions.                                              |
| Default User Color        | `DEFAULT_COLOR`           | `cyan`                                               | Default color for user input in `rich` console displays (used by some handlers).   |
| Persona Storage Path      | `ROLE_STORAGE_PATH`       | `~/Desktop/VIGI/roles`                               | Directory to store custom persona JSON files.                                        |
| Default Execute Shell Cmd | `DEFAULT_EXECUTE_SHELL_CMD` | `false`                                              | Default action in shell assistance mode ('e'xecute or 'a'bort). Deprecated by Vigi Shell. |
| Disable Streaming         | `DISABLE_STREAMING`       | `false`                                              | Set to `true` to disable streaming AI responses (receive full response at once).   |
| Code Theme (Rich)         | `CODE_THEME`              | `vigi-dark`                                          | Theme for code blocks in Markdown rendering.                                         |
| Custom Functions Path     | `VIGI_FUNCTIONS_PATH`     | `~/Desktop/VIGI/functions`                           | Path to load custom Python procedures from.                                          |
| Use Custom Functions      | `VIGI_USE_FUNCTIONS`      | `true`                                               | Whether to allow Vigi to use custom functions/tools.                                 |
| Show Functions Output     | `SHOW_FUNCTIONS_OUTPUT`   | `false`                                              | If `true`, displays the output of called custom functions directly in the chat.      |
| API Base URL              | `API_BASE_URL`            | `https://generativelanguage.googleapis.com/v1beta` | Base URL for the Google Gemini API.                                                |
| Prettify Markdown         | `PRETTIFY_MARKDOWN`       | `true`                                               | Enable `rich` library's Markdown rendering for AI responses.                       |
| OS Name Override          | `OS_NAME`                 | `auto`                                               | Manually set OS name (e.g., "Linux/Ubuntu 22.04"). `auto` for detection.           |
| Shell Name Override       | `SHELL_NAME`              | `auto`                                               | Manually set shell name (e.g., "bash"). `auto` for detection.                        |

---
## 💡 Usage Examples

### Using Vigi (`vg`) Command

Vigi can be invoked conveniently using the command `vg`. Below is a comprehensive guide to its various usage patterns:

### Basic Invocation

```bash
vg [OPTIONS] [PROMPT_TEXT...]
````

1) ### Chaining with Other Commands

Pass the output of another command directly into Vigi for interpretation or clarification:

```bash
ifconfig | vg [PROMPT_TEXT]
top -3 | vg "What's this?"
```

2) ### Interactive Modes

* **Standard Interactive Mode (Vigi Persona)**

  Engage in a standard interactive conversation:

  ```bash
  vg .talk
  ```

* **Standard Shell Mode**

  Start a basic shell interaction:

  ```bash
  vg .shell
  ```

  For a one-shot shell query:

  ```bash
  vg .shell [PROMPT_TEXT...]
  ```

* **Context-Aware Shell Mode (Requires `faiss-cpu`)**

  Start a context-aware shell session:

  ```bash
  vg .memshell
  ```

3) ### Command Descriptions

* Provide detailed descriptions of shell commands:

```bash
vg --describe-shell [SHELL_COMMAND]
OR vg -d [SHELL_COMMAND]
```

* Examples:

```bash
vg -d "find . -type f -name '*.py' -exec wc -l {} \;"

# With Markdown formatting
vg -d "docker run -it --rm -p 8080:80 nginx:latest" --md
```

4) ### Developer Assistance

* **Interactive Developer Mode**

  Engage Vigi's developer persona interactively:

  ```bash
  vg .dev .talk
  ```

* **Single-Shot Developer Queries**

  Quickly query Vigi for development assistance:

  ```bash
  vg .dev [PROMPT_TEXT]
  ```

5) ### AI Personas

* **Manage Custom AI Personas**

  ```bash
  vg .prs        # Use or create custom AI personas
  vg .shprs      # List available personas
  vg --show-role [PERSONA_NAME] # Show details of a specific persona
  ```

6) ### Tool Integration

* Explicitly instruct Vigi to leverage defined tools from the function storage path:

```bash
vg .talk --tools
```

6) ### Docker Mode

* Initiate Docker-focused interactions:

```bash
vg --docker
```











