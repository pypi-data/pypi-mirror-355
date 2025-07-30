"""Module for file operations."""

import os
import shutil
from pathlib import Path
from prometheus_swarm.tools.git_operations.implementations import commit_and_push
from git import Repo
from prometheus_swarm.types import ToolOutput


def _normalize_path(path: str) -> str:
    """Helper function to normalize paths by stripping leading slashes."""
    return path.lstrip("/")


def read_file(file_path: str, **kwargs) -> ToolOutput:
    """
    Read the contents of a file.

    Args:
        file_path (str): Path to the file to read

    Returns:
        ToolOutput: A dictionary containing:
            - success (bool): Whether the operation succeeded
            - message (str): A human readable message
            - data (dict): The file contents if successful
    """
    try:
        file_path = _normalize_path(file_path)
        full_path = Path(os.getcwd()) / file_path
        with open(full_path, "r") as f:
            content = f.read()
            return {
                "success": True,
                "message": f"Successfully read file {file_path}",
                "data": {"content": content},
            }
    except FileNotFoundError:
        return {
            "success": False,
            "message": f"File not found: {file_path}",
            "data": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reading file: {str(e)}",
            "data": None,
        }


def write_file(
    file_path: str, content: str, commit_message: str = None, **kwargs
) -> ToolOutput:
    """Write file with directory creation and optional commit"""
    try:
        file_path = _normalize_path(file_path)
        full_path = Path(os.getcwd()) / file_path

        # First verify we can create the directory
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not full_path.parent.exists():
                return {
                    "success": False,
                    "message": f"Failed to create directory {full_path.parent} - directory does not exist after creation",
                    "data": None,
                }
            if not os.access(full_path.parent, os.W_OK):
                return {
                    "success": False,
                    "message": f"No write permission for directory {full_path.parent}",
                    "data": None,
                }
        except Exception as dir_error:
            return {
                "success": False,
                "message": f"Failed to create directory {full_path.parent}: {str(dir_error)}",
                "data": None,
            }

        # Write the file
        try:
            with open(full_path, "w") as f:
                f.write(content)
        except Exception as write_error:
            return {
                "success": False,
                "message": f"Failed to write file {file_path}: {str(write_error)}",
                "data": None,
            }

        # Verify the file was written successfully
        if not full_path.exists():
            return {
                "success": False,
                "message": f"Failed to write file {file_path} (file does not exist after write)",
                "data": None,
            }
        if (
            full_path.stat().st_size == 0 and content
        ):  # Only check if content was provided
            return {
                "success": False,
                "message": f"Failed to write file {file_path} (file is empty)",
                "data": None,
            }

        # If commit message provided, commit and push changes
        if commit_message:
            commit_result = commit_and_push(commit_message)
            if not commit_result["success"]:
                return commit_result

        return {
            "success": True,
            "message": f"Successfully wrote to file {file_path}",
            "data": {"path": file_path},
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error writing file {file_path}: {str(e)}",
            "data": None,
        }


def copy_file(
    source: str, destination: str, commit_message: str = None, **kwargs
) -> ToolOutput:
    """Copy a file and optionally commit the change."""
    try:
        source = _normalize_path(source)
        destination = _normalize_path(destination)
        source_path = Path(os.getcwd()) / source
        dest_path = Path(os.getcwd()) / destination

        if not source_path.exists():
            return {
                "success": False,
                "message": "Source file not found",
                "data": None,
            }

        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest_path)

        # If commit message provided, commit and push changes
        if commit_message:
            commit_result = commit_and_push(commit_message)
            if not commit_result["success"]:
                return commit_result

        return {
            "success": True,
            "message": f"Successfully copied file from {source} to {destination}",
            "data": {"source": source, "destination": destination},
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None,
        }


def move_file(
    source: str, destination: str, commit_message: str = None, **kwargs
) -> ToolOutput:
    """Move a file and optionally commit the change."""
    try:
        source = _normalize_path(source)
        destination = _normalize_path(destination)
        source_path = Path(os.getcwd()) / source
        dest_path = Path(os.getcwd()) / destination

        if not source_path.exists():
            return {
                "success": False,
                "message": "Source file not found",
                "data": None,
            }

        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source_path), str(dest_path))

        # If commit message provided, commit and push changes
        if commit_message:
            commit_result = commit_and_push(commit_message)
            if not commit_result["success"]:
                return commit_result

        return {
            "success": True,
            "message": f"Successfully moved file from {source} to {destination}",
            "data": {"source": source, "destination": destination},
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None,
        }


def rename_file(
    source: str, destination: str, commit_message: str = None
) -> ToolOutput:
    """Rename a file and optionally commit the change."""
    try:
        source = _normalize_path(source)
        destination = _normalize_path(destination)
        source_path = Path(os.getcwd()) / source
        dest_path = Path(os.getcwd()) / destination

        if not source_path.exists():
            return {
                "success": False,
                "message": f"Source file not found: {source}",
                "data": None,
            }

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        os.rename(source_path, dest_path)

        # If commit message provided, commit and push changes
        if commit_message:
            commit_result = commit_and_push(commit_message)
            if not commit_result["success"]:
                return commit_result

        return {
            "success": True,
            "message": f"Successfully renamed file from {source} to {destination}",
            "data": {"source": source, "destination": destination},
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error renaming file: {str(e)}",
            "data": None,
        }


def delete_file(file_path: str, commit_message: str = None, **kwargs) -> ToolOutput:
    """Delete a file and optionally commit the change."""
    try:
        file_path = _normalize_path(file_path)
        full_path = Path(os.getcwd()) / file_path

        if not full_path.exists():
            return {
                "success": False,
                "message": "File not found",
                "data": None,
            }

        os.remove(full_path)

        # If commit message provided, commit and push changes
        if commit_message:
            commit_result = commit_and_push(commit_message)
            if not commit_result["success"]:
                return commit_result

        return {
            "success": True,
            "message": f"Successfully deleted file: {file_path}",
            "data": {"path": file_path},
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None,
        }


def list_files(directory: str, **kwargs) -> ToolOutput:
    """
    Return a list of all files in the specified directory and its subdirectories,
    excluding .git directory and node_modules directory, and respecting .gitignore.

    Parameters:
    directory (str or Path): The directory to search for files.

    Returns:
        ToolOutput: A dictionary containing:
            - success (bool): Whether the operation succeeded
            - message (str): A human readable message
            - data (dict): Dictionary containing list of files if successful
    """
    try:
        directory = _normalize_path(directory)
        directory = Path(os.getcwd()) / directory

        if not directory.exists():
            return {
                "success": False,
                "message": f"Directory does not exist: {directory}",
                "data": None,
            }

        if not directory.is_dir():
            return {
                "success": False,
                "message": f"Path exists but is not a directory: {directory}",
                "data": None,
            }

        # Use git to list all tracked and untracked files, respecting .gitignore
        try:
            repo = Repo(directory)
        except Exception as e:
            # If not a git repo, just list files normally
            files = []
            for root, _, filenames in os.walk(directory):
                rel_root = os.path.relpath(root, directory)
                # Skip node_modules directory
                if "node_modules" in rel_root.split(os.sep):
                    continue
                for filename in filenames:
                    if rel_root == ".":
                        files.append(filename)
                    else:
                        files.append(os.path.join(rel_root, filename))
            return {
                "success": True,
                "message": f"Found {len(files)} files in {directory}",
                "data": {"files": sorted(files)},
            }

        # Get tracked files
        tracked_files = set(repo.git.ls_files().splitlines())

        # Get untracked files (excluding .gitignored)
        untracked_files = set(
            repo.git.ls_files("--others", "--exclude-standard").splitlines()
        )

        # Combine and filter out .git directory and node_modules
        all_files = tracked_files.union(untracked_files)
        files = sorted(
            [
                f
                for f in all_files
                if not f.startswith(".git/") and not "node_modules" in f.split("/")
            ]
        )

        return {
            "success": True,
            "message": f"Found {len(files)} files in {directory}",
            "data": {"files": files},
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing files: {str(e)}",
            "data": None,
        }


def list_directory_contents(directory: str, **kwargs) -> ToolOutput:
    """
    Return a list of files and directories in the specified directory (no subdirectories),
    excluding .git directory and node_modules directory. For files, includes their line count.

    Parameters:
    directory (str or Path): The directory to list contents from.

    Returns:
        ToolOutput: A dictionary containing:
            - success (bool): Whether the operation succeeded
            - message (str): A human readable message
            - data (dict): Dictionary containing lists of files and directories if successful
    """
    try:
        directory = _normalize_path(directory)
        directory = Path(os.getcwd()) / directory

        if not directory.exists():
            return {
                "success": False,
                "message": f"Directory does not exist: {directory}",
                "data": None,
            }

        if not directory.is_dir():
            return {
                "success": False,
                "message": f"Path exists but is not a directory: {directory}",
                "data": None,
            }

        # List files and directories in current directory
        files = []
        directories = []
        for item in directory.iterdir():
            if item.is_file():
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    files.append({"name": item.name, "lines": line_count})
                except Exception:
                    # If we can't read the file, just add it without line count
                    files.append({"name": item.name, "lines": None})
            elif item.is_dir():
                directories.append(item.name)

        return {
            "success": True,
            "message": f"Found {len(files)} files and {len(directories)} directories in {directory}",
            "data": {
                "files": sorted(files, key=lambda x: x["name"]),
                "directories": sorted(directories)
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing directory contents: {str(e)}",
            "data": None,
        }


def create_directory(path: str, **kwargs) -> ToolOutput:
    """Create a directory and any necessary parent directories.

    Args:
        path (str): Path to the directory to create

    Returns:
        ToolOutput: A dictionary containing:
            - success (bool): Whether the operation succeeded
            - message (str): A human readable message
            - data (dict): Dictionary containing path if successful
    """
    try:
        path = _normalize_path(path)
        full_path = Path(os.getcwd()) / path
        full_path.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "message": f"Created directory: {path}",
            "data": {"path": path},
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create directory: {str(e)}",
            "data": None,
        }
