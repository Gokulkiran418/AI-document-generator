# AI-Powered Documentation Generator
A Django-based web application that automatically generates Google-style docstrings and README files for repositories using OpenAI’s API and GitHub integration.

# Description
This project is a user-friendly tool designed to streamline documentation for projects hosted on GitHub. By inputting a repository URL, users can generate detailed docstrings for functions and classes, as well as a professional README file. The app features a modern interface styled with Bootstrap 5.3.3, a progress indicator, and a download option for the generated README.

# Features
- GitHub Integration: Fetches files from any public GitHub repository.
- Docstring Generation: Automatically adds Google-style docstrings using OpenAI’s gpt-3.5-turbo-instruct model.
- README Generation: Creates a professional Markdown README with project details.
- Modern UI: Responsive design with Bootstrap 5.3.3
- Download Option: Allows users to download the generated README as a .md file.
- Error Handling: Skips invalid files and displays errors in the UI.

# Prerequisites
- Python 3.10 or higher
- PostgreSQL 14 or higher
- OpenAI API key (get from OpenAI Platform)
- GitHub Personal Access Token (optional, for private repositories)

# Requirements
Install in virtual environment
- django
- openai
- requests
- psycopg2-binary
- asttokens
- python-dotenv
- httpx