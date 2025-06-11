from django.shortcuts import render
from .utils import get_files, get_file_content, generate_docstrings, extract_docstrings, generate_readme, generate_readme_from_code

def home(request):
    if request.method == 'POST':
        if 'from_github' in request.POST:
            repo_url = request.POST.get('github_url')
            if not repo_url:
                return render(request, 'home.html', {'error': 'Please provide a repository URL.'})
            files = get_files(repo_url)
            if not files:
                return render(request, 'home.html', {'error': 'No files found in the repository.'})
            documentation = {}
            for file_path in files[:5]:
                content = get_file_content(repo_url, file_path)
                if content:
                    modified_code = generate_docstrings(content, file_path)
                    docstrings = extract_docstrings(modified_code, file_path)
                    if docstrings:
                        documentation[file_path] = docstrings
            readme_content = generate_readme(repo_url, files)
            source = f"GitHub repository: {repo_url}"
        elif 'from_code' in request.POST:
            code = request.POST.get('code')
            if not code:
                return render(request, 'home.html', {'error': 'Please paste some code.'})
            file_path = "pasted_code.py"  # Default to Python
            modified_code = generate_docstrings(code, file_path)
            docstrings = extract_docstrings(modified_code, file_path)
            documentation = {file_path: docstrings} if docstrings else {}
            readme_content = generate_readme_from_code(code)
            source = "Pasted Code"
        else:
            return render(request, 'home.html', {'error': 'Invalid submission.'})
        
        return render(request, 'docs.html', {
            'documentation': documentation,
            'readme': readme_content,
            'source': source
        })
    
    return render(request, 'home.html')