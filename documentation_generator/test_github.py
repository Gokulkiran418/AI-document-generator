from docs_generator.utils import get_python_files, get_file_content
repo_url = "https://github.com/python/cpython"  # Replace with a public repository URL for testing
python_files = get_python_files(repo_url)
print("Python files found:", python_files)

if python_files:
    content = get_file_content(repo_url, python_files[0])
    print("Content of first file:\n", content[:500])  # Print first 500 characters