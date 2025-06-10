from docs_generator.utils import get_python_files, get_file_content, generate_docstrings, extract_docstrings

repo_url = "https://github.com/pallets/flask"  # Use a small public Python repo
python_files = get_python_files(repo_url)
if python_files:
    file_path = python_files[0]  # Test with the first Python file
    content = get_file_content(repo_url, file_path)
    if content:
        modified_code = generate_docstrings(content)
        docstrings = extract_docstrings(modified_code)
        print(f"Docstrings for {file_path}:\n", docstrings)
    else:
        print("Failed to fetch file content.")
else:
    print("No Python files found in repository.")