import os
import re
import json
import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable
from collections.abc import Callable as CallableType
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger(__name__)

# Ensure API key is configured. Consider moving this to a central init if not already.
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
else:
    logger.warning("GEMINI_API_KEY environment variable not set. LLM calls will fail.")


VIGI_DEV_SYSTEM_PROMPT = """
You are a top tier AI developer writing a program based on user intent.
Fully implement every feature without TODOs. Add code comments explaining your implementation.
"""

CONVERSATION_PROMPT_TEMPLATE = """
You are maintaining a software project. Consider this conversation history:
{history}

Current project structure:
{file_tree}
{web_search_block}
Respond to the user's request while considering the existing codebase.
User: {input}
Assistant:
"""

MODIFICATION_PROMPT_TEMPLATE = """
Modify the existing codebase based on this request: {request}
{web_search_block}
Existing files:
{existing_files}

Provide ONLY a JSON object where:
- Keys are relative file paths (strings).
- Values are the **complete new content** for that file (strings).
- CRITICAL: Within the string values (the file content), all special characters such as double quotes ("), backslashes (\\), newlines (\\n), tabs (\\t), etc., MUST be correctly escaped to form a valid JSON string. For example, if a file's content is `print("hello")`, the JSON value for that file should be `"print(\\"hello\\")"`. If the content has a newline, it should be represented as `\\n` within the JSON string.
Example: {{"src/app.js": "console.log(\\"Hello World!\\");\\n// more code...", "public/index.html": "<!DOCTYPE html>..."}}
"""

QA_PROMPT_TEMPLATE = """
Answer this question about the codebase: {question}
{web_search_block}
Relevant code files:
{relevant_code}

Provide a concise technical answer:
"""

GENERATE_SLUG_PROMPT = """
Based on the following user prompt, suggest a short, descriptive, filesystem-friendly project name (slug).
The slug should be in kebab-case (all lowercase, words separated by hyphens).
It should not contain spaces or special characters other than hyphens. Aim for 2-5 words.
Examples:
User Prompt: "a simple pong game in javascript" -> Slug: "simple-pong-game"
User Prompt: "complex data analysis tool with python and pandas" -> Slug: "data-analysis-tool"
User Prompt: "My new web app" -> Slug: "my-new-web-app"

User Prompt: {user_prompt}

Return ONLY the slug:
"""

SPECIFY_FILE_PATHS_PROMPT_TEMPLATE = """
    {system_prompt}
    Generate a JSON array of **relative file paths** needed for this project.
    Paths should be relative to the project's root directory.
    Filenames should be appropriate for their content and OS-agnostic where possible.
    - DO NOT include absolute paths (e.g., paths starting with / or a drive letter like C:\\).
    - DO NOT use ".." to navigate to parent directories. All paths must be within the project.
    - Ensure paths are valid filenames or relative paths like "src/components/button.js".
    {web_search_block}
    Example: ["index.html", "styles.css", "app.js", "src/components/button.js"]

    User Prompt: {prompt}
    Plan: {plan}

    Return ONLY a JSON array of strings representing relative file paths:
"""

PLAN_PROMPT_TEMPLATE = """
    {system_prompt}
    Create a development plan using GitHub Markdown. Start with a YAML block describing files to create.
    Include for each file: variables, schemas, DOM IDs, and function names.
    {web_search_block}
    App Prompt: {prompt}
"""

GENERATE_CODE_PROMPT_TEMPLATE = """
    {system_prompt}
    You are generating code for the file: {current_file}
    Follow this overall development plan:
    {plan_details}
    {web_search_block}
    User's Original Goal (for context): {prompt}

    Instructions:
    1. Generate ONLY the complete, valid code for the file `{current_file}`.
    2. Ensure the code is fully functional and implements the requirements for this specific file as per the plan.
    3. Do not add any explanatory text, markdown, or comments *outside* the code block if one is used.
    4. If the file is a configuration file (e.g. JSON, YAML), just output the raw content.
    5. If the file is a script (e.g. Python, JavaScript), output the code, ideally within a ```<language_hint> ... ``` block if appropriate, but ensure ONLY code is present. If no language hint, just raw code.

    Code for {current_file}:
"""

REFINE_SEARCH_QUERY_PROMPT_TEMPLATE = """
Based on the user's topic or request, generate a concise and effective search engine query.
The query should be suitable for finding technical information, libraries, APIs, or best practices.
Focus on keywords and specific terms.

User's Topic/Request: {search_topic}

Return ONLY the refined search query:
"""

SUMMARIZE_SEARCH_RESULTS_PROMPT_TEMPLATE = """
You are an AI assistant helping a developer.
The developer is working on the task: "{task_description}"
They performed a web search with the query: "{search_query}"
Here are the search results (title, URL, snippet):
--- BEGIN SEARCH RESULTS ---
{search_results_str}
--- END SEARCH RESULTS ---

Based on these results, provide a concise summary of information that is MOST RELEVANT to accomplishing the task: "{task_description}".
Focus on:
- Key insights, concepts, or important definitions.
- Relevant libraries, tools, APIs, or functions mentioned.
- Specific code patterns or best practices highlighted.
- Potential solutions or approaches suggested by the results.
If the search results seem largely irrelevant to the task, explicitly state that.
Present the summary clearly. Avoid just listing the results; synthesize the information.
Your summary should directly help the developer move forward with their task.

Concise Relevant Summary:
"""

def _prepare_web_search_block(web_search_summary: Optional[str]) -> str:
    if web_search_summary:
        return f"\n\n--- WEB SEARCH INSIGHTS ---\n{web_search_summary}\n--- END WEB SEARCH INSIGHTS ---\n"
    return ""

def generate_project_slug(user_prompt: str, model: str = 'gemini-1.5-pro-latest') -> str:
    """Generates a filesystem-friendly project slug from a user prompt."""

    prompt_text = GENERATE_SLUG_PROMPT.format(user_prompt=user_prompt)

    try:
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt_text,
            generation_config=genai.GenerationConfig(temperature=0.4, max_output_tokens=50))

        slug = response.text.strip().lower()
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')

        if not slug:
            slug = "-".join(user_prompt.lower().split()[:3])
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
            return slug if slug else "unnamed-project"
        return slug
    except Exception as e:
        logger.error(f"Error generating project slug: {e}")
        slug = "-".join(user_prompt.lower().split()[:3])
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug if slug else "error-unnamed-project"


def specify_file_paths(prompt: str, plan_content: str, model: str = 'gemini-1.5-pro-latest', web_search_summary: Optional[str] = None) -> List[str]:
    web_search_block = _prepare_web_search_block(web_search_summary)
    prompt_text = SPECIFY_FILE_PATHS_PROMPT_TEMPLATE.format(
        system_prompt=VIGI_DEV_SYSTEM_PROMPT,
        prompt=prompt,
        plan=plan_content,
        web_search_block=web_search_block
    )

    try:
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt_text,
            generation_config=genai.GenerationConfig(temperature=0.7))

        match = re.search(r'\[\s*(?:".*?"\s*,\s*)*".*?"\s*\]|\[\s*\]', response.text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            logger.error(f"Failed to find a valid JSON array in LLM response for file paths: {response.text}")
            lines = [line.strip() for line in response.text.splitlines() if line.strip().endswith(('.html', '.css', '.js', '.py', '.md', '.json', '.txt'))]
            if lines:
                 logger.warning(f"Attempting to use line-extracted paths: {lines}")
                 return lines
            return []
    except Exception as e:
        logger.error(f"Failed to parse file paths from LLM response '{response.text}': {e}")
        return []

def plan(prompt: str,
         stream_handler: Optional[Callable[[bytes], None]] = None,
         model: str = 'gemini-1.5-pro-latest',
         extra_messages: List[Dict[str, str]] = [],
         web_search_summary: Optional[str] = None) -> str:
    web_search_block = _prepare_web_search_block(web_search_summary)
    full_prompt = PLAN_PROMPT_TEMPLATE.format(
        system_prompt=VIGI_DEV_SYSTEM_PROMPT,
        prompt=prompt,
        web_search_block=web_search_block
    )

    try:
        model_instance = genai.GenerativeModel(model)
        response_stream = model_instance.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(temperature=0.7),
            stream=True)

        collected = []
        for chunk in response_stream:
            text = chunk.text
            collected.append(text)
            if stream_handler and text:
                stream_handler(text.encode('utf-8'))

        return "".join(collected)
    except Exception as e:
        logger.error(f"Error in plan generation stream: {e}")
        return f"Error during plan generation: {e}"


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
async def generate_code(prompt: str,
                       plan_details: str,
                       current_file: str,
                       stream_handler: Optional[Callable[[bytes], Any]] = None,
                       model_name: str = 'gemini-1.5-pro-latest',
                       web_search_summary: Optional[str] = None) -> str:
    web_search_block = _prepare_web_search_block(web_search_summary)
    full_prompt = GENERATE_CODE_PROMPT_TEMPLATE.format(
        system_prompt=VIGI_DEV_SYSTEM_PROMPT,
        current_file=current_file,
        plan_details=plan_details,
        prompt=prompt,
        web_search_block=web_search_block
    )

    async def sync_generate() -> str:
        model = genai.GenerativeModel(model_name)
        response_stream = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(temperature=0.5, max_output_tokens=4096),
            stream=True)

        collected = []
        for chunk in response_stream:
            text = chunk.text
            collected.append(text)
            if stream_handler and text:
                stream_handler(text.encode('utf-8'))
        return "".join(collected)

    try:
        code_content = await sync_generate()
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9_+\-]+)?\s*\n(.*?)\n```", code_content, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        else:
            return code_content.strip()
    except Exception as e:
        logger.error(f"Error generating code for {current_file}: {e}")
        return f"// Error generating code for {current_file}: {e}"


def generate_code_sync(prompt: str,
                      plan_details: str,
                      current_file: str,
                      stream_handler: Optional[Callable[[bytes], Any]] = None,
                      model: str = 'gemini-1.5-pro-latest',
                      web_search_summary: Optional[str] = None) -> str:
    try:
        # This simplification might be necessary if running within Agent's managed loop
        return asyncio.run(generate_code(prompt, plan_details, current_file, stream_handler, model, web_search_summary))
    except RuntimeError as e:
        if "cannot be nested" in str(e) or "is already running" in str(e) : # Adjusted to catch common error messages
            logger.warning("Asyncio event loop nesting issue in generate_code_sync. Attempting direct call or task creation if possible. This is a temporary workaround.")
            if genai.api_key:
                 web_search_block = _prepare_web_search_block(web_search_summary)
                 full_prompt_text = GENERATE_CODE_PROMPT_TEMPLATE.format(
                    system_prompt=VIGI_DEV_SYSTEM_PROMPT, current_file=current_file,
                    plan_details=plan_details, prompt=prompt, web_search_block=web_search_block
                )
                 model_instance = genai.GenerativeModel(model)
                 response = model_instance.generate_content(full_prompt_text) # Simple blocking call
                 code_blocks = re.findall(r"```(?:.*?)\n(.*?)```", response.text, re.DOTALL)
                 return code_blocks[0] if code_blocks else response.text.strip()
            return f"// Error due to event loop issue for {current_file}"
        raise e

async def handle_conversation(context: Dict[str, Any],
                            user_input: str,
                            model_name: str = 'gemini-1.5-pro-latest',
                            web_search_summary: Optional[str] = None) -> str:
    web_search_block = _prepare_web_search_block(web_search_summary)
    prompt = CONVERSATION_PROMPT_TEMPLATE.format(
        history="\n".join([f"{msg['role']}: {msg['content']}"
                          for msg in context.get('conversation_history', [])]),
        file_tree=context.get('file_tree', "File tree not available."), # Use provided file_tree
        input=user_input,
        web_search_block=web_search_block
    )

    try:
        model_instance = genai.GenerativeModel(model_name)
        response = await asyncio.to_thread(model_instance.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error handling conversation: {e}")
        return f"Error during conversation: {e}"


def handle_conversation_sync(context: Dict[str, Any],
                           user_input: str,
                           model: str = 'gemini-1.5-pro-latest',
                           web_search_summary: Optional[str] = None) -> str:
    try:
        return asyncio.run(handle_conversation(context, user_input, model, web_search_summary))
    except RuntimeError: # Simplified error handling for nesting
        if genai.api_key:
            web_search_block = _prepare_web_search_block(web_search_summary)
            prompt_text = CONVERSATION_PROMPT_TEMPLATE.format(history="...", file_tree="...", input=user_input, web_search_block=web_search_block)
            model_instance = genai.GenerativeModel(model)
            response = model_instance.generate_content(prompt_text)
            return response.text
        return "Error: Could not handle conversation due to event loop issue."

async def generate_modification(context: Dict[str, Any],
                              request: str,
                              model_name: str = 'gemini-1.5-pro-latest',
                              web_search_summary: Optional[str] = None) -> Dict[str, Any]: # Return type includes error
    existing_files_parts = []
    for path in context.get('file_paths', []):
        content = context['codebase'].get(path, f'// File {path} exists but no content loaded or available.')
        existing_files_parts.append(f"File: {path}\nContent:\n{content}")
    existing_files_str = "\n\n---\n\n".join(existing_files_parts)
    web_search_block = _prepare_web_search_block(web_search_summary)

    modification_prompt_text = MODIFICATION_PROMPT_TEMPLATE.format(
        request=request,
        existing_files=existing_files_str,
        web_search_block=web_search_block
    )

    json_str_cleaned = "" # Initialize to ensure it's defined in case of early exit
    try:
        json_response_str = await generate_code(
            prompt=request,
            plan_details=modification_prompt_text,
            current_file="modifications.json",
            model_name=model_name,
            web_search_summary=None
        )

        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_response_str, re.DOTALL | re.MULTILINE)
        if match:
            json_str_cleaned = match.group(1)
        else:
            first_brace = json_response_str.find('{')
            last_brace = json_response_str.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str_cleaned = json_response_str[first_brace : last_brace+1]
            else:
                logger.error(f"Could not find JSON structure in modification response: {json_response_str}")
                return {"error": "LLM response did not contain a recognizable JSON object for modifications."}

        parsed_json = json.loads(json_str_cleaned)
        processed_json = {}
        if isinstance(parsed_json, dict):
            for file_path, value in parsed_json.items():
                if isinstance(value, dict) and "content" in value and isinstance(value["content"], str):
                    processed_json[file_path] = value["content"] # Use content if nested
                elif isinstance(value, str):
                    processed_json[file_path] = value # Use value directly if string
                else:
                    logger.warning(f"Unexpected value type for file '{file_path}' in modification JSON: {type(value)}. Value: {str(value)[:100]} Skipping.")
            return processed_json
        else:
            logger.error(f"LLM modification response was not a dictionary as expected: {type(parsed_json)} Content: {json_str_cleaned[:200]}")
            return {"error": "LLM response for modifications was not a dictionary of files."}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from modification response: '{json_str_cleaned}'. Error: {e}")
        return {"error": f"Failed to parse LLM JSON output for modifications. Content (cleaned): {json_str_cleaned[:200]}..."}
    except Exception as e:
        logger.error(f"Error generating modification: {e}", exc_info=True)
        return {"error": f"General error during modification: {str(e)}"}


def generate_modification_sync(context: Dict[str, Any],
                             request: str,
                             model: str = 'gemini-1.5-pro-latest',
                             web_search_summary: Optional[str] = None) -> Dict[str, Any]:
    try:
        return asyncio.run(generate_modification(context, request, model, web_search_summary))
    except RuntimeError:
        return {"error": "Could not generate modification due to event loop issue."}


async def answer_question(context: Dict[str, Any],
                        question: str,
                        model_name: str = 'gemini-1.5-pro-latest',
                        web_search_summary: Optional[str] = None) -> str:
    relevant_files = context.get('file_paths', [])
    relevant_code_parts = []
    for path in relevant_files:
        code_snippet = context['codebase'].get(path, f'// Code for {path} not available.')
        if len(code_snippet) > 1500:
            code_snippet = code_snippet[:1500] + "\n... (file truncated)\n"
        relevant_code_parts.append(f"File: {path}\n{code_snippet}")
    relevant_code_str = "\n\n---\n\n".join(relevant_code_parts)
    web_search_block = _prepare_web_search_block(web_search_summary)

    prompt_text = QA_PROMPT_TEMPLATE.format(
        question=question,
        relevant_code=relevant_code_str,
        web_search_block=web_search_block
    )

    try:
        model_instance = genai.GenerativeModel(model_name)
        response = await asyncio.to_thread(
            model_instance.generate_content,
            prompt_text
        )
        return response.text
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        return f"Error during question answering: {e}"


def answer_question_sync(context: Dict[str, Any],
                        question: str,
                        model: str = 'gemini-1.5-pro-latest',
                        web_search_summary: Optional[str] = None) -> str:
    try:
        return asyncio.run(answer_question(context, question, model, web_search_summary))
    except RuntimeError:
        return "Error: Could not answer question due to event loop issue."

async def refine_search_query_async(search_topic: str, model_name: str = 'gemini-1.5-pro-latest') -> str:
    """Refines a user's search topic into an effective search engine query using an LLM."""
    prompt = REFINE_SEARCH_QUERY_PROMPT_TEMPLATE.format(search_topic=search_topic)
    try:
        model_instance = genai.GenerativeModel(model_name)
        response = await asyncio.to_thread(
            model_instance.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.3, max_output_tokens=100)
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error refining search query for '{search_topic}': {e}")
        return search_topic # Fallback to original topic


async def summarize_search_results_async(task_description: str, search_query: str,
                                         search_results: List[Dict[str, str]],
                                         model_name: str = 'gemini-1.5-pro-latest') -> str:
    """Summarizes web search results in the context of a given task using an LLM."""
    if not search_results:
        return "No search results provided to summarize."

    results_str_parts = []
    for i, res in enumerate(search_results):
        results_str_parts.append(f"Result {i+1}:\nTitle: {res.get('title', 'N/A')}\nURL: {res.get('href', 'N/A')}\nSnippet: {res.get('body', 'N/A')}\n---")
    search_results_str = "\n".join(results_str_parts)

    MAX_RESULTS_STR_LEN = 10000
    if len(search_results_str) > MAX_RESULTS_STR_LEN:
        search_results_str = search_results_str[:MAX_RESULTS_STR_LEN] + "\n... (search results truncated for brevity)"


    prompt = SUMMARIZE_SEARCH_RESULTS_PROMPT_TEMPLATE.format(
        task_description=task_description,
        search_query=search_query,
        search_results_str=search_results_str
    )

    try:
        model_instance = genai.GenerativeModel(model_name)
        response = await asyncio.to_thread(
            model_instance.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.5, max_output_tokens=1024)
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error summarizing search results for query '{search_query}': {e}", exc_info=True)
        return f"Error summarizing search results: {e}. Raw results might be too extensive or an API issue occurred."