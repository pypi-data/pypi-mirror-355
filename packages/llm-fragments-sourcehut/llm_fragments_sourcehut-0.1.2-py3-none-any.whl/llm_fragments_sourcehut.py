from typing import List
import llm
import os
import pathlib
import subprocess
import tempfile


@llm.hookimpl
def register_fragment_loaders(register):
    register("srht", srht_loader)


def srht_loader(argument: str) -> List[llm.Fragment]:
    """
    Load files from a SourceHut repository as fragments

    Argument is a SourceHut repository URL or ~user/repo
    """
    # Normalize the repository argument
    if argument.startswith("~"):
        repo_url = f"https://git.sr.ht/{argument}"
    elif not argument.startswith(("http://", "https://")):
        # Fallback for user/repo, though ~user/repo is standard
        repo_url = f"https://git.sr.ht/~{argument}"
    else:
        repo_url = argument

    # Create a temporary directory to clone the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", "--depth=1", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True,
            )

            # Process the cloned repository
            repo_path = pathlib.Path(temp_dir)
            fragments = []

            # Walk through all files in the repository, excluding .git directory
            for root, dirs, files in os.walk(repo_path):
                # Remove .git from dirs to prevent descending into it
                if ".git" in dirs:
                    dirs.remove(".git")

                # Process files
                for file in files:
                    file_path = pathlib.Path(root) / file
                    if file_path.is_file():
                        try:
                            # Try to read the file as UTF-8
                            content = file_path.read_text(encoding="utf-8")

                            # Create a relative path for the fragment identifier
                            relative_path = file_path.relative_to(repo_path)

                            # Add the file as a fragment
                            fragments.append(
                                llm.Fragment(
                                    content, f"{argument}/{relative_path}"
                                )
                            )
                        except UnicodeDecodeError:
                            # Skip files that can't be decoded as UTF-8
                            continue

            return fragments
        except subprocess.CalledProcessError as e:
            # Handle Git errors
            raise ValueError(
                f"Failed to clone repository {repo_url}: {e.stderr}"
            )
        except Exception as e:
            # Handle other errors
            raise ValueError(
                f"Error processing repository {repo_url}: {str(e)}"
            )
