"""
Git history tracking for TODO comments.
"""

import os
import re
from typing import List, Dict, Union, Optional
from datetime import datetime
import subprocess
from pathlib import Path


def get_git_root(path: str) -> Optional[str]:
    """
    Find the root directory of the git repository containing the given path.
    
    Args:
        path: Path to search from
        
    Returns:
        Git root directory path or None if not in a git repository
    """
    try:
        git_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=path,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        ).strip()
        return git_root
    except subprocess.CalledProcessError:
        return None


def get_file_history(file_path: str) -> List[Dict[str, Union[str, datetime]]]:
    """
    Get the git history for a specific file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of dictionaries containing commit information
    """
    git_root = get_git_root(os.path.dirname(file_path))
    if not git_root:
        return []
        
    relative_path = os.path.relpath(file_path, git_root)
    
    try:
        # Get all commits that modified this file
        log_output = subprocess.check_output(
            ['git', 'log', '--follow', '--format=%H|%an|%ae|%at|%s', '--', relative_path],
            cwd=git_root,
            universal_newlines=True
        ).strip()
        
        if not log_output:
            return []
            
        commits = []
        for line in log_output.split('\n'):
            if line:
                hash_, author, email, timestamp, subject = line.split('|')
                commits.append({
                    'hash': hash_,
                    'author': author,
                    'email': email,
                    'date': datetime.fromtimestamp(int(timestamp)),
                    'subject': subject
                })
        return commits
    except subprocess.CalledProcessError:
        return []


def get_todo_history(file_path: str, todo_pattern: str = r'(?:^|\s)#\s*(?:TODO|todo)[\s:-](.+)') -> List[Dict[str, Union[str, datetime, dict]]]:
    """
    Track the history of TODO comments in a file through git history.
    
    Args:
        file_path: Path to the file
        todo_pattern: Regex pattern to match TODO comments
        
    Returns:
        List of dictionaries containing TODO history information
    """
    git_root = get_git_root(os.path.dirname(file_path))
    if not git_root:
        return []
        
    relative_path = os.path.relpath(file_path, git_root)
    todo_regex = re.compile(todo_pattern, re.IGNORECASE)
    todo_history = []
    
    try:
        # Get all commits that modified this file
        commits = get_file_history(file_path)
        
        for commit in commits:
            try:
                # Get file content at this commit
                file_content = subprocess.check_output(
                    ['git', 'show', f'{commit["hash"]}:{relative_path}'],
                    cwd=git_root,
                    universal_newlines=True
                )
                
                # Find TODOs in this version
                current_todos = set()
                for line in file_content.split('\n'):
                    match = todo_regex.search(line)
                    if match and not line.strip().startswith(("'", '"', '"""', "'''")):
                        current_todos.add(match.group(1).strip())
                
                # Compare with previous version to find added/removed TODOs
                if todo_history:
                    prev_todos = set(item['todo'] for item in todo_history[-1]['todos'])
                    added = current_todos - prev_todos
                    removed = prev_todos - current_todos
                else:
                    added = current_todos
                    removed = set()
                
                if added or removed:
                    todo_history.append({
                        'commit': commit,
                        'todos': [{'todo': todo, 'status': 'added'} for todo in added] +
                                [{'todo': todo, 'status': 'removed'} for todo in removed]
                    })
                    
            except subprocess.CalledProcessError:
                continue
                
        return todo_history
    except subprocess.CalledProcessError:
        return []


def format_todo_history(todo_history: List[Dict[str, Union[str, datetime, dict]]], format_type: str = 'text') -> str:
    """
    Format TODO history into a readable format.
    
    Args:
        todo_history: List of TODO history entries
        format_type: Output format ('text' or 'markdown')
        
    Returns:
        Formatted string of TODO history
    """
    if not todo_history:
        return ""
        
    if format_type == 'markdown':
        output = []
        for entry in todo_history:
            commit = entry['commit']
            output.append(f"## Commit {commit['hash'][:8]}")
            output.append(f"**Author:** {commit['author']} ({commit['email']})")
            output.append(f"**Date:** {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}")
            output.append(f"**Subject:** {commit['subject']}")
            output.append("\n**Changes:**")
            
            for todo in entry['todos']:
                status = "✅ Added" if todo['status'] == 'added' else "❌ Removed"
                output.append(f"- {status}: {todo['todo']}")
            output.append("")
            
        return "\n".join(output)
    else:
        output = []
        for entry in todo_history:
            commit = entry['commit']
            output.append(f"[{commit['hash'][:8]}] {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}")
            output.append(f"Author: {commit['author']} ({commit['email']})")
            output.append(f"Subject: {commit['subject']}")
            output.append("Changes:")
            
            for todo in entry['todos']:
                status = "+" if todo['status'] == 'added' else "-"
                output.append(f"  {status} {todo['todo']}")
            output.append("")
            
        return "\n".join(output) 