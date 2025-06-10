from django.shortcuts import render
from .utils import get_python_files, get_file_content, generate_docstrings, extract_docstrings, generate_readme

def home(request):
    """
    Render the home page and handle repository URL submission.
    """
    if request.method == 'POST':
        repo_url = request.POST.get('repo_url')
        if not repo_url:
            return render(request, 'home.html', {'error': 'Please provide a repository URL.'})
        
        python_files = get_python_files(repo_url)
        if not python_files:
            return render(request, 'home.html', {'error': 'No Python files found in the repository.'})
        
        documentation = {}
        errors = []
        for file_path in python_files[:5]:  # Limit to 5 files
            content = get_file_content(repo_url, file_path)
            if content:
                try:
                    modified_code = generate_docstrings(content)
                    docstrings = extract_docstrings(modified_code)
                    if docstrings:
                        documentation[file_path] = docstrings
                    else:
                        errors.append(f"No docstrings generated for {file_path}.")
                except Exception as e:
                    errors.append(f"Error processing {file_path}: {str(e)}")
            else:
                errors.append(f"Failed to fetch content for {file_path}.")
        
        # Generate README
        readme_content = generate_readme(repo_url, python_files)
        
        if not documentation and not readme_content.startswith("Failed"):
            return render(request, 'home.html', {'error': 'No docstrings generated. Try another repository.', 'errors': errors})
        
        return render(request, 'docs.html', {
            'documentation': documentation,
            'repo_url': repo_url,
            'readme': readme_content,
            'errors': errors
        })
    
    return render(request, 'home.html')