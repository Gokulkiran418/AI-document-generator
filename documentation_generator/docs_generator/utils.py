import openai
import ast
import os
import requests
import base64
from dotenv import load_dotenv
from httpx import Client as HttpxClient

load_dotenv()
# Initialize OpenAI client with a custom HTTP client to disable proxies
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=HttpxClient(proxies=None)
)

def get_python_files(repo_url):
    """
    Fetch a list of Python files from a GitHub repository.
    Args:
        repo_url (str): URL of the GitHub repository (e.g., https://github.com/username/repo).
    Returns:
        list: List of file paths for Python files in the repository.
    """
    try:
        owner, repo = repo_url.rstrip('/').split('/')[-2:]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        response = requests.get(api_url, headers={"Accept": "application/vnd.github.v3+json"})
        response.raise_for_status()
        files = []
        for item in response.json():
            if item['type'] == 'file' and item['name'].endswith('.py'):
                files.append(item['path'])
            elif item['type'] == 'dir':
                dir_url = item['url']
                dir_response = requests.get(dir_url, headers={"Accept": "application/vnd.github.v3+json"})
                dir_response.raise_for_status()
                for sub_item in dir_response.json():
                    if sub_item['type'] == 'file' and sub_item['name'].endswith('.py'):
                        files.append(sub_item['path'])
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

def generate_docstrings(code):
    """
    Generate Google-style docstrings for functions and classes in the provided code using OpenAI.
    Args:
        code (str): The Python code to process.
    Returns:
        str: Modified code with added docstrings or original code if an error occurs.
    """
    try:
        # Estimate tokens (1 token ~ 4 chars)
        max_chars = 8000  # Approx 2000 tokens to leave room for prompt and completion
        if len(code) > max_chars:
            print(f"Code too large ({len(code)} chars), chunking input.")
            # Split code into chunks based on character count
            chunks = []
            current_chunk = ""
            for line in code.split('\n'):
                if len(current_chunk) + len(line) + 1 <= max_chars:
                    current_chunk += line + '\n'
                else:
                    chunks.append(current_chunk)
                    current_chunk = line + '\n'
            if current_chunk:
                chunks.append(current_chunk)
            
            modified_chunks = []
            for chunk in chunks:
                prompt = f"Add Google-style docstrings to all functions and classes in this Python code that don't have them. Do not modify existing docstrings:\n\n{chunk}"
                # Check prompt size before sending
                if len(prompt) > 10000:  # Approx 2500 tokens
                    print(f"Skipping chunk due to excessive prompt size ({len(prompt)} chars).")
                    modified_chunks.append(chunk)  # Keep original chunk
                    continue
                response = client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=prompt,
                    temperature=0.2,
                    max_tokens=2048,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                modified_chunks.append(response.choices[0].text)
            return '\n'.join(modified_chunks)
        else:
            prompt = f"Add Google-style docstrings to all functions and classes in this Python code that don't have them. Do not modify existing docstrings:\n\n{code}"
            # Check prompt size
            if len(prompt) > 10000:
                print(f"Skipping file due to excessive prompt size ({len(prompt)} chars).")
                return code
            response = client.completions.create(
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
        print(f"OpenAI API error: {e}")
        return code
    except Exception as e:
        print(f"Unexpected error generating docstrings: {e}")
        return code

def extract_docstrings(modified_code):
    """
    Extract docstrings from the modified code for functions and classes.
    Args:
        modified_code (str): Python code with added docstrings.
    Returns:
        dict: Dictionary mapping function/class names to their docstrings, or empty dict if error.
    """
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
        print(f"Syntax error in code, skipping: {e}")
        return {}  # Return empty dict to skip invalid files
    except Exception as e:
        print(f"Unexpected error extracting docstrings: {e}")
        return {}
    
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