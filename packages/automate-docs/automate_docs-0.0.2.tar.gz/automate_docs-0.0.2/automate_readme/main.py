"""
Enhanced README Generator
Clones repository, extracts project tree and file contents, sends to Liberty GPT AI, rewrites README in the cloned repo.
"""

import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# File extensions to include in content extraction
INCLUDE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
    '.md', '.txt', '.yml', '.yaml', '.json', '.xml', '.sql', '.sh', '.bat',
    '.dockerfile', '.gitignore', '.env.example', '.conf', '.ini', '.toml'
}

# Directories to ignore
IGNORE_DIRS = {
    '__pycache__', '*.pyc', '.git', 'node_modules', 'venv', 'env', 'build',
    'dist', 'migrations', 'static', '.pytest_cache', '.coverage', 'htmlcov',
    '.vscode', '.idea', 'logs', 'tmp', 'temp', '.DS_Store', 'Thumbs.db'
}

# Files to ignore
IGNORE_FILES = {
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib', '*.log',
    '*.sqlite', '*.sqlite3', '*.db', '*.jpg', '*.jpeg', '*.png', '*.gif',
    '*.ico', '*.svg', '*.pdf', '*.zip', '*.tar.gz', '*.exe', '*.bin'
}


def clone_repository(repo_url: str, target_dir: str) -> bool:
    """Clone repository to target directory"""
    try:
        print(f"🔄 Cloning repository: {repo_url}")
        result = subprocess.run([
            "git", "clone", repo_url, target_dir
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ Repository cloned successfully to: {target_dir}")
            return True
        else:
            print(f"❌ Git clone failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return False
    except Exception as e:
        print(f"❌ Error cloning repository: {e}")
        return False


def get_project_tree(project_path: str, output_file: str) -> str:
    """Get project tree and save to file"""
    try:
        print(f"🌳 Generating project tree for: {project_path}")

        # Build ignore pattern for tree command
        ignore_pattern = "|".join(IGNORE_DIRS)

        result = subprocess.run([
            "tree",
            "-I", ignore_pattern,
            "-L", "5",  # Increased depth
            "-a",  # Show hidden files
            project_path
        ], capture_output=True, text=True, timeout=60)

        tree_output = ""
        if result.returncode == 0:
            tree_output = result.stdout
        else:
            print(f"⚠️ Tree command failed, using fallback: {result.stderr}")
            tree_output = get_fallback_tree(project_path)

        # Save tree to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(tree_output)

        print(f"💾 Project tree saved to: {output_file}")
        return tree_output

    except Exception as e:
        print(f"❌ Error generating tree: {e}")
        fallback_tree = get_fallback_tree(project_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fallback_tree)
        return fallback_tree


def get_fallback_tree(project_path: str) -> str:
    """Fallback tree generation using Python"""
    try:
        tree_lines = []
        path = Path(project_path)

        def add_to_tree(current_path: Path, prefix: str = "", depth: int = 0):
            if depth > 4:  # Limit depth
                return

            items = []
            try:
                for item in current_path.iterdir():
                    if not should_ignore_path(item):
                        items.append(item)
            except PermissionError:
                return

            items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    add_to_tree(item, next_prefix, depth + 1)

        tree_lines.append(path.name + "/")
        add_to_tree(path)
        return "\n".join(tree_lines)

    except Exception as e:
        return f"Could not generate tree structure: {e}"


def should_ignore_path(path: Path) -> bool:
    """Check if path should be ignored"""
    name = path.name

    # Check against ignore directories
    if path.is_dir() and name in IGNORE_DIRS:
        return True

    # Check against ignore files patterns
    for pattern in IGNORE_FILES:
        if pattern.startswith('*.'):
            ext = pattern[1:]  # Remove *
            if name.endswith(ext):
                return True
        elif name == pattern:
            return True

    # Hidden files (except important ones)
    if name.startswith('.') and name not in {'.env.example', '.gitignore', '.dockerignore'}:
        return True

    return False


def extract_file_contents(project_path: str, output_file: str) -> str:
    """Extract content from relevant files in the project"""
    try:
        print(f"📄 Extracting file contents from: {project_path}")

        project_path = Path(project_path)
        all_content = []
        file_count = 0

        # Walk through project directory
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and not should_ignore_path(file_path):

                # Check if file extension should be included
                if file_path.suffix.lower() in INCLUDE_EXTENSIONS or file_path.name in {
                    'Dockerfile', 'Makefile', 'requirements.txt', 'package.json',
                    'setup.py', 'pyproject.toml', 'README', 'LICENSE'
                }:

                    try:
                        # Get relative path from project root
                        relative_path = file_path.relative_to(project_path)

                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Skip very large files
                        if len(content) > 50000:  # 50KB limit
                            content = content[:50000] + "\n... [File truncated - too large] ..."

                        # Add to collection
                        all_content.append(f"\n{'=' * 80}")
                        all_content.append(f"FILE: {relative_path}")
                        all_content.append(f"{'=' * 80}")
                        all_content.append(content)

                        file_count += 1

                        # Limit total files to prevent overwhelming Liberty GPT
                        if file_count >= 100:
                            all_content.append(f"\n... [Stopped after {file_count} files to prevent overwhelming] ...")
                            break

                    except Exception as e:
                        print(f"⚠️ Could not read {file_path}: {e}")
                        continue

        # Combine all content
        combined_content = "\n".join(all_content)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)

        print(f"💾 File contents extracted ({file_count} files) and saved to: {output_file}")
        return combined_content

    except Exception as e:
        print(f"❌ Error extracting file contents: {e}")
        return f"Error extracting file contents: {e}"


def backup_existing_readme(clone_dir: Path) -> Optional[Path]:
    """Backup existing README if it exists"""
    try:
        readme_variants = ['README.md', 'README.txt', 'README.rst', 'README', 'readme.md', 'readme.txt']

        for readme_name in readme_variants:
            readme_path = clone_dir / readme_name
            if readme_path.exists():
                backup_path = clone_dir / f"{readme_name}.backup"
                shutil.copy2(readme_path, backup_path)
                print(f"📋 Backed up existing README: {readme_name} -> {readme_name}.backup")
                return readme_path

        print("ℹ️ No existing README found to backup")
        return None
    except Exception as e:
        print(f"⚠️ Error backing up README: {e}")
        return None


def create_gpt_prompt(tree: str, file_contents: str, repo_url: str = "") -> str:
    """Create comprehensive prompt for Liberty GPT AI"""

    # Truncate content if too long to fit in context
    max_tree_length = 5000
    max_content_length = 100000

    if len(tree) > max_tree_length:
        tree = tree[:max_tree_length] + "\n... [Tree truncated] ..."

    if len(file_contents) > max_content_length:
        file_contents = file_contents[:max_content_length] + "\n... [Content truncated] ..."

    repo_info = f"\nRepository URL: {repo_url}\n" if repo_url else ""

    return f"""Write a comprehensive README.md file for this project.

{repo_info}
PROJECT STRUCTURE:
```
{tree}
```

FILE CONTENTS:
```
{file_contents}
```

Create a professional README.md with the following sections:
1. Project title and clear description
2. Key features and functionality
3. Technology stack used(accordign to the file_contents)
4. Installation instructions
5. Usage examples and documentation
6. Project structure overview
7. Configuration details (if applicable)
8. Contributing guidelines (if applicable)
9. License information (if applicable)

Analyze the code structure and dependencies to provide accurate setup instructions.
Make the README informative, well-structured, and professional.
Use appropriate markdown formatting with headers, code blocks, and lists.

Return only the README content in markdown format - no additional text or wrapping.
"""


def write_readme_to_repo(content: str, clone_dir: Path) -> bool:
    """Write README content to the cloned repository"""
    try:
        readme_path = clone_dir / "README.md"
        print(f"✏️ Writing README.md to cloned repository: {readme_path}")

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ README.md written successfully to: {readme_path}")
        return True

    except Exception as e:
        print(f"❌ Error writing README to repository: {e}")
        return False


def chat_with_liberty_gpt_for_readme(prompt: str) -> str:
    """
    Wrapper for Liberty GPT API call - replace with your implementation
    """
    try:
        from .request import chat_with_liberty_gpt 
        response = chat_with_liberty_gpt(prompt)
        return str(response)

        # Placeholder for testing
        # return "# Sample README\n\nThis is a placeholder README generated from the project analysis."

    except Exception as e:
        print(f"❌ Error calling Liberty GPT: {e}")
        return f"# README Generation Failed\n\nError: {e}"



def main():
    """Main function with interactive user inputs instead of command line arguments"""
    try:
        # Prompt user for inputs
        print("MAKE SURE TO HAVE A .env FILE WITH YOUR CORTEX LIBERTY GPT ACCESS TOKEN. THIS CAN BE FOUND HERE: '' ")

        repo_url = input("Enter Git repository URL to clone: ").strip()
        if not repo_url:
            print("Repository URL is required. Exiting.")
            return False

        output_dir_input = input("Output directory for analysis files [default: ./temp_repo_analysis]: ").strip()
        output_dir = Path(output_dir_input) if output_dir_input else Path("./temp_repo_analysis")

        keep_clone_input = input("Keep cloned repository after analysis? (y/N): ").strip().lower()
        keep_clone = keep_clone_input in ['y', 'yes']

        no_backup_input = input("Do not backup existing README file? (y/N): ").strip().lower()
        no_backup = no_backup_input in ['y', 'yes']


        # Create output directory
        output_dir.mkdir(exist_ok=True)

        # Paths for analysis files
        clone_dir = output_dir / "cloned_repo"
        tree_file = output_dir / "project_tree.txt"
        content_file = output_dir / "file_contents.txt"

        print(f"🚀 Starting README generation for: {repo_url}")

        # Step 1: Clone repository
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        if not clone_repository(repo_url, str(clone_dir)):
            return False

        # Step 2: Backup existing README if it exists (unless disabled)
        if not no_backup:
            backup_existing_readme(clone_dir)

        # Step 3: Generate project tree
        tree_content = get_project_tree(str(clone_dir), str(tree_file))

        # Step 4: Extract file contents
        file_contents = extract_file_contents(str(clone_dir), str(content_file))

        # Step 5: Create prompt and call Liberty GPT
        prompt = create_gpt_prompt(tree_content, file_contents, repo_url)
        print("🤖 Calling Liberty GPT AI to generate README...")
        Liberty_GPT_response = chat_with_liberty_gpt_for_readme(prompt)

        # Step 6: Write README to the cloned repository
        if not write_readme_to_repo(Liberty_GPT_response, clone_dir):
            return False

        # Final output information
        readme_location = clone_dir / "README.md"
        print(f"🎉 README generation completed successfully!")
        print(f"📁 Analysis files saved in: {output_dir}")
        print(f"📝 Generated README written to: {readme_location}")

        if keep_clone:
            print(f"📦 Cloned repository preserved at: {clone_dir}")
        else:
            print("🧹 Cloned repository will be cleaned up.")

        # Cleanup (only if not keeping clone)
        if not keep_clone:
            # Ask user if they want to keep the clone since README was written there
            try:
                response = input("\n❓ The README has been written to the cloned repository. Do you want to keep it? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    print(f"📦 Cloned repository preserved at: {clone_dir}")
                else:
                    shutil.rmtree(clone_dir)
                    print("🧹 Cleaned up cloned repository")
            except KeyboardInterrupt:
                print(f"\n📦 Cloned repository preserved at: {clone_dir}")

        return True

    except Exception as e:
        print(f"❌ Error in main process: {e}")
        return False


if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)
