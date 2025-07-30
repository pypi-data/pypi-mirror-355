######################################################################
#                                                                    #
#               Engineered for GitHub: naumanAhmed3                  #
#                                                                    #
#     <<<<< AI System Instruction & Example Formulator >>>>>         #
#                                                                    #
######################################################################
"""
Responsible for constructing the structured prompts and example dialogues
fed to the Generative AI for shell instruction generation tasks.
It defines the expected JSON output formats and provides few-shot learning examples.
"""

from datetime import datetime

class SystemInstructionBuilder:
    """
    Constructs and manages templates for AI system instructions and few-shot examples,
    specifically for generating shell instructions based on user requests.
    It defines the JSON schemas for valid responses and error indications from the AI.
    """
    DETAILED_RESPONSE_JSON_SCHEMA = """
{
"input": "<user input>",
"error": 0,
"commands": [
{
"seq": <Order of Command>,
"cmd_to_execute": "<commands and arguments to execute>",
"cmd_explanations": ["<explanation of command 1>", "<explanation of command 2>", ...],
"arg_explanations": {"<arg1>": "<explanation of arg1>", "<arg2>": "<explanation of argument 2>", ...}
},
{
"seq": <Order of Command>,
"cmd_to_execute": "<commands and arguments to execute>",
"cmd_explanations": ["<explanation of command 1>", "<explantion of command 2>", ...],
"arg_explanations": {"<arg1>": "<explanation of arg1>", "<arg2>": "<explanation of argument 2>", ...}
}
]
}
"""

    CONDENSED_RESPONSE_JSON_SCHEMA = """
{
"commands": ["<commands and arguments to execute>", "<commands and arguments to execute>", ...]
}
"""
    INVALID_REQUEST_JSON_RESPONSE = """{"input": "<user input>", "error": 1}"""
    INVALID_REQUEST_CONDENSED_JSON_RESPONSE = """{"error": 1}"""

    SAMPLE_TARGET_OS_FOR_EXAMPLES = "macOS-13.3.1-x86-64bit"
    EXAMPLE_REQUEST_CONDA_INSTALL = "install conda"
    EXAMPLE_OUTPUT_CONDA_DETAILED = """
{
"input": "install conda",
"error": 0,
"commands": [
{
"seq": 1,
"cmd_to_execute": "curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh",
"cmd_explanations": ["The curl command is used to issue web requests, e.g. download web pages."],
"arg_explanations": {
"-O": "specifies that we want to save the response to a file.",
"https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh": "is the URL of the file we want to download."
}
},
{
"seq": 2,
"cmd_to_execute": "bash Miniconda3-latest-MacOSX-x86_64.sh",
"cmd_explanations": ["The bash command is used to execute shell scripts."],
"arg_explanations": {"Miniconda3-latest-MacOSX-x86_64.sh": "is the name of the file we want to execute."}
}
]
}
"""
    EXAMPLE_OUTPUT_CONDA_CONDENSED = """
{
"commands": ["curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh", "bash Miniconda3-latest-MacOSX-x86_64.sh"]
}
"""
    EXAMPLE_REQUEST_FILE_SEARCH = "search ~/Documents directory for any python file that begins with 'test'"
    EXAMPLE_OUTPUT_SEARCH_DETAILED = """
{
"input": "search the ~/Documents/ directory for any python file that begins with 'test'",
"error" : 0,
"commands": [
{
"seq": 1,
"cmd_to_execute": "find /Documents/ -name 'test*.py'",
"cmd_explanations": ["find is used to list files."],
"arg_explanations": {
"/Documents": "specifies the folder to search in.",
"-name 'test*.py'": "specifies that we want to search for files starting with test that are python files."
}
}
]
}
"""
    EXAMPLE_OUTPUT_SEARCH_CONDENSED = """
{
"commands": ["find ~/Documents/ -name 'test*.py'"]
}
"""
    EXAMPLE_REQUEST_PROCESS_LIST = "list all processes using more than 50 MB of memory"
    EXAMPLE_OUTPUT_PROCESS_CONDENSED = """
{
"commands": ["ps -axm -o %mem,rss,comm | awk '$1 > 0.5 { printf(\\"%.0fMB\\t%s\\n\\", $2/1024, $3); }'"]
}
"""
    EXAMPLE_AMBIGUOUS_REQUEST = "the quick brown fox jumped over"
    EXAMPLE_OUTPUT_AMBIGUOUS_DETAILED = """{"input": "the quick brown fox jumped over", "error": 1}"""
    EXAMPLE_OUTPUT_AMBIGUOUS_CONDENSED = """{"error": 1}"""

    EXAMPLE_REQUEST_WINDOWS_SERVICES = "list running services on windows"
    EXAMPLE_OUTPUT_WINDOWS_SERVICES_DETAILED = """
{
"input": "list running services on windows",
"error": 0,
"commands": [
{
"seq": 1,
"cmd_to_execute": "powershell -Command 'Get-Service | Where-Object {$_.Status -eq \\"Running\\"} | Select-Object DisplayName, Name, Status'",
"cmd_explanations": ["Uses PowerShell to get all services, filters for those that are 'Running', and then selects specific properties to display."],
"arg_explanations": {
"powershell -Command '...'": "Instructs the command prompt to execute the entire single-quoted string using PowerShell.",
"Get-Service": "PowerShell cmdlet to retrieve information about system services.",
"Where-Object {$_.Status -eq \\"Running\\"}": "PowerShell cmdlet to filter objects. Here, it filters for services where the Status property is 'Running' (using double quotes for the string value inside the PowerShell script block).",
"Select-Object DisplayName, Name, Status": "PowerShell cmdlet to select specific properties of an object. Here, it chooses to display the DisplayName, Name, and Status of each running service."
}
}
]
}
"""
    EXAMPLE_OUTPUT_WINDOWS_SERVICES_CONDENSED = """
{
"commands": ["powershell -Command 'Get-Service | Where-Object {$_.Status -eq \\"Running\\"} | Select-Object DisplayName, Name, Status'"]
}
"""

    EXAMPLE_REQUEST_WINDOWS_FLASK = "on windows, make a file on my desktop named app.py and write a simple flask hello world app in it"
    EXAMPLE_OUTPUT_WINDOWS_FLASK_DETAILED = """
{
"input": "on windows, make a file on my desktop named app.py and write a simple flask hello world app in it",
"error": 0,
"commands": [
{
"seq": 1,
"cmd_to_execute": "powershell -Command \"'from flask import Flask`n`napp = Flask(__name__)`n`n@app.route(''/'')`ndef hello_world():`n    return ''Hello, World!''`n`nif __name__ == ''__main__'':`n    app.run(debug=True)' | Set-Content -Path \\\"$env:USERPROFILE\\Desktop\\app.py\\\" -Force\"",
"cmd_explanations": ["This single PowerShell command creates a new file 'app.py' on the desktop and writes a basic Flask application into it. It uses a robust method to handle multi-line content with special characters."],
"arg_explanations": {
"powershell -Command \"...'\"": "Executes the enclosed PowerShell script block. The outer double quotes are for cmd.exe, and the inner single quotes are for PowerShell.",
"'...content...' | Set-Content": "A PowerShell technique where a multi-line string is created and then 'piped' to the Set-Content cmdlet.",
"Set-Content -Path ... -Force": "This cmdlet writes content to a file, creating the file if it doesn't exist or overwriting it if it does (`-Force`).",
"`n": "Represents a newline character within the PowerShell string.",
"''": "Escapes a single quote character within a single-quoted PowerShell string. For example, to write 'hello', you use ''hello''."
}
}
]
}
"""
    EXAMPLE_OUTPUT_WINDOWS_FLASK_CONDENSED = """
{
"commands": ["powershell -Command \"'from flask import Flask`n`napp = Flask(__name__)`n`n@app.route(''/'')`ndef hello_world():`n    return ''Hello, World!''`n`nif __name__ == ''__main__'':`n    app.run(debug=True)' | Set-Content -Path \\\"$env:USERPROFILE\\Desktop\\app.py\\\" -Force\""]
}
"""


    def __init__(self):
        pass

    def _determine_instruction_json_schema(self, use_condensed_format: bool) -> str:
        return self.CONDENSED_RESPONSE_JSON_SCHEMA if use_condensed_format else self.DETAILED_RESPONSE_JSON_SCHEMA

    def _determine_error_json_response(self, use_condensed_format: bool) -> str:
        return self.INVALID_REQUEST_CONDENSED_JSON_RESPONSE if use_condensed_format else self.INVALID_REQUEST_JSON_RESPONSE

    def generate_initial_ai_directive(self, use_condensed_format: bool) -> str:
        json_response_template = self._determine_instruction_json_schema(use_condensed_format)
        json_error_template = self._determine_error_json_response(use_condensed_format)
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""
Provide the appropriate command-line commands that can be executed for a user request (keep in mind the platform of the user, e.g., {self.SAMPLE_TARGET_OS_FOR_EXAMPLES} or a specific Windows version like Windows-10-10.0.19041-SP0).
Today's date/time is {current_timestamp}.
If the request is possible, please provide commands that can be executed in the command line and do not require a GUI.
Do not include commands that require a yes/no response.
For each command, explain the command and any arguments used.
Try to find the simplest command(s) that can be used to execute the request.

IMPORTANT FOR COMPLEX COMMANDS (e.g., PowerShell on Windows, or piped commands on any OS):
Ensure the entire command sequence is formatted to be executed as a single unit by the system's default shell (e.g., cmd.exe on Windows, bash on Linux/macOS).
The `cmd_to_execute` field should contain the complete, runnable, SINGLE-LINE command string. Do NOT use newlines or line breaks within the `cmd_to_execute` value itself.

- On Windows for PowerShell: `powershell -Command 'Get-Process | Sort-Object CPU -Descending | Select-Object -First 5'`
- On Linux/macOS for bash: `bash -c "your_command_1 | your_command_2"`

SPECIAL INSTRUCTIONS FOR WRITING FILE CONTENT ON WINDOWS:
When a request involves writing multi-line text with quotes to a file, the most robust method is to use a single PowerShell command that pipes the content to `Set-Content`.
This avoids complex quoting issues. The pattern is: `powershell -Command "'<content>' | Set-Content -Path '<filepath>'"`.
- The content MUST be enclosed in single quotes.
- Any single quotes `'` inside the content MUST be escaped by doubling them to `''`.
- Newline characters inside the content MUST be represented by the PowerShell escape sequence, a backtick followed by n (`n).

If the request is valid, format each command output in the following JSON format: {json_response_template}

If the request is invalid, please return the following JSON format: {json_error_template}
            """

    def _construct_ai_interaction_message(self, role_type: str, message_content: str) -> dict:
        return {"role": role_type, "parts": [message_content]}

    def _create_user_request_message_for_instruction_gen(self, end_user_query: str, target_os_descriptor: str) -> dict:
        formatted_query_content = (
            f"""Provide the appropriate command-line commands that can be executed on a {target_os_descriptor} machine for the user request: "{end_user_query}"."""
        )
        return self._construct_ai_interaction_message("user", formatted_query_content)

    def _create_ai_response_message_for_instruction_gen(self, ai_generated_json_output: str) -> dict:
        return self._construct_ai_interaction_message("model", ai_generated_json_output)

    def assemble_instruction_generation_training_examples(self, use_condensed_format: bool) -> list:
        initial_directive_message = self.generate_initial_ai_directive(use_condensed_format)
        dialogue_sequence = [
            self._construct_ai_interaction_message("user", initial_directive_message),
            self._construct_ai_interaction_message("model", "Understood!"),
        ]
        conda_user_request = self._create_user_request_message_for_instruction_gen(
            self.EXAMPLE_REQUEST_CONDA_INSTALL, target_os_descriptor=self.SAMPLE_TARGET_OS_FOR_EXAMPLES
        )
        conda_ai_response_content = self.EXAMPLE_OUTPUT_CONDA_CONDENSED if use_condensed_format else self.EXAMPLE_OUTPUT_CONDA_DETAILED
        conda_ai_response = self._create_ai_response_message_for_instruction_gen(conda_ai_response_content)
        dialogue_sequence.extend([conda_user_request, conda_ai_response])

        search_user_request = self._create_user_request_message_for_instruction_gen(
            self.EXAMPLE_REQUEST_FILE_SEARCH, target_os_descriptor=self.SAMPLE_TARGET_OS_FOR_EXAMPLES
        )
        search_ai_response_content = self.EXAMPLE_OUTPUT_SEARCH_CONDENSED if use_condensed_format else self.EXAMPLE_OUTPUT_SEARCH_DETAILED
        search_ai_response = self._create_ai_response_message_for_instruction_gen(search_ai_response_content)
        dialogue_sequence.extend([search_user_request, search_ai_response])

        if use_condensed_format:
            process_user_request = self._create_user_request_message_for_instruction_gen(
                self.EXAMPLE_REQUEST_PROCESS_LIST, target_os_descriptor=self.SAMPLE_TARGET_OS_FOR_EXAMPLES
            )
            process_ai_response = self._create_ai_response_message_for_instruction_gen(self.EXAMPLE_OUTPUT_PROCESS_CONDENSED)
            dialogue_sequence.extend([process_user_request, process_ai_response])

        # Add a Windows-specific example to ensure the AI sees correct PowerShell formatting for cmd.exe
        windows_example_os_descriptor = "Windows-10-10.0.19041-SP0" # A sample Windows OS string
        win_services_user_request = self._create_user_request_message_for_instruction_gen(
            self.EXAMPLE_REQUEST_WINDOWS_SERVICES, target_os_descriptor=windows_example_os_descriptor
        )
        win_services_ai_response_content = self.EXAMPLE_OUTPUT_WINDOWS_SERVICES_CONDENSED if use_condensed_format else self.EXAMPLE_OUTPUT_WINDOWS_SERVICES_DETAILED
        win_services_ai_response = self._create_ai_response_message_for_instruction_gen(win_services_ai_response_content)
        dialogue_sequence.extend([win_services_user_request, win_services_ai_response])

        # Add the new, robust Windows file writing example
        win_flask_user_request = self._create_user_request_message_for_instruction_gen(
            self.EXAMPLE_REQUEST_WINDOWS_FLASK, target_os_descriptor=windows_example_os_descriptor
        )
        win_flask_ai_response_content = self.EXAMPLE_OUTPUT_WINDOWS_FLASK_CONDENSED if use_condensed_format else self.EXAMPLE_OUTPUT_WINDOWS_FLASK_DETAILED
        win_flask_ai_response = self._create_ai_response_message_for_instruction_gen(win_flask_ai_response_content)
        dialogue_sequence.extend([win_flask_user_request, win_flask_ai_response])


        ambiguous_user_request = self._create_user_request_message_for_instruction_gen(
            self.EXAMPLE_AMBIGUOUS_REQUEST, target_os_descriptor=self.SAMPLE_TARGET_OS_FOR_EXAMPLES
        )
        ambiguous_ai_response_content = self.EXAMPLE_OUTPUT_AMBIGUOUS_CONDENSED if use_condensed_format else self.EXAMPLE_OUTPUT_AMBIGUOUS_DETAILED
        ambiguous_ai_response = self._create_ai_response_message_for_instruction_gen(ambiguous_ai_response_content)
        dialogue_sequence.extend([ambiguous_user_request, ambiguous_ai_response])

        return dialogue_sequence

    def format_actual_user_request_for_instruction_gen(self, end_user_query: str, current_target_os_descriptor: str) -> dict:
        return self._create_user_request_message_for_instruction_gen(end_user_query, current_target_os_descriptor)

    def format_actual_ai_response_for_instruction_gen(self, ai_generated_json_output: str) -> dict:
        return self._create_ai_response_message_for_instruction_gen(ai_generated_json_output)