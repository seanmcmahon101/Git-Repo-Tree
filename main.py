import streamlit as st
import requests
from urllib.parse import urlparse
import re

def get_repo_info(repo_url):
    """
    Extracts the owner and repository name from the GitHub URL.
    """
    
    repo_url = repo_url.rstrip('.git')
    #f it, it works
    pattern = r'github\.com[:/](?P<owner>[\w\-\._]+)/(?P<repo>[\w\-\._]+)'
    match = re.search(pattern, repo_url)
    if match:
        owner = match.group('owner')
        repo = match.group('repo')
        return owner, repo
    else:
        return None, None

def get_branches(owner, repo):
    """
    Retrieves the list of branches from the GitHub API.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/branches'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        branches_data = response.json()
        branches = [branch['name'] for branch in branches_data]
        return branches
    else:
        return None

def get_tree(owner, repo, branch='master'):
    """
    Retrieves the repository tree from the GitHub API.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def build_tree(data):
    """
    Builds a nested dictionary representing the directory structure.
    """
    tree = {}
    for item in data['tree']:
        if item['type'] == 'tree' or item['type'] == 'blob':
            path_parts = item['path'].split('/')
            current_level = tree
            for part in path_parts:
                current_level = current_level.setdefault(part, {})
    return tree

def print_tree(tree, prefix=''):
    """
    Prints the directory structure in a tree-like format.
    """
    lines = []
    items = sorted(tree.items())
    for index, (key, subtree) in enumerate(items):
        if index == len(items) - 1:
            connector = '└── '
            next_prefix = prefix + '    '
        else:
            connector = '├── '
            next_prefix = prefix + '│   '
        lines.append(f"{prefix}{connector}{key}")
        if isinstance(subtree, dict) and subtree:
            lines.extend(print_tree(subtree, next_prefix))
    return lines

def main():
    st.title("GitHub Repository Directory Layout")

    st.write("Enter a GitHub repository URL to display its directory layout.")
    repo_url = st.text_input("GitHub Repository URL", "")

    if repo_url:
        owner, repo = get_repo_info(repo_url)
        if owner and repo:
            st.write(f"**Repository**: {owner}/{repo}")
            with st.spinner('Fetching branches...'):
                branches = get_branches(owner, repo)
            if branches:
                default_branch = 'master' if 'master' in branches else branches[0]
                branch = st.selectbox("Select Branch", options=branches, index=branches.index(default_branch) if default_branch in branches else 0)
                st.write(f"Selected branch: **{branch}**")
                if st.button("Show Directory Layout"):
                    st.write(f"Fetching directory layout for **{owner}/{repo}** on branch **{branch}**...")
                    with st.spinner('Fetching repository data...'):
                        tree_data = get_tree(owner, repo, branch)
                    if tree_data:
                        tree = build_tree(tree_data)
                        tree_lines = print_tree(tree)
                        st.code('\n'.join(tree_lines), language='text')
                    else:
                        st.error("Failed to retrieve repository data. Please check the repository URL and branch name.")
            else:
                st.error("Failed to retrieve branches. Please check the repository URL.")
        else:
            st.error("Invalid GitHub repository URL.")
    else:
        st.write("Please enter a GitHub repository URL.")

    st.sidebar.header("Options")
    st.sidebar.markdown("Adjust the settings as needed.")

if __name__ == "__main__":
    main()
