import os
import sys
# subprocess will not be imported here as we removed shell env var setting
from pathlib import Path # For home directory

# readline import for interactive experience (platform-dependent)
if sys.platform == "win32":
    import pyreadline3 as readline  # noqa: F401
else:
    import readline  # noqa: F401

import typer
from click import BadArgumentUsage
# Import click.Context and click.HelpFormatter for type hinting in custom Typer class
import click # Keep for Context, HelpFormatter, BadArgumentUsage
from typing_extensions import Annotated
from typing import Optional, List, TYPE_CHECKING

# --- Rich and Questionary for beautiful prompts ---
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.padding import Padding
    from rich.rule import Rule
    from rich.prompt import Confirm as RichConfirm # For a simple yes/no if Questionary fails
    import questionary
    from questionary import Style as QuestionaryStyle
except ImportError:
    # Use standard print before console is initialized if rich is missing
    print("Critical Error: Missing 'rich' or 'questionary' libraries. These are essential for Vigi's UI.")
    print("Please install them: pip install rich questionary")
    sys.exit(1)

# Initialize Rich console - This should be one of the first things
console = Console(highlight=False, log_time=False, log_path=False)

# --- python-dotenv for .env file handling ---
try:
    from dotenv import dotenv_values, set_key, find_dotenv
except ImportError:
    console.print("[bold red]Critical Error: Missing 'python-dotenv' library.[/bold red]")
    console.print("This is required for managing API keys.")
    console.print("Please install it: [cyan]pip install python-dotenv[/cyan]")
    sys.exit(1)


# Configuration
try:
    from .config import cfg , DESKTOP_VIGI_PATH
except ImportError:
    current_script_dir = Path(__file__).parent
    sys.path.insert(0, str(current_script_dir.parent))
    from vigi.config import cfg, DESKTOP_VIGI_PATH # type: ignore


# Forward declaration for type hinting
if TYPE_CHECKING:
    from .tools_and_personas import DigitalPersona


# --- API Key Management (Revised and Streamlined) ---
API_KEY_ENV_VAR = "GEMINI_API_KEY"
ENV_FILE_PATH = DESKTOP_VIGI_PATH / ".env"

def _print_api_key_banner(title: str, subtitle: Optional[str] = None, border_style: str = "cyan", icon: str = "🔑"):
    """Prints a consistent, styled banner for API key operations."""
    console.line()
    console.print(Panel(
        Padding(
            Text.assemble(
                (f"{icon} ", border_style),
                (title, f"bold {border_style}")
            ),
            (1, 2)
        ),
        subtitle=Text(subtitle, style="dim") if subtitle else "",
        border_style=border_style,
        expand=False,
        width=70
    ))
    console.line()

def _prompt_for_api_key_interactive() -> Optional[str]:
    """Prompts the user for their API key using a styled questionary prompt."""
    _print_api_key_banner("Vigi AI Key Setup", "Your Gemini API Key is needed for AI features.")
    try:
        custom_style = QuestionaryStyle([
            ('qmark', 'fg:#FFB300 bold'), # Amber qmark
            ('question', 'bold fg:#E0E0E0'),   # Light gray question
            ('answer', 'fg:#81D4FA bold'),    # Light blue answer
        ])
        api_key = questionary.text(
            "🔑 Please enter your Gemini API Key:",
            validate=lambda text: True if len(text.strip()) >= 10 else "API key seems too short. It should be at least 10 characters.",
            style=custom_style
        ).ask() # Removed qmark from text as it's in the style
        console.line()
        return api_key.strip() if api_key else None
    except Exception as e:
        console.print(Panel(
            Text.assemble(
                ("🚨 ", "bold red"),
                ("API Key Prompt Error\n\n", "bold red"),
                (f"An error occurred while trying to get your API key: {e}\n\n", "red"),
                ("You can set the ", "red"),
                (API_KEY_ENV_VAR, "bold red"),
                (" variable in the file:\n", "red"),
                (str(ENV_FILE_PATH), "underline red"),
                ("\nmanually.", "red")
            ),
            title="[bold red]Error[/bold red]", border_style="red", padding=(1,2)
        ))
        console.line()
        return None

def _save_api_key_to_vigi_env_file(api_key_value: str) -> None:
    """Saves the API key to Vigi's .env file."""
    try:
        DESKTOP_VIGI_PATH.mkdir(parents=True, exist_ok=True)
        set_key(dotenv_path=ENV_FILE_PATH, key_to_set=API_KEY_ENV_VAR, value_to_set=api_key_value, quote_mode="always")
        console.print(Panel(
            Text.assemble(
                ("💾 ", "green"),
                (f"{API_KEY_ENV_VAR} saved successfully to:\n", "green"),
                (str(ENV_FILE_PATH), "underline green")
            ),
            title="[bold green]Key Saved[/bold green]", border_style="green", padding=(1,1), width=70
        ))
    except Exception as e:
        console.print(Panel(
            Text.assemble(
                ("⚠️ ", "yellow"),
                (f"Failed to save {API_KEY_ENV_VAR} to {ENV_FILE_PATH}.\n\n", "yellow"),
                (f"Error: {e}\n\n", "yellow"),
                ("Please try adding the line manually:\n", "yellow"),
                (f'{API_KEY_ENV_VAR}="{api_key_value}"', "bold yellow")
            ),
            title="[bold yellow]Save Warning[/bold yellow]", border_style="yellow", padding=(1,2)
        ))
    console.line()


def ensure_api_key_is_set() -> bool:
    """
    Ensures GEMINI_API_KEY is available.
    Priority:
    1. Vigi's .env file (DESKTOP_VIGI_PATH/.env)
    2. System environment variable (os.getenv)
    3. Prompts user if not found, offering to save to Vigi's .env file.
    Returns True if the key is set for the current session, False otherwise.
    """
    # Attempt to load from Vigi's .env file first
    loaded_from_vigi_env = False
    if ENV_FILE_PATH.exists() and ENV_FILE_PATH.is_file():
        key_values_from_dotenv = dotenv_values(dotenv_path=ENV_FILE_PATH)
        api_key_from_dotenv = key_values_from_dotenv.get(API_KEY_ENV_VAR)
        if api_key_from_dotenv:
            os.environ[API_KEY_ENV_VAR] = api_key_from_dotenv # Set for current session
            _print_api_key_banner(
                f"{API_KEY_ENV_VAR} Loaded",
                f"Using API key from Vigi's .env file:\n{ENV_FILE_PATH}",
                border_style="green", icon="✅"
            )
            loaded_from_vigi_env = True
            return True
    elif ENV_FILE_PATH.exists() and not ENV_FILE_PATH.is_file():
         _print_api_key_banner(
            "Vigi .env Path Issue",
            f"Expected an .env file at '{ENV_FILE_PATH}', but found a directory.\n"
            "Please resolve this to use Vigi's .env for API key storage.",
            border_style="orange3", icon="⚠️"
        )

    # If not in Vigi's .env, check system environment
    api_key_from_os_env = os.getenv(API_KEY_ENV_VAR)
    if api_key_from_os_env:
        # If loaded from Vigi's .env, this won't be printed due to early return
        _print_api_key_banner(
            f"{API_KEY_ENV_VAR} Found",
            "Using API key from your system environment variables.",
            border_style="blue", icon="🌍"
        )
        return True

    # If still not found, prompt user
    _print_api_key_banner(
        f"{API_KEY_ENV_VAR} Not Found",
        f"The API key was not found in Vigi's .env file or system environment.\n"
        "It's required for Vigi's AI features.",
        border_style="orange3", icon="❓"
    )
    
    api_key_input = _prompt_for_api_key_interactive()

    if not api_key_input:
        _print_api_key_banner(
            "API Key Setup Cancelled",
            f"No API key provided. Vigi's AI features will not be available.\n"
            f"To use Vigi, please set {API_KEY_ENV_VAR} in:\n"
            f"1. {ENV_FILE_PATH}\n"
            f"2. Your system environment variables.",
            border_style="red", icon="❌"
        )
        return False

    os.environ[API_KEY_ENV_VAR] = api_key_input # Set for the current session
    _print_api_key_banner(
        f"{API_KEY_ENV_VAR} Set for Session",
        "The API key is active for this Vigi session.",
        border_style="green", icon="⏳"
    )

    # Offer to save to Vigi's .env file
    save_env_style = QuestionaryStyle([('qmark', 'fg:#A78BFA bold'), ('question', 'bold fg:#E0E0E0')])
    try:
        save_to_vigi_env_q = questionary.confirm(
            f"📝 Save this API key to Vigi's .env file ({ENV_FILE_PATH}) for future Vigi sessions?",
            default=True, auto_enter=False, style=save_env_style
        ).ask()
        
        if save_to_vigi_env_q is None:
             console.print(Panel(f"ℹ️ Save to Vigi's .env file choice cancelled.", title="[dim]Action Cancelled[/dim]", border_style="dim", padding=(0,1)))
             save_to_vigi_env_q = False

        if save_to_vigi_env_q:
            _save_api_key_to_vigi_env_file(api_key_input)
        else:
            console.print(Panel(
                Text.assemble(
                    ("ℹ️ API key not saved to Vigi's .env file.\n", "dim"),
                    ("It will need to be provided again in future Vigi startups if not set in system environment.", "dim")
                ),
                title="[dim]Information[/dim]", border_style="dim", padding=(0,1)
            ))
            console.line()

    except Exception:
        console.print("[bold orange3]Questionary prompt for .env save failed. Using simple confirmation.[/bold orange3]")
        if RichConfirm.ask(f"Save API key to {ENV_FILE_PATH} for Vigi?", default=True, console=console):
            _save_api_key_to_vigi_env_file(api_key_input)
        else:
            console.print(Panel(f"ℹ️ API key not saved to Vigi's .env file.", title="[dim]Information[/dim]", border_style="dim", padding=(0,1)))
            console.line()
            
    return True
# --- END API Key Management ---



# Wrapper for display_personas_entry_point to defer import
def display_personas_entry_point_wrapper(value: bool):
    if value:
        from .tools_and_personas import _display_personas_impl as display_personas_callback_internal
        display_personas_callback_internal(value)
        raise typer.Exit()
    return value


# Wrapper for display_persona_details_callback to defer import
def display_persona_details_callback_wrapper(value: Optional[str]):
    if value is not None:
        from .tools_and_personas import _display_persona_details_impl as display_persona_details_actual_callback
        display_persona_details_actual_callback(value)
        raise typer.Exit()
    return value

# Wrapper for ChatHandler.list_ids callback to defer import
def list_chats_callback_wrapper(value: bool):
    if value:
        from .chat_manage import ChatHandler
        ChatHandler.list_ids(value)
        raise typer.Exit()
    return value


class InteractiveHelpTyper(typer.Typer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        current_command_epilog = self.epilog
        if not (ctx.parent is None and current_command_epilog):
            if current_command_epilog:
                formatter.write_paragraph()
                formatter.write_text(current_command_epilog)
            return

        epilog_to_render = current_command_epilog
        if sys.stdin.isatty():
            try:
                decision_attr_name = '_show_examples_main_app_help_decision'
                if hasattr(ctx, decision_attr_name):
                    show_examples = getattr(ctx, decision_attr_name)
                else:
                    show_examples = questionary.confirm(
                        "Show command examples in help?",
                        default=True,
                        auto_enter=False,
                        kbi_msg="Example display choice cancelled. Defaulting to show."
                    ).ask()
                    if show_examples is None:
                        show_examples = True
                    setattr(ctx, decision_attr_name, show_examples)
                if not show_examples:
                    epilog_to_render = None
            except Exception:
                pass
        
        if epilog_to_render:
            formatter.write_paragraph()
            formatter.write_text(epilog_to_render)


app = InteractiveHelpTyper(rich_markup_mode="rich")

@app.callback(invoke_without_command=True)
def default_handler_main(
    ctx: typer.Context,
    prompt_args: Annotated[Optional[List[str]], typer.Argument(
        show_default=False,
        help="The prompt text. Can be entered as a single string or multiple words. Options like .dev, .talk should precede this.",
        metavar="[PROMPT_TEXT...]"
    )] = None,
    model: Annotated[str, typer.Option(
        help="LLM to use. Passed to developer/ch if .dev is used.",
        hidden=True,
    )] = cfg.get("DEFAULT_MODEL"),
    temperature: Annotated[float, typer.Option(
        min=0.0, max=2.0, help="Randomness of output.",
        hidden=True,
    )] = 0.0,
    top_p: Annotated[float, typer.Option(
        min=0.0, max=1.0, help="Limits highest probable tokens.",
        hidden=True,
    )] = 1.0,
    md: Annotated[bool, typer.Option(
        help="Prettify markdown output.",
        hidden=True,
    )] = (cfg.get("PRETTIFY_MARKDOWN") == "true"),
    shell: Annotated[bool, typer.Option(
        "--assist-shell",
        help="Generate/execute shell commands. (Assistance Options)",
        rich_help_panel="Assistance Options",
        hidden=True 
    )] = False,
    interaction: Annotated[bool, typer.Option(
        help="Interactive mode for shell assistance. (Assistance Options)",
        rich_help_panel="Assistance Options",
        hidden=True
    )] = (cfg.get("SHELL_INTERACTION") == "true"),
    describe_shell: Annotated[bool, typer.Option(
        "--describe-shell", "-d", help="Describe a shell command.", rich_help_panel="Assistance Options"
    )] = False,
    code: Annotated[bool, typer.Option(
        ".dev" ,
        help="Generate code with developer/ch. Use .talk for its chat mode.",
        rich_help_panel="Code Development Module",
    )] = False,
    shell_mode: Annotated[bool, typer.Option(
        ".shell",
        help="Invoke Vigi Shell: Interactive AI Shell, or single query processing.",
        rich_help_panel="Vigi Shell Module",
    )] = False,
    memshell_flag: Annotated[bool, typer.Option(
        ".memshell",
        help="Invoke Vigi Shell with session memory (interactive, retains context).",
        rich_help_panel="Vigi Shell Module",
    )] = False,
    devch_output_dir: Annotated[Optional[str], typer.Option(
        "--devch-output-dir",
        help="Base output directory for developer/ch (with .dev).",
        rich_help_panel="Code Development Module",
        hidden=True,
    )] = None,
    devch_debug: Annotated[bool, typer.Option(
        "--devch-debug",
        help="Enable debug logging for developer/ch (with .dev).",
        rich_help_panel="Code Development Module",
        hidden=True,
    )] = False,
    conversation: Annotated[bool, typer.Option(
        ".talk", "--conversation",
        help="Enable conversation. With .dev, enables developer/ch chat. Else, Vigi REPL/chat.",
        rich_help_panel="Persona and Chat Module",
    )] = False,
    docker: Annotated[bool, typer.Option(
        "--docker", help="Specialized assistance for Docker commands.", rich_help_panel="Docker Module",
    )] = False,
    functions: Annotated[bool, typer.Option(
        help="Allow AI to use predefined function calls.", rich_help_panel="Assistance Options",
    )] =True ,
    editor: Annotated[bool, typer.Option(
        help="Open $EDITOR to provide a prompt.",
        hidden=True,
        )] = False,
    cache: Annotated[bool, typer.Option(
        help="Cache completion results from AI.",
        hidden=True,
        )] = True,
    repl: Annotated[bool, typer.Option(
        ".convo", help="Start a REPL session (DEPRECATED, use .talk or --conversation).", rich_help_panel="Persona and Chat Module", hidden=True,
    )] = False,
    repl_id: Annotated[Optional[str], typer.Option(
        "--repl-id", help="Session ID for REPL/conversation (optional, cached if provided).", rich_help_panel="Persona and Chat Module",
        hidden=True,
    )] = None,
    show_chat_id: Annotated[Optional[str], typer.Option(
        "--show-chat", help="Show messages from a specific chat ID.", rich_help_panel="Persona and Chat Module",
        hidden=True,
    )] = None,
    list_chats_flag: Annotated[bool, typer.Option(
        "--list-chats", "-lc",
        help="List existing chat ids.",
        callback=list_chats_callback_wrapper, 
        rich_help_panel="Persona and Chat Module",
        is_eager=True,
        hidden=True,
    )] = False,
    select_persona_flag: Annotated[bool, typer.Option(
        ".prs", ".persona",
        help="Interactively select or create a persona, then starts a REPL session.",
        rich_help_panel="Persona and Chat Module",
        is_flag=True
    )] = False,
    show_role_trigger: Annotated[Optional[str], typer.Option(
        "--show-role",
        help="Show details of a specific persona: --show-role MyRoleName",
        callback=display_persona_details_callback_wrapper,
        rich_help_panel="Persona and Chat Module",
        is_eager=True,
    )] = None,
    display_personas_trigger: Annotated[bool, typer.Option(
        ".shpersonas", ".shprs",
        help="List all available personas.",
        callback=display_personas_entry_point_wrapper,
        rich_help_panel="Persona and Chat Module",
        is_eager=True
    )] = False,
    # --- Vigi Hub Options ---
    hub_mode: Annotated[bool, typer.Option(
        ".hub", help="Access the Vigi Community Hub.", rich_help_panel="Vigi Hub"
    )] = False,
    hub_list: Annotated[bool, typer.Option(
        ".list", help="List available resources from the Vigi Hub.", rich_help_panel="Vigi Hub"
    )] = False,
    hub_install: Annotated[Optional[str], typer.Option(
        ".install", help="Install a resource by its ID (e.g., 'author/tool_name').", rich_help_panel="Vigi Hub"
    )] = None,
    hub_install_persona: Annotated[bool, typer.Option(
        "--persona", help="Flag to indicate the resource to install is a persona.", rich_help_panel="Vigi Hub"
    )] = False
) -> None:

    if ctx.invoked_subcommand is not None:
        return

    # --- Hub Logic ---
    if hub_mode:
        from .hub_manager import HubManager
        hub_manager = HubManager()

        if hub_list:
            if hub_install:
                raise BadArgumentUsage("Cannot use .list and .install at the same time.")
            hub_manager.list_resources()
            raise typer.Exit()
        
        if hub_install:
            hub_manager.install_resource(resource_id=hub_install, is_persona=hub_install_persona)
            raise typer.Exit()
        
        # If just `.hub` is provided without a sub-command
        console.print("Vigi Hub: Please specify an action, e.g., [bold cyan].list[/bold cyan] or [bold cyan].install <ID>[/bold cyan].")
        raise typer.Exit()

    needs_ai_features = (code or shell_mode or memshell_flag or conversation or docker or 
                         select_persona_flag or (prompt_args and any(prompt_args))) 
    
    if needs_ai_features: 
        if not ensure_api_key_is_set(): # This now handles .env file internally
            # ensure_api_key_is_set() prints its own detailed error messages
            raise typer.Exit(code=1)
    
    stdin_content_str: Optional[str] = None
    if not sys.stdin.isatty():
        stdin_data_lines = []
        for line in sys.stdin:
            if "__sgpt__eof__" in line: 
                break
            stdin_data_lines.append(line)
        if stdin_data_lines:
            stdin_content_str = "".join(stdin_data_lines).strip()
        try: 
            if os.name == "posix":
                sys.stdin = open("/dev/tty", "r")
            elif os.name == "nt":
                sys.stdin = open("CONIN$", "r") 
        except OSError:
            pass

    cli_arg_prompt_str: Optional[str] = None
    if prompt_args: 
        processed_args = [str(arg) for arg in prompt_args if arg is not None]
        if processed_args:
            cli_arg_prompt_str = " ".join(processed_args).strip()
            if not cli_arg_prompt_str: 
                cli_arg_prompt_str = None
    
    effective_prompt: Optional[str] = None
    if stdin_content_str and cli_arg_prompt_str:
        effective_prompt = f"{stdin_content_str}\n\n{cli_arg_prompt_str}"
    elif stdin_content_str:
        effective_prompt = stdin_content_str
    elif cli_arg_prompt_str:
        effective_prompt = cli_arg_prompt_str

    if editor and not effective_prompt: 
        from .corefunctions import get_edited_prompt 
        effective_prompt = get_edited_prompt()

    role_class: Optional['DigitalPersona'] = None
    general_shell_assistance_flag = shell 

    vigi_main_conversation_mode = (conversation and not code) or \
                                  (repl and not code) 

    if select_persona_flag: 
        from .tools_and_personas import DigitalPersona 
        try:
            role_class = DigitalPersona.retrieve_persona()
        except InterruptedError: 
            typer.secho("Persona selection/creation was cancelled. Exiting.", fg=typer.colors.YELLOW)
            raise typer.Exit(code=0)
        except (BadArgumentUsage, RuntimeError) as e:
            typer.secho(f"Error during persona processing: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        
        if role_class:
            vigi_main_conversation_mode = True 
    else:
        from .tools_and_personas import DefaultPersonas, DigitalPersona 
        role_class = DefaultPersonas.determine_persona(general_shell_assistance_flag, describe_shell, code)

    if not role_class: 
        typer.secho("CRITICAL: Persona could not be determined. This indicates an issue with default persona logic.", fg=typer.colors.RED)
        raise typer.Exit(1) 

    if docker:
        from .docker_part.docker_main import docker_main 
        docker_main()
        raise typer.Exit()

    if memshell_flag: 
        from .shell_part.main import ai_shell_interactive 
        if effective_prompt:
            typer.secho(
                "Warning: .memshell is for interactive sessions; provided prompt ignored.",
                fg=typer.colors.YELLOW,
            )
        typer.echo("Starting Vigi Shell with session memory (.memshell)...")
        ai_shell_interactive() 
        raise typer.Exit() 

    if shell_mode: 
        from .shell_smart.shell_main import vigi_shell_entry_point as smart_vigi_shell_entry_point
        smart_vigi_shell_entry_point(initial_query=effective_prompt if effective_prompt else None)
        raise typer.Exit()

    if code: 
        from .developerch.main import main as developerch_main 
        dev_ch_conversation_mode = conversation 

        if repl and not dev_ch_conversation_mode: 
            raise BadArgumentUsage(
                "Cannot use .convo with .dev. Use '.dev .talk' for developer/ch chat."
            )

        original_argv = sys.argv[:]
        developerch_args = ['developerch_invoker'] 
        if effective_prompt:
             developerch_args.extend(['--prompt', effective_prompt])
        if model != cfg.get("DEFAULT_MODEL"): 
            developerch_args.extend(['--model', model])
        if devch_output_dir:
            developerch_args.extend(['--output_dir', devch_output_dir])
        if devch_debug:
            developerch_args.append('--debug') 
        if dev_ch_conversation_mode:
            developerch_args.append('--conversation')
        
        sys.argv = developerch_args 
        exit_code = 0
        try:
            developerch_main() 
        except SystemExit as e_sys: 
            exit_code = e_sys.code if isinstance(e_sys.code, int) else (0 if e_sys.code is None else 1)
        except Exception as e_exc:
            typer.secho(f"Error running developer/ch module: {e_exc}", file=sys.stderr, fg=typer.colors.RED)
            exit_code = 1
        finally:
            sys.argv = original_argv 
        raise typer.Exit(code=exit_code) 

    if show_chat_id: 
        from .chat_manage import ChatHandler 
        ChatHandler.show_messages(show_chat_id, md)
        raise typer.Exit() 
    
    function_schemas_repl = None
    function_schemas_single = None
    if functions: 
        from .tools_and_personas import collect_schemas 
        schemas = collect_schemas() or None 
        function_schemas_repl = schemas 
        function_schemas_single = schemas 

    if vigi_main_conversation_mode: 
        from .convo_manage import ReplHandler 
        if not effective_prompt and not repl_id and select_persona_flag : 
             typer.echo(f"Starting Vigi conversation with selected persona: {role_class.identifier}")
        
        ReplHandler(repl_id, role_class, md).handle(
            init_prompt=effective_prompt if effective_prompt else "", 
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas_repl, 
        )
        raise typer.Exit() 

    if not effective_prompt: 
        typer.secho("No prompt provided and no specific mode selected (e.g., .shell, .talk, .dev).", fg=typer.colors.YELLOW)
        console.line()
        typer.echo(ctx.get_help()) 
        raise typer.Exit(code=1)

    if general_shell_assistance_flag and describe_shell:
        raise BadArgumentUsage(
            "Cannot use general shell assistance (--assist-shell) and --describe-shell together."
        )
    
    if repl_id == ".dev": 
        raise BadArgumentUsage("Session ID for --repl-id cannot be '.dev'.")

    from .base_manage import DefaultHandler 
    full_completion = DefaultHandler(role_class, md).handle(
        prompt=effective_prompt, 
        model=model,
        temperature=temperature,
        top_p=top_p,
        caching=cache,
        functions=function_schemas_single 
    )

    active_shell_interaction_loop = general_shell_assistance_flag and interaction and full_completion

    while active_shell_interaction_loop:
        from click.types import Choice as ClickChoice 
        from .corefunctions import run_command 
        console.line()
        try:
            action_choices = [
                questionary.Choice(title="[E]xecute Command", value="e"),
                questionary.Choice(title="[A]bort", value="a"),
            ]
            default_action = "e" if cfg.get("DEFAULT_EXECUTE_SHELL_CMD") == "true" else "a"
            
            option_choice_q = questionary.select(
                "Choose action for generated shell command:",
                choices=action_choices,
                default=next((c for c in action_choices if c.value == default_action), None),
                style=QuestionaryStyle([('qmark', 'fg:#00FF00 bold'),('question', 'bold')]), 
                qmark="⚙️"
            ).ask()
            option_choice = option_choice_q if option_choice_q else default_action 
        except Exception: 
            console.print("[yellow]Questionary prompt failed, using basic prompt.[/yellow]")
            option_choice = typer.prompt(
                text="Choose action: [E]xecute, [A]bort",
                type=ClickChoice(("e", "a"), case_sensitive=False),
                default="e" if cfg.get("DEFAULT_EXECUTE_SHELL_CMD") == "true" else "a",
                show_choices=True, show_default=True,
            )
        console.line()
        
        if option_choice == "e":
            run_command(full_completion) 
            break 
        elif option_choice == "a":
            typer.secho("Shell command execution aborted by user.", fg=typer.colors.YELLOW)
            break

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred in main execution: {e}[/bold red]")
        sys.exit(1)