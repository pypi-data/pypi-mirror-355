import importlib.util
import sys
from abc import ABCMeta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .config import cfg

import questionary 
import typer 
from click import BadArgumentUsage
from distro import name as distro_name

import platform
import json
import os
from enum import Enum
from os import getenv, pathsep
from os.path import basename, join, exists

from .corefunctions import option_callback

import inspect

# --- Docstring Parsing ---
try:
    from docstring_parser import parse as parse_docstring
except ImportError:
    def parse_docstring(docstring_text: Optional[str]) -> Any: # type: ignore
        class MockDocstringParam:
            def __init__(self, arg_name: str, description: Optional[str]):
                self.arg_name = arg_name
                self.description = description
        class MockDocstring:
            def __init__(self, short_desc: Optional[str], long_desc: Optional[str], params: List[MockDocstringParam]):
                self.short_description = short_desc
                self.long_description = long_desc
                self.params = params
        
        raise ImportError(
            "The 'docstring-parser' library is required to automatically build procedure schemas from docstrings. "
            "Please install it by running: pip install docstring-parser"
        )

# --- Procedure handling ---
class Procedure:
    def __init__(self, file_path: str):
        module_id = Path(file_path).stem
        
        spec = importlib.util.spec_from_file_location(module_id, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec from {file_path}. File might not exist or be inaccessible.")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module 
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            if module_id in sys.modules:
                del sys.modules[module_id]
            raise ImportError(f"Failed to execute module {module_id} from {file_path}: {e}")

        self._action = self._find_procedure_function(module, module_id, file_path)
        self._schema = self._build_schema_from_function(self._action, func_name_override=module_id)
        self._id = self._schema["id"]

    @property
    def identifier(self) -> str:
        return self._id

    @property
    def schema_data(self) -> Dict[str, Any]:
        return self._schema

    @property
    def run(self) -> Callable[..., Any]:
        return self._action

    @classmethod
    def _find_procedure_function(cls, module: Any, expected_func_name: str, file_path: str) -> Callable[..., Any]:
        if not hasattr(module, expected_func_name):
            raise AttributeError(
                f"Procedure file '{file_path}' must define a function named '{expected_func_name}'."
            )
        
        func = getattr(module, expected_func_name)
        
        if not callable(func):
            raise TypeError(
                f"The attribute '{expected_func_name}' in '{file_path}' is not a callable function."
            )
        
        if getattr(func, '__module__', None) != module.__name__:
            # Silently pass to avoid cluttering the console with warnings about imported functions.
            pass
        return func

    @classmethod
    def _get_actual_type(cls, py_type: Any) -> Any:
        """Handles Optional[T] (as Union[T, NoneType]) and returns T, otherwise returns py_type."""
        if getattr(py_type, '__origin__', None) is Union:
            args = getattr(py_type, '__args__', ())
            non_none_type_args = [t for t in args if t is not type(None)]
            if len(non_none_type_args) == 1:
                return non_none_type_args[0]
        return py_type

    @classmethod
    def _map_type_to_json_schema(cls, py_type: Any) -> Dict[str, Any]:
        """Maps a Python type to a JSON schema type definition dictionary."""
        actual_type = cls._get_actual_type(py_type)
        
        if actual_type == str: return {"type": "string"}
        if actual_type == int: return {"type": "integer"}
        if actual_type == float: return {"type": "number"}
        if actual_type == bool: return {"type": "boolean"}
        
        origin_type = getattr(actual_type, '__origin__', None)
        if origin_type == list or actual_type == list:
            items_schema: Dict[str, Any] = {"type": "string"}
            if hasattr(actual_type, '__args__') and actual_type.__args__:
                items_schema = cls._map_type_to_json_schema(actual_type.__args__[0])
            return {"type": "array", "items": items_schema}
            
        if origin_type == dict or actual_type == dict:
            return {"type": "object"} 

        if inspect.isclass(actual_type) and issubclass(actual_type, Enum):
            enum_value_type = "string"
            try:
                first_member_value = next(iter(actual_type.__members__.values())).value
                if isinstance(first_member_value, int): enum_value_type = "integer"
                elif isinstance(first_member_value, float): enum_value_type = "number"
                elif isinstance(first_member_value, bool): enum_value_type = "boolean"
            except (StopIteration, AttributeError):
                pass
            
            return {"type": enum_value_type, "enum": [e.value for e in actual_type]}

        type_name = getattr(actual_type, '__name__', str(actual_type))
        return {"type": "string", "description": f"(Represents Python type: {type_name})"}

    @classmethod
    def _build_schema_from_function(cls, func: Callable[..., Any], func_name_override: Optional[str] = None) -> Dict[str, Any]:
        sig = inspect.signature(func)
        docstring_obj = parse_docstring(func.__doc__)

        func_id = func_name_override or func.__name__

        schema: Dict[str, Any] = {
            "id": func_id,
            "info": (docstring_obj.short_description or "").strip(),
            "args": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        if docstring_obj.long_description:
            schema["info"] = (schema["info"] + "\n\n" + docstring_obj.long_description.strip()).strip()
        if not schema["info"] and func_id:
            schema["info"] = f"Executes the '{func_id}' procedure."

        param_docs = {p.arg_name: (p.description or "").strip() for p in docstring_obj.params}

        for name, param in sig.parameters.items():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if name in ("self", "cls") and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                 pass

            param_schema_entry: Dict[str, Any] = {}
            
            if param.annotation is not inspect.Parameter.empty:
                param_schema_entry.update(cls._map_type_to_json_schema(param.annotation))
            elif param.default is not inspect.Parameter.empty:
                param_schema_entry.update(cls._map_type_to_json_schema(type(param.default)))
            else:
                param_schema_entry["type"] = "string" 

            param_description = param_docs.get(name, f"Parameter '{name}'.")
            
            if param.default is not inspect.Parameter.empty:
                default_value_str = f"{param.default!r}"
                if param_description.endswith('.'):
                    param_description = param_description[:-1] + f" (default: {default_value_str})."
                else:
                    param_description += f" (default: {default_value_str})."
            
            param_schema_entry["description"] = param_description.strip()
            schema["args"]["properties"][name] = param_schema_entry

            if param.default is inspect.Parameter.empty:
                if name not in schema["args"]["required"]:
                     schema["args"]["required"].append(name)
        
        if not schema["args"]["properties"]:
            pass

        if not schema["args"]["required"]:
            del schema["args"]["required"]

        return schema

procedure_dir_str = cfg.get("VIGI_FUNCTIONS_PATH")
procedure_dir = Path(procedure_dir_str)
procedure_dir.mkdir(parents=True, exist_ok=True)

procedures: List[Procedure] = []
for file in procedure_dir.glob("*.py"):
    if file.is_file() and not file.name.startswith("_"):
        try:
            procedures.append(Procedure(str(file)))
        except Exception as e:
            # Silently ignore procedures that fail to load. This prevents
            # cluttering the UI with error messages about broken or
            # incomplete function files.
            pass

def fetch_procedure(identifier: str) -> Callable[..., Any]:
    for proc in procedures:
        if proc.identifier == identifier:
            return proc.run
    raise ValueError(f"Procedure {identifier} not found")

def collect_schemas() -> List[Dict[str, Any]]:
    schemas = []
    for proc in procedures:
        function_schema = {
            "name": proc.schema_data["id"],
            "description": proc.schema_data.get("info", ""),
            "parameters": proc.schema_data.get("args", {"type": "object", "properties": {}}),
        }
        schemas.append({
            "type": "function",
            "function": function_schema,
        })
    return schemas

SHELL_PERSONA = """You are Vigi, a shell command generator specifically tailored for the {os} operating system using the {shell} shell.
Your sole responsibility is to provide only the necessary shell command to complete the user's request—nothing more, nothing less.
If the user's request is vague, you, as Vigi, will infer the most logical command that could solve the problem based on context.
Ensure that the command is accurate, syntactically correct, and executable in the provided shell.
If the task involves multiple steps, combine those steps into a single command using &&, ensuring each part is sequential and logical.
Do not include explanations, comments, or formatting like Markdown (e.g.,    or  bash ). Only provide the plain command text that can be directly run in the shell."""

DESCRIBE_SHELL_PERSONA = """You are Vigi, the concise shell command descriptor. 
When given a shell command, you will describe it in a terse, clear sentence, explaining what it does without unnecessary elaboration.
You will provide a brief explanation of each argument or option in the command, focusing only on the key details.
Keep your description to about 80 words and ensure clarity, simplicity, and accuracy.
Where appropriate, you may apply Markdown formatting to make the description or the command easier to understand, but avoid excessive formatting."""

CODE_PERSONA = f"""You are Vigi, a python code generator, focused solely on delivering the python code needed for the task at hand.
You provide the necessary python code in plain text format, ensuring that it's concise and executable, without offering any explanations.
If the user's request is vague, you will deduce the most logical approach to solve the problem, even when details are scarce.
Do not include any Markdown formatting—just the plain, runnable python code.
"""


DEFAULT_PERSONA = """You are Vigi, a versatile programming and system administration assistant, proficient in managing {os} using the {shell} shell.
Your purpose is to assist with tasks related to programming, shell commands, and system administration. If a user asks for something that requires a tool you have, do not try to answer it from your general knowledge; use the tool.
Describe the parameters for the tool accurately based on the user's query. As Vigi, you will provide concise responses, typically within 100 words, unless asked for more detail.
For every task, you will offer the most practical and logical solution, leveraging available functions wherever possible !
You will store information from the conversation as necessary and always strive to provide efficient, actionable responses.
When required, you may apply Markdown formatting to enhance the clarity of your responses."""

PERSONA_TEMPLATE = """You are a {role} and below a description of your capabilities/limitations : \n{persona}"""

DEFAULT_PERSONAS_MAPPING = {
    "DEFAULT": "Vigi",
    "SHELL": "Shell Command Generator",
    "DESCRIBE_SHELL": "Shell Command Descriptor",
    "CODE": "Code Generator",
}


def _get_os_identifier() -> str:
    if cfg.get("OS_NAME") != "auto":
        return cfg.get("OS_NAME")
    current_platform = platform.system()
    if current_platform == "Linux":
        return "Linux/" + distro_name(pretty=True)
    if current_platform == "Windows":
        return "Windows " + platform.release()
    if current_platform == "Darwin":
        return "Darwin/MacOS " + platform.mac_ver()[0]
    return current_platform

def _get_shell_identifier() -> str:
    if cfg.get("SHELL_NAME") != "auto":
        return cfg.get("SHELL_NAME")
    current_platform = platform.system()
    if current_platform in ("Windows", "nt"):
        is_powershell = len(getenv("PSModulePath", "").split(pathsep)) >= 3
        return "powershell.exe" if is_powershell else "cmd.exe"
    return basename(getenv("SHELL", "/bin/sh"))

def _get_persona_directory() -> str:
    persona_dir_str = cfg.get("ROLE_STORAGE_PATH")
    persona_dir_path = Path(persona_dir_str)
    persona_dir_path.mkdir(parents=True, exist_ok=True)
    return str(persona_dir_path)

def list_available_persona_names() -> List[str]:
    persona_dir_str = _get_persona_directory()
    persona_dir_path = Path(persona_dir_str)
    if not persona_dir_path.is_dir():
        return []
    persona_files = [f.stem for f in persona_dir_path.glob("*.json") if f.is_file()]
    return sorted(persona_files)

def generate_persona(persona_name: str, persona_blueprint: str, formatting_args: Optional[Dict[str, str]] = None, silent: bool = False) -> Dict[str, str]:
    if formatting_args:
        persona_blueprint = persona_blueprint.format(**formatting_args)
    persona_blueprint_escaped = persona_blueprint.replace('{', '{{').replace('}', '}}')
    try:
        persona_content = PERSONA_TEMPLATE.format(role=persona_name, persona=persona_blueprint_escaped)
    except KeyError as e:
        raise BadArgumentUsage(f"Formatting error for '{persona_name}'. Missing key: {e}.")
    persona_info = {"name": persona_name, "persona": persona_content}
    persona_file_path = join(_get_persona_directory(), f"{persona_name}.json")
    if exists(persona_file_path) and not silent:
        raise BadArgumentUsage(f"Persona '{persona_name}' already exists at {persona_file_path}")
    with open(persona_file_path, "w", encoding="utf-8") as f:
        json.dump(persona_info, f, indent=2)
    if not silent:
        typer.echo(f"Created persona '{persona_name}' ")
    return persona_info

def initialize_default_personas() -> None:
    persona_dir = _get_persona_directory()
    formatting_args = {"shell": _get_shell_identifier(), "os": _get_os_identifier()}
    default_blueprints = {
        DEFAULT_PERSONAS_MAPPING["DEFAULT"]: DEFAULT_PERSONA,
        DEFAULT_PERSONAS_MAPPING["SHELL"]: SHELL_PERSONA,
        DEFAULT_PERSONAS_MAPPING["DESCRIBE_SHELL"]: DESCRIBE_SHELL_PERSONA,
        DEFAULT_PERSONAS_MAPPING["CODE"]: CODE_PERSONA,
    }
    for name, blueprint in default_blueprints.items():
        persona_file = join(persona_dir, f"{name}.json")
        if not exists(persona_file):
            current_formatting_args = formatting_args if name != DEFAULT_PERSONAS_MAPPING["CODE"] else None
            DigitalPersona.generate_persona_instance(name, blueprint, current_formatting_args, silent=True)

import questionary
from questionary import Style
import json
from os.path import join, exists
from typing import Optional, Dict
import time

def fetch_persona(identifier: Optional[str] = None) -> Dict[str, str]:
    if identifier:
        persona_path = join(_get_persona_directory(), f"{identifier}.json")
        if not exists(persona_path):
            if identifier in DEFAULT_PERSONAS_MAPPING.values():
                initialize_default_personas()
                if not exists(persona_path):
                    raise BadArgumentUsage(f"Default persona '{identifier}' could not be initialized or found.")
            else:
                raise BadArgumentUsage(f"Persona '{identifier}' not found.")
        with open(persona_path, "r", encoding="utf-8") as f:
            return json.load(f)

    available_personas = list_available_persona_names()
    custom_style = Style([
        ('qmark', 'fg:#A78BFA bold'),
        ('question', 'bold fg:#E5E7EB'),
        ('selected', 'fg:#A78BFA bold'),
        ('pointer', 'fg:#A78BFA bold'),
        ('highlighted', 'fg:#A78BFA bold'),
        ('answer', 'fg:#A78BFA'),
        ('instruction', 'fg:#6B7280'),
    ])

    def draw_header(title: str, color: str = "bright_cyan") -> None:
        term_width = os.get_terminal_size().columns
        box_content_width = len(title) + 4
        min_box_width = 55
        box_width = max(box_content_width, min_box_width)
        left_padding = max((term_width - box_width) // 2, 0)
        
        padding = ' ' * left_padding
        border = f"{padding}╔{'═' * (box_width - 2)}╗"
        title_line = f"{padding}{title.center(box_width - 2)}"
        bottom_border = f"{padding}╚{'═' * (box_width - 2)}╝"
        
        typer.secho(border, fg=color)
        typer.secho(title_line, fg=color, bold=True)
        typer.secho(bottom_border, fg=color)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        draw_header(" 👤👤👤 Persona Creation and Selection 👤👤👤")
        choices = [
            questionary.Choice("🆕 Create New Persona", value="__create_new__"),
            questionary.Choice("🌌 Choose Existing Persona", value="__choose_existing__") if available_personas else None,
            questionary.Choice("🚪 Exit", value="__exit__")
        ]
        choices = [c for c in choices if c is not None]

        main_action = questionary.select(
            "\n",
            choices=choices,
            style=custom_style,
            qmark="  ",
            pointer="❯ ",
            use_arrow_keys=True
        ).ask()

        if not main_action or main_action == "__exit__":
            raise InterruptedError("Persona selection cancelled")

        if main_action == "__create_new__":
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
                draw_header("✨ CREATE CUSTOM VIGI PERSONA ✨", "bright_yellow")

                name_prompt = typer.style("\n  🚀 GIVE PERSONA NAME ", 
                                        fg=typer.colors.BRIGHT_YELLOW, 
                                        bold=True)
                persona_name = typer.prompt(name_prompt, prompt_suffix="\n  🔹 ").strip()
                if not persona_name:
                    raise typer.Abort()

                os.system('cls' if os.name == 'nt' else 'clear')
                draw_header(f"📝 GIVE BLUEPRINT FOR: {persona_name.upper()}", "bright_magenta")
                
                desc_prompt = (
                    typer.style("\n  🌈 PERSONA DEFINITION ", 
                              fg=typer.colors.BRIGHT_WHITE,
                              bold=True) +
                    typer.style("(describe capabilities)", 
                              fg=typer.colors.BLUE,
                              dim=True)
                )
                description = typer.prompt(desc_prompt, prompt_suffix="\n  ➤ ").strip()

                DigitalPersona.generate_persona_instance(persona_name, description)
                available_personas = list_available_persona_names()
                
                os.system('cls' if os.name == 'nt' else 'clear')
                draw_header(f"✅ SUCCESSFULLY CREATED PERSONA: {persona_name}", "green")
                time.sleep(1.5)

            except typer.Abort:
                pass
            except Exception as e:
                os.system('cls' if os.name == 'nt' else 'clear')
                draw_header("❌ PERSONA CREATION FAILED", "red")
                typer.secho(f"\nError: {str(e)}", fg=typer.colors.RED)
                time.sleep(2)
            continue

        if main_action == "__choose_existing__":
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                draw_header("📂 Available Personas")
                
                persona_choices = [
                    questionary.Choice(f"🌟 {persona}", value=persona)
                    for persona in available_personas
                ] + [
                    questionary.Choice("🔙 Back", value="__back__"),
                    questionary.Choice("🚪 Exit", value="__exit__")
                ]

                selected_persona = questionary.select(
                    "\n",
                    choices=persona_choices,
                    style=custom_style,
                    qmark="  ",
                    pointer="❯ ",
                    use_arrow_keys=True
                ).ask()

                if selected_persona == "__back__":
                    break
                if selected_persona == "__exit__":
                    raise InterruptedError("Persona selection cancelled")
                if selected_persona in available_personas:
                    return fetch_persona(selected_persona)

    raise BadArgumentUsage("No valid selection made")
class DigitalPersona:
    def __init__(self, identifier: str, persona_definition: str) -> None:
        self.identifier = identifier
        self.definition = persona_definition
      
    @classmethod
    def retrieve_persona(cls, identifier: Optional[str] = None) -> "DigitalPersona":
        persona_data = fetch_persona(identifier)
        return cls(persona_data["name"], persona_data["persona"])

    @classmethod
    def generate_persona_instance(cls, identifier: str, persona_definition: str, formatting_args: Optional[Dict[str, str]] = None, silent: bool = False) -> "DigitalPersona":
        persona_data = generate_persona(identifier, persona_definition, formatting_args, silent)
        return cls(persona_data["name"], persona_data["persona"])

    @classmethod
    def extract_persona_identifier(cls, initial_prompt: str) -> Optional[str]:
        if not initial_prompt: return None
        prompt_lines = initial_prompt.splitlines()
        if prompt_lines and "You are " in prompt_lines[0]:
            return prompt_lines[0].split("You are ", 1)[1].strip()
        return None

    def matches_persona(self, initial_prompt: str) -> bool:
        if not initial_prompt: return False
        extracted_id = self.extract_persona_identifier(initial_prompt)
        return extracted_id == self.identifier

class DefaultPersonas(Enum):
    DEFAULT = DEFAULT_PERSONAS_MAPPING["DEFAULT"]
    SHELL = DEFAULT_PERSONAS_MAPPING["SHELL"]
    DESCRIBE_SHELL = DEFAULT_PERSONAS_MAPPING["DESCRIBE_SHELL"]
    CODE = DEFAULT_PERSONAS_MAPPING["CODE"]

    @classmethod
    def determine_persona(cls, shell_flag: bool, describe_flag: bool, code_flag: bool) -> DigitalPersona:
        identifier = (
            cls.SHELL.value if shell_flag else
            cls.DESCRIBE_SHELL.value if describe_flag else
            cls.CODE.value if code_flag else
            cls.DEFAULT.value
        )
        return DigitalPersona.retrieve_persona(identifier)

    def get_persona(self) -> DigitalPersona:
        return DigitalPersona.retrieve_persona(self.value)

# CLI Functions for Typer Callbacks
def generate_persona_command(name_from_option: Optional[str]) -> None:
    invoked_by_user = any(arg in (".mkpr", ".mkpersona") for arg in sys.argv)
    if not invoked_by_user and name_from_option is None:
        return

    actual_persona_name_to_create = name_from_option
    if actual_persona_name_to_create is None:
        header = "✨ CREATE CUSTOM VIGI PERSONA ✨"
        box_width = max(50, len(header) + 8)
        
        typer.secho(f"\n╔{'═' * box_width}╗", fg=typer.colors.BRIGHT_CYAN)
        typer.secho(f"║{header.center(box_width)}", 
                   fg=typer.colors.BRIGHT_CYAN, bold=True)
        typer.secho(f"╚{'═' * box_width}╝", fg=typer.colors.BRIGHT_CYAN)
        
        actual_persona_name_to_create = typer.prompt(
            typer.style("\n  🚀 GIVE PERSONA NAME ", 
                       fg=typer.colors.BRIGHT_YELLOW, 
                       bold=True) ,
            prompt_suffix="\n  🔹 ",
            show_default=False
        )

        if not actual_persona_name_to_create:
            typer.secho("\n╔════════════════════════════════════════════╗", fg=typer.colors.RED)
            typer.secho("║ ‼️  ERROR: NAME CANNOT BE EMPTY ‼️  ║", 
                       fg=typer.colors.RED, 
                       bold=True)
            typer.secho("╚════════════════════════════════════════════╝", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    blueprint_header = f"📝 GIVE BLUEPRINT FOR: {actual_persona_name_to_create.upper()}"
    box_width = max(50, len(blueprint_header) + 8)
    
    typer.secho(f"\n╔{'═' * box_width}╗", fg=typer.colors.BRIGHT_MAGENTA)
    typer.secho(f"║{blueprint_header.center(box_width)}", 
               fg=typer.colors.BRIGHT_MAGENTA, 
               bold=True)
    typer.secho(f"╚{'═' * box_width}╝", fg=typer.colors.BRIGHT_MAGENTA)
    
    description = typer.prompt(
        typer.style("\n  🌈 PERSONA DEFINITION ", 
                   fg=typer.colors.BRIGHT_WHITE, 
                   bold=True) +
        typer.style("(describe limitaions/capabilities)", 
                   fg=typer.colors.BLUE, 
                   dim=True),
        prompt_suffix="\n  ➤ "
    )

    DigitalPersona.generate_persona_instance(actual_persona_name_to_create, description)
    
    raise typer.Exit()

def _display_personas_impl(value: bool) -> None:
    if not value: return
    persona_names = list_available_persona_names()
    if not persona_names:
        typer.echo("No personas found.")
    else:
        for name in persona_names:
            typer.echo(name)
    raise typer.Exit()

def _display_persona_details_impl(identifier_from_option: Optional[str]) -> None:
    invoked_by_user = "--show-role" in sys.argv
    
    if not identifier_from_option and not invoked_by_user:
        return 
    if not identifier_from_option and invoked_by_user:
        typer.secho("Please provide a persona name for --show-role.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    
    try:
        persona = DigitalPersona.retrieve_persona(identifier_from_option) 
        typer.echo(persona.definition)
    except BadArgumentUsage as e:
        typer.secho(str(e), fg=typer.colors.RED)
    raise typer.Exit()

display_personas_callback = option_callback(_display_personas_impl)

initialize_default_personas()