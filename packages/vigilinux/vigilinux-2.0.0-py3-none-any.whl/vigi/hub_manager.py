import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import questionary
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import cfg

# --- Constants ---
HUB_REGISTRY_URL = "https://raw.githubusercontent.com/Muhammad-Subhan-Rauf/vigi-hub/main/registry.json"
LOCAL_FUNCTIONS_PATH = Path(cfg.get("VIGI_FUNCTIONS_PATH"))
LOCAL_ROLES_PATH = Path(cfg.get("ROLE_STORAGE_PATH"))

class HubManager:
    """Manages interactions with the Vigi Community Hub."""

    def __init__(self):
        self.console = Console()

    def _fetch_registry(self) -> Optional[Dict]:
        """Fetches and parses the registry.json file from the Hub."""
        self.console.print(f"Fetching registry from [link={HUB_REGISTRY_URL}]Vigi Hub[/link]...", style="cyan")
        try:
            response = requests.get(HUB_REGISTRY_URL, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.RequestException as e:
            self.console.print(f"[bold red]Error:[/bold red] Could not connect to the Vigi Hub. Please check your internet connection.", style="red")
            self.console.print(f"Details: {e}", style="dim red")
            return None
        except json.JSONDecodeError:
            self.console.print(f"[bold red]Error:[/bold red] The hub registry file seems to be malformed.", style="red")
            return None

    def list_resources(self):
        """Displays a list of all available tools and personas from the hub."""
        registry = self._fetch_registry()
        if not registry:
            return

        # --- List Tools ---
        tools = registry.get("tools", {})
        if tools:
            self.console.line()
            tool_table = Table(title="🛠️ Available Tools", show_header=True, header_style="bold magenta", expand=True)
            tool_table.add_column("ID", style="cyan", no_wrap=True)
            tool_table.add_column("Author", style="green")
            tool_table.add_column("Description", style="white")
            tool_table.add_column("Dependencies", style="yellow")

            for tool_id, meta in tools.items():
                deps = ", ".join(meta.get("dependencies", [])) or "None"
                tool_table.add_row(
                    tool_id,
                    meta.get("author", "N/A"),
                    meta.get("description", "No description provided."),
                    deps
                )
            self.console.print(tool_table)
        else:
            self.console.print("No community tools found in the registry.", style="yellow")

        # --- List Personas ---
        personas = registry.get("personas", {})
        if personas:
            self.console.line()
            persona_table = Table(title="👤 Available Personas", show_header=True, header_style="bold bright_blue", expand=True)
            persona_table.add_column("ID", style="cyan", no_wrap=True)
            persona_table.add_column("Author", style="green")
            persona_table.add_column("Description", style="white")

            for persona_id, meta in personas.items():
                persona_table.add_row(
                    persona_id,
                    meta.get("author", "N/A"),
                    meta.get("description", "No description provided."),
                )
            self.console.print(persona_table)
        else:
            self.console.print("No community personas found in the registry.", style="yellow")
        self.console.line()
        self.console.print("To install, use: [bold]vg .hub .install <ID>[/bold] (add [bold]--persona[/bold] for personas)")

    def _install_dependencies(self, dependencies: List[str]) -> bool:
        """Prompts the user to install a list of Python packages."""
        if not dependencies:
            return True # Success, nothing to do

        # *** FIXED: Create the multi-line dependency string first ***
        dependency_list_str = "  - " + "\n  - ".join(dependencies)

        self.console.print(Panel(
            Text.assemble(
                ("This tool requires the following packages:\n", "yellow"),
                (dependency_list_str, "bold cyan")
            ),
            title="[bold yellow]Dependencies Found[/bold yellow]",
            border_style="yellow",
            expand=False
        ))
        
        try:
            confirm = questionary.confirm(
                "Do you want to install them now using pip?", default=True
            ).ask()
        except Exception:
            confirm = True # Default to yes if questionary fails

        if not confirm:
            self.console.print("Dependency installation skipped by user.", style="yellow")
            return True # User skipped, not a failure

        with self.console.status("[bold green]Installing dependencies...", spinner="dots") as status:
            try:
                command = [sys.executable, "-m", "pip", "install"] + dependencies
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                self.console.log("Installation successful.")
                return True
            except subprocess.CalledProcessError as e:
                status.stop()
                self.console.print("[bold red]Error during dependency installation.[/bold red]")
                self.console.print("--- PIP OUTPUT ---", style="dim red")
                self.console.print(e.stdout)
                self.console.print(e.stderr, style="bold")
                self.console.print("------------------", style="dim red")
                return False

    def _download_and_save(self, url: str, destination_path: Path) -> bool:
        """Downloads a file from a URL and saves it to a local path."""
        with self.console.status(f"[bold green]Downloading [cyan]{destination_path.name}[/cyan]...", spinner="earth"):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                # Ensure parent directory exists
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                destination_path.write_text(response.text, encoding="utf-8")
                self.console.print(f"✅ Saved to [underline green]{destination_path}[/underline green]")
                return True
            except requests.exceptions.RequestException as e:
                self.console.print(f"[bold red]Error downloading file from {url}.[/bold red]")
                self.console.print(f"Details: {e}", style="dim red")
                return False
            except IOError as e:
                self.console.print(f"[bold red]Error saving file to {destination_path}.[/bold red]")
                self.console.print(f"Details: {e}", style="dim red")
                return False

    def install_resource(self, resource_id: str, is_persona: bool):
        """Installs a single tool or persona from the hub."""
        # Sanitize resource ID, e.g., remove .py/.json if present, as the key is the basename
        if resource_id.endswith(('.py', '.json')):
            resource_id_key = os.path.splitext(resource_id)[0]
        else:
            resource_id_key = resource_id

        registry = self._fetch_registry()
        if not registry:
            return

        resource_type = "personas" if is_persona else "tools"
        resource_repo = registry.get(resource_type, {})
        
        if resource_id_key not in resource_repo:
            self.console.print(f"[bold red]Error:[/bold red] Resource ID '{resource_id_key}' not found in the hub's {resource_type} list.", style="red")
            self.console.print("Use 'vg .hub .list' to see available resources.")
            return

        meta = resource_repo[resource_id_key]
        url = meta.get("url")
        if not url:
            self.console.print(f"[bold red]Error:[/bold red] Registry entry for '{resource_id_key}' is missing a URL.", style="red")
            return

        # Determine filename and destination path
        base_name = resource_id_key.split('/')[-1]
        if is_persona:
            filename = f"{base_name}.json"
            destination = LOCAL_ROLES_PATH / filename
        else:
            filename = f"{base_name}.py"
            destination = LOCAL_FUNCTIONS_PATH / filename

        # Download the file
        if not self._download_and_save(url, destination):
            return # Stop if download fails

        # Install dependencies for tools
        if not is_persona:
            dependencies = meta.get("dependencies", [])
            if not self._install_dependencies(dependencies):
                self.console.print("[bold yellow]Warning:[/bold yellow] Tool installed, but dependency installation failed. The tool may not work correctly.", style="yellow")
                return

        self.console.print(f"\n[bold green]Successfully installed '{resource_id_key}'.[/bold green]")
        if is_persona:
            self.console.print(f"You can now use it with: [cyan]vg .prs[/cyan] or [cyan]vg .talk --role \"{base_name}\"[/cyan]")
        else:
             self.console.print(f"It is now available for Vigi to use as a tool.")