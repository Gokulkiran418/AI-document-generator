import openai
import ast
import os
import requests
import base64
import re
from dotenv import load_dotenv
from httpx import Client as HttpxClient

load_dotenv()
# Initialize OpenAI client with a custom HTTP client to disable proxies
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=HttpxClient(proxies=None)
)

def get_files(repo_url, extensions=None):
    """
    Fetch a list of files from a GitHub repository, optionally filtered by extensions.
    Args:
        repo_url (str): URL of the GitHub repository (e.g., https://github.com/username/repo).
        extensions (list, optional): List of file extensions to filter (e.g., ['.py', '.js']). If None, fetch all files.
    Returns:
        list: List of file paths in the repository.
    """
    try:
        owner, repo = repo_url.rstrip('/').split('/')[-2:]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        response = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        files = []
        for item in response.json():
            if item['type'] == 'file':
                file_path = item['path']
                if extensions is None or any(file_path.endswith(ext) for ext in extensions):
                    files.append(file_path)
            elif item['type'] == 'dir':
                # Recursively fetch files from directories
                dir_url = item['url']
                dir_response = requests.get(dir_url, headers={"Accept": "application/vnd.github.v3+json"})
                dir_response.raise_for_status()
                for sub_item in dir_response.json():
                    if sub_item['type'] == 'file':
                        file_path = sub_item['path']
                        if extensions is None or any(file_path.endswith(ext) for ext in extensions):
                            files.append(file_path)
        return files
    except requests.RequestException as e:
        print(f"Error fetching repository contents: {e}")
        return []

def get_file_content(repo_url, file_path):
    """
    Fetch the content of a specific file from a GitHub repository.
    Args:
        repo_url (str): URL of the GitHub repository.
        file_path (str): Path to the file in the repository.
    Returns:
        str: Decoded file content or None if an error occurs.
    """
    try:
        owner, repo = repo_url.rstrip('/').split('/')[-2:]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        response = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')
    except requests.RequestException as e:
        print(f"Error fetching file content: {e}")
        return None
    except UnicodeDecodeError as e:
        print(f"Error decoding file content: {e}")
        return None

def generate_docstrings(code, file_path):
    """
    Generate documentation for the provided code based on its language or skip non-code files.
    Args:
        code (str): The code to process.
        file_path (str): Path of the file being processed.
    Returns:
        str: Modified code with added documentation or original code if skipped.
    """
    # Define supported languages and their documentation styles
    language_map = {
        '.py': 'Python (Google-style docstrings)',
        '.js': 'JavaScript (JSDoc comments)',
        '.java': 'Java (Javadoc comments)',
        # Add more languages as needed
    }
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    
    # Skip non-code files
    if ext not in language_map:
        print(f"Skipping non-code file: {file_path}")
        return code
    
    language_style = language_map[ext]
    
    try:
        # Language-specific prompt
        prompt = f"Add {language_style} to the following code:\n\n{code}"
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.2,
            max_tokens=2048,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].text
    except openai.OpenAIError as e:
        print(f"OpenAI API error for {file_path}: {e}")
        return code
    except Exception as e:
        print(f"Unexpected error generating documentation for {file_path}: {e}")
        return code

def extract_docstrings(modified_code, file_path):
    """
    Extract documentation from the modified code based on the file's language.
    Args:
        modified_code (str): Code with added documentation.
        file_path (str): Path of the file being processed.
    Returns:
        dict: Dictionary mapping names to documentation or generic metadata for non-code files.
    """
    _, ext = os.path.splitext(file_path)
    
    if ext == '.py':
        try:
            tree = ast.parse(modified_code)
            docstrings = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        name = node.name
                        docstring = node.body[0].value.s
                        docstrings[name] = docstring
            return docstrings
        except SyntaxError as e:
            print(f"Syntax error in {file_path}, skipping: {e}")
            return {}
    elif ext in ['.js', '.java']:
        # Extract multi-line comments (/** ... */ or /* ... */)
        pattern = r'/\*\*?\s*(.*?)\s*\*/'
        matches = re.findall(pattern, modified_code, re.DOTALL)
        if matches:
            return {"Documentation": "\n".join(matches)}
        else:
            return {"Documentation": "No documentation found."}
    else:
        # Generic metadata for non-code files
        return {"Message": "Documentation not applicable for this file type."}

def generate_readme_from_code(code, language="Python"):
    """
    Generate a README for the provided code using OpenAI.
    Args:
        code (str): The code to generate a README for.
        language (str): The programming language of the code (default: Python).
    Returns:
        str: Generated README content or error message.
    """
    try:
        prompt = f"Generate a README for this {language} code:\n\n{code}"
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.3,
            max_tokens=2048,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].text
    except openai.OpenAIError as e:
        print(f"OpenAI API error generating README from code: {e}")
        return "Failed to generate README due to API error."
   
def generate_readme(repo_url, python_files):
    """
    Generate a README file for the repository based on its Python files.
    Args:
        repo_url (str): URL of the GitHub repository.
        python_files (list): List of Python file paths in the repository.
    Returns:
        str: Generated README content or error message if generation fails.
    """
    try:
        # Create a summary of the repository's structure
        repo_summary = f"Repository: {repo_url}\nPython files found: {len(python_files)}\nSample files: {python_files[:3]}"
        prompt = f"""
        Generate a professional README file in Markdown format for a Python project based on the following information:
        {repo_summary}
        The README should include:
        - Project title (derived from the repository name)
        - Brief description of the project
        - Installation instructions
        - Usage examples
        - Any other relevant sections (e.g., Contributing, License)
        Ensure the content is clear, concise, and follows standard Markdown formatting.
        """
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.3,
            max_tokens=2048,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].text
    except openai.OpenAIError as e:
        print(f"OpenAI API error generating README: {e}")
        return "Failed to generate README due to API error."
    except Exception as e:
        print(f"Unexpected error generating README: {e}")
        return "Failed to generate README due to an unexpected error."