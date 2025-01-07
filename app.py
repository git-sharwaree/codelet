import requests
import re
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


# Function to fetch GitHub repo content using the GitHub API
def fetch_github_repo_content(github_url):
    match = re.search(r"github.com/([^/]+)/([^/]+)", github_url)
    if not match:
        return None  # Invalid URL
    
    user, repo = match.groups()
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents"

    # Add authentication using the GitHub token
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"  # Replace with your token
    }

    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"GitHub API Error: {response.status_code} - {response.json().get('message')}")
        return None


# Function to extract functions, classes, and methods from the code (supports multiple languages)
def extract_code_details(code, language):
    functions = []
    classes = []
    if language == 'python':
        functions = re.findall(r"def (\w+)\(", code)  # Extract function names
        classes = re.findall(r"class (\w+)", code)   # Extract class names
    elif language == 'javascript':
        functions = re.findall(r"function (\w+)\(", code)  # Extract function names
        classes = re.findall(r"class (\w+)", code)        # Extract class names
    elif language == 'java':
        functions = re.findall(r"public\s+[\w<>,]+\s+(\w+)\(", code)  # Extract method names
        classes = re.findall(r"class (\w+)", code)  # Extract class names
    elif language == 'csharp':
        functions = re.findall(r"public\s+[\w<>,]+\s+(\w+)\(", code)  # Extract method names
        classes = re.findall(r"class (\w+)", code)  # Extract class names
    return functions, classes

# Function to analyze code using Gemini API
def analyze_code_with_gemini(code, language):
    if language == 'python':
        prompt = f"Analyze the following Python code and summarize the functions, classes, and methods:\n\n{code}"
    elif language == 'javascript':
        prompt = f"Analyze the following JavaScript code and summarize the functions, classes, and methods:\n\n{code}"
    elif language == 'java':
        prompt = f"Analyze the following Java code and summarize the functions, classes, and methods:\n\n{code}"
    elif language == 'csharp':
        prompt = f"Analyze the following C# code and summarize the functions, classes, and methods:\n\n{code}"
    else:
        prompt = f"Analyze the following code and summarize the functions, classes, and methods:\n\n{code}"

    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generation_config": {
            "max_output_tokens": 500,
            "temperature": 0.7
        }
    }
    params = {"key": GEMINI_API_KEY}

    response = requests.post(api_url, headers=headers, json=payload, params=params)
    if response.status_code == 200:
        output = response.json()
        if 'candidates' in output and output['candidates']:
            return output['candidates'][0]['content']['parts'][0]['text']
        else:
            return 'Error in generating analysis: No candidates found in response.'
    else:
        return f"API Error: {response.status_code} - {response.text}"

# Streamlit app to display GitHub project details
def display_github_analysis():
    st.title("GitHub Repository Code Analyzer")
    github_url = st.text_input('Enter GitHub Repo URL')

    if github_url:
        repo_content = fetch_github_repo_content(github_url)
        if repo_content:
            file_names = [file['name'] for file in repo_content]
            selected_file = st.selectbox('Choose a file', file_names)

            if selected_file:
                file_url = next(file['download_url'] for file in repo_content if file['name'] == selected_file)
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    code_content = file_response.text
                    language = selected_file.split('.')[-1].lower()
                    functions, classes = extract_code_details(code_content, language)
                    analysis = analyze_code_with_gemini(code_content, language)

                    st.subheader("Functions:")
                    st.write(functions)

                    st.subheader("Classes:")
                    st.write(classes)

                    st.subheader("Code Analysis:")
                    st.write(analysis)
                else:
                    st.error("Failed to fetch file content.")
        else:
            st.error("Failed to fetch repository content. Please check the URL.")
    
# Run the Streamlit app
if __name__ == "__main__":
    display_github_analysis()
