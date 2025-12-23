"""
Version Control Integration for Synth Mind
Provides git-based project versioning with auto-commit, rollback, and changelog generation.
"""

import os
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class CommitType(Enum):
    """Types of commits for semantic commit messages."""
    PROJECT_START = "project"
    SUBTASK_COMPLETE = "feat"
    ITERATION = "wip"
    MILESTONE = "milestone"
    PAUSE = "pause"
    RESUME = "resume"
    EXIT = "exit"
    ROLLBACK = "revert"
    CONFIG_CHANGE = "config"
    FIX = "fix"


class VersionControlManager:
    """
    Manages version control operations for GDIL projects.
    Supports automatic commits, branching, and rollback.
    """

    def __init__(
        self,
        workspace_path: Optional[str] = None,
        auto_commit: bool = True,
        commit_on_subtask: bool = True,
        create_branches: bool = True,
        generate_changelog: bool = True
    ):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.auto_commit = auto_commit
        self.commit_on_subtask = commit_on_subtask
        self.create_branches = create_branches
        self.generate_changelog = generate_changelog

        # State tracking
        self.is_initialized = False
        self.current_project_branch: Optional[str] = None
        self.commit_history: List[Dict] = []

        # Check if git is available
        self.git_available = self._check_git_available()

    def _check_git_available(self) -> bool:
        """Check if git is available on the system."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _run_git(self, *args, cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """
        Run a git command and return (success, stdout, stderr).
        """
        if not self.git_available:
            return False, "", "Git not available"

        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=cwd or self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Git command timed out"
        except Exception as e:
            return False, "", str(e)

    def initialize_repo(self, project_path: Optional[Path] = None) -> Dict:
        """
        Initialize a git repository for a project.
        Returns status dict with success and message.
        """
        target_path = project_path or self.workspace_path

        if not self.git_available:
            return {
                "success": False,
                "message": "Git is not available on this system",
                "initialized": False
            }

        # Check if already a git repo
        git_dir = target_path / ".git"
        if git_dir.exists():
            self.is_initialized = True
            return {
                "success": True,
                "message": "Repository already initialized",
                "initialized": True,
                "existing": True
            }

        # Initialize new repo
        success, stdout, stderr = self._run_git("init", cwd=target_path)

        if success:
            self.is_initialized = True

            # Create initial .gitignore if it doesn't exist
            gitignore_path = target_path / ".gitignore"
            if not gitignore_path.exists():
                self._create_default_gitignore(gitignore_path)

            # Create initial commit
            self._run_git("add", ".gitignore", cwd=target_path)
            self._run_git(
                "commit", "-m", "Initial project setup",
                cwd=target_path
            )

            return {
                "success": True,
                "message": "Repository initialized successfully",
                "initialized": True,
                "existing": False
            }
        else:
            return {
                "success": False,
                "message": f"Failed to initialize: {stderr}",
                "initialized": False
            }

    def _create_default_gitignore(self, path: Path):
        """Create a default .gitignore file."""
        gitignore_content = """# Synth Mind generated .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.env

# State files (optional - remove if you want to track)
state/
*.db

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build
build/
dist/
*.egg-info/
"""
        path.write_text(gitignore_content)

    def create_project_branch(self, project_id: str, project_name: str) -> Dict:
        """
        Create a dedicated branch for a project.
        """
        if not self.git_available or not self.create_branches:
            return {"success": False, "message": "Branching disabled or git unavailable"}

        # Sanitize branch name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_name.lower())
        branch_name = f"synth/{project_id[:8]}-{safe_name[:20]}"

        # Check current branch
        success, current_branch, _ = self._run_git("rev-parse", "--abbrev-ref", "HEAD")

        # Create and checkout new branch
        success, stdout, stderr = self._run_git("checkout", "-b", branch_name)

        if success:
            self.current_project_branch = branch_name
            return {
                "success": True,
                "branch": branch_name,
                "previous_branch": current_branch,
                "message": f"Created and switched to branch: {branch_name}"
            }
        else:
            # Branch might already exist, try switching
            success, stdout, stderr = self._run_git("checkout", branch_name)
            if success:
                self.current_project_branch = branch_name
                return {
                    "success": True,
                    "branch": branch_name,
                    "message": f"Switched to existing branch: {branch_name}"
                }
            return {
                "success": False,
                "message": f"Failed to create branch: {stderr}"
            }

    def commit_changes(
        self,
        commit_type: CommitType,
        message: str,
        project_id: Optional[str] = None,
        subtask_name: Optional[str] = None,
        files: Optional[List[str]] = None,
        auto_stage: bool = True
    ) -> Dict:
        """
        Create a commit with semantic message format.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        if not self.auto_commit and commit_type not in [CommitType.MILESTONE, CommitType.EXIT]:
            return {"success": True, "message": "Auto-commit disabled", "skipped": True}

        # Stage files
        if auto_stage:
            if files:
                for f in files:
                    self._run_git("add", f)
            else:
                self._run_git("add", "-A")

        # Check if there are changes to commit
        success, status, _ = self._run_git("status", "--porcelain")
        if not status.strip():
            return {
                "success": True,
                "message": "No changes to commit",
                "skipped": True
            }

        # Build commit message
        scope = subtask_name or project_id or "project"
        full_message = f"{commit_type.value}({scope}): {message}"

        # Add metadata
        metadata = {
            "synth_commit": True,
            "commit_type": commit_type.value,
            "project_id": project_id,
            "subtask": subtask_name,
            "timestamp": time.time()
        }

        # Commit
        success, stdout, stderr = self._run_git(
            "commit", "-m", full_message,
            "-m", f"Synth-Meta: {json.dumps(metadata)}"
        )

        if success:
            # Get commit hash
            hash_success, commit_hash, _ = self._run_git("rev-parse", "HEAD")

            commit_record = {
                "hash": commit_hash if hash_success else "unknown",
                "type": commit_type.value,
                "message": message,
                "project_id": project_id,
                "subtask": subtask_name,
                "timestamp": time.time()
            }
            self.commit_history.append(commit_record)

            return {
                "success": True,
                "message": full_message,
                "hash": commit_hash if hash_success else None,
                "commit_record": commit_record
            }
        else:
            return {
                "success": False,
                "message": f"Commit failed: {stderr}"
            }

    def get_project_history(
        self,
        project_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get commit history, optionally filtered by project.
        """
        if not self.git_available:
            return []

        # Get log
        success, log_output, _ = self._run_git(
            "log", f"--max-count={limit}",
            "--format=%H|%s|%an|%ad|%b",
            "--date=iso"
        )

        if not success:
            return []

        commits = []
        for line in log_output.split("\n"):
            if "|" in line:
                parts = line.split("|", 4)
                if len(parts) >= 4:
                    commit = {
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                        "body": parts[4] if len(parts) > 4 else ""
                    }

                    # Check if synth commit and filter by project
                    if "Synth-Meta:" in commit.get("body", ""):
                        try:
                            meta_start = commit["body"].find("Synth-Meta:") + 11
                            meta_json = commit["body"][meta_start:].strip()
                            metadata = json.loads(meta_json)
                            commit["metadata"] = metadata

                            # Filter by project if specified
                            if project_id and metadata.get("project_id") != project_id:
                                continue
                        except:
                            pass

                    commits.append(commit)

        return commits

    def rollback_to_commit(
        self,
        commit_hash: str,
        soft: bool = True,
        create_backup_branch: bool = True
    ) -> Dict:
        """
        Rollback to a specific commit.
        Soft rollback keeps changes as staged, hard rollback discards.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        # Create backup branch if requested
        if create_backup_branch:
            timestamp = int(time.time())
            backup_branch = f"backup/{timestamp}"
            success, _, _ = self._run_git("branch", backup_branch)
            if success:
                backup_created = backup_branch
            else:
                backup_created = None
        else:
            backup_created = None

        # Perform rollback
        reset_type = "--soft" if soft else "--hard"
        success, stdout, stderr = self._run_git("reset", reset_type, commit_hash)

        if success:
            # Create rollback commit for audit trail
            if soft:
                self.commit_changes(
                    CommitType.ROLLBACK,
                    f"Rolled back to {commit_hash[:8]}",
                    auto_stage=True
                )

            return {
                "success": True,
                "message": f"Rolled back to {commit_hash[:8]}",
                "backup_branch": backup_created,
                "soft": soft
            }
        else:
            return {
                "success": False,
                "message": f"Rollback failed: {stderr}"
            }

    def rollback_subtask(self, project_id: str, subtask_name: str) -> Dict:
        """
        Rollback changes from a specific subtask.
        """
        # Find the commit before this subtask
        history = self.get_project_history(project_id)

        target_commit = None
        for i, commit in enumerate(history):
            metadata = commit.get("metadata", {})
            if metadata.get("subtask") == subtask_name:
                # Found the subtask commit, get the one before it
                if i + 1 < len(history):
                    target_commit = history[i + 1]["hash"]
                break

        if target_commit:
            return self.rollback_to_commit(target_commit, soft=True)
        else:
            return {
                "success": False,
                "message": f"Could not find commit for subtask: {subtask_name}"
            }

    def generate_changelog(
        self,
        project_id: Optional[str] = None,
        since_commit: Optional[str] = None,
        format_type: str = "markdown"
    ) -> str:
        """
        Generate a changelog from commit history.
        """
        history = self.get_project_history(project_id, limit=100)

        if since_commit:
            # Filter to commits after since_commit
            filtered = []
            found_start = False
            for commit in reversed(history):
                if commit["hash"].startswith(since_commit):
                    found_start = True
                    continue
                if found_start:
                    filtered.append(commit)
            history = list(reversed(filtered))

        if format_type == "markdown":
            return self._format_changelog_markdown(history)
        else:
            return self._format_changelog_text(history)

    def _format_changelog_markdown(self, commits: List[Dict]) -> str:
        """Format changelog as markdown."""
        if not commits:
            return "# Changelog\n\nNo commits found.\n"

        output = "# Changelog\n\n"

        # Group by type
        grouped = {}
        for commit in commits:
            metadata = commit.get("metadata", {})
            commit_type = metadata.get("commit_type", "other")
            if commit_type not in grouped:
                grouped[commit_type] = []
            grouped[commit_type].append(commit)

        # Format each group
        type_labels = {
            "feat": "Features",
            "fix": "Bug Fixes",
            "wip": "Work in Progress",
            "milestone": "Milestones",
            "project": "Project Setup",
            "pause": "Paused",
            "resume": "Resumed",
            "exit": "Completed",
            "revert": "Rollbacks",
            "config": "Configuration"
        }

        for commit_type, label in type_labels.items():
            if commit_type in grouped:
                output += f"## {label}\n\n"
                for commit in grouped[commit_type]:
                    date = commit.get("date", "")[:10]
                    msg = commit.get("message", "")
                    hash_short = commit.get("hash", "")[:8]
                    output += f"- [{hash_short}] {msg} ({date})\n"
                output += "\n"

        return output

    def _format_changelog_text(self, commits: List[Dict]) -> str:
        """Format changelog as plain text."""
        if not commits:
            return "Changelog\n=========\n\nNo commits found.\n"

        output = "Changelog\n=========\n\n"

        for commit in commits:
            date = commit.get("date", "")[:10]
            msg = commit.get("message", "")
            hash_short = commit.get("hash", "")[:8]
            output += f"[{hash_short}] {date} - {msg}\n"

        return output

    def get_diff(
        self,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict:
        """
        Get diff between commits or current changes.
        """
        if not self.git_available:
            return {"success": False, "diff": "", "message": "Git not available"}

        args = ["diff"]

        if commit1 and commit2:
            args.extend([commit1, commit2])
        elif commit1:
            args.append(commit1)

        if file_path:
            args.extend(["--", file_path])

        success, diff_output, stderr = self._run_git(*args)

        if success:
            return {
                "success": True,
                "diff": diff_output,
                "has_changes": bool(diff_output.strip())
            }
        else:
            return {
                "success": False,
                "diff": "",
                "message": stderr
            }

    def get_status(self) -> Dict:
        """
        Get current repository status.
        """
        if not self.git_available:
            return {
                "git_available": False,
                "initialized": False
            }

        # Check if repo exists
        success, _, _ = self._run_git("rev-parse", "--git-dir")
        if not success:
            return {
                "git_available": True,
                "initialized": False
            }

        # Get branch
        success, branch, _ = self._run_git("rev-parse", "--abbrev-ref", "HEAD")

        # Get status
        success, status, _ = self._run_git("status", "--porcelain")

        # Parse status
        staged = []
        modified = []
        untracked = []

        for line in status.split("\n"):
            if not line.strip():
                continue
            status_code = line[:2]
            file_path = line[3:]

            if status_code[0] in "MADRC":
                staged.append(file_path)
            if status_code[1] in "MD":
                modified.append(file_path)
            if status_code == "??":
                untracked.append(file_path)

        # Get commit count
        success, count, _ = self._run_git("rev-list", "--count", "HEAD")

        return {
            "git_available": True,
            "initialized": True,
            "branch": branch,
            "staged_files": staged,
            "modified_files": modified,
            "untracked_files": untracked,
            "has_changes": bool(staged or modified or untracked),
            "commit_count": int(count) if count.isdigit() else 0,
            "current_project_branch": self.current_project_branch
        }

    def switch_to_main(self) -> Dict:
        """
        Switch back to main/master branch.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        # Try main first, then master
        for branch in ["main", "master"]:
            success, _, _ = self._run_git("checkout", branch)
            if success:
                self.current_project_branch = None
                return {
                    "success": True,
                    "branch": branch,
                    "message": f"Switched to {branch}"
                }

        return {
            "success": False,
            "message": "Could not find main or master branch"
        }

    def stash_changes(self, message: Optional[str] = None) -> Dict:
        """
        Stash current changes.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])

        success, stdout, stderr = self._run_git(*args)

        return {
            "success": success,
            "message": stdout if success else stderr
        }

    def pop_stash(self) -> Dict:
        """
        Pop most recent stash.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        success, stdout, stderr = self._run_git("stash", "pop")

        return {
            "success": success,
            "message": stdout if success else stderr
        }

    def list_stashes(self) -> List[Dict]:
        """
        List all stashes.
        """
        if not self.git_available:
            return []

        success, stdout, _ = self._run_git("stash", "list")

        if not success or not stdout:
            return []

        stashes = []
        for line in stdout.split("\n"):
            if line.strip():
                # Format: stash@{0}: WIP on branch: message
                parts = line.split(":", 2)
                stashes.append({
                    "id": parts[0].strip() if parts else line,
                    "branch": parts[1].strip() if len(parts) > 1 else "",
                    "message": parts[2].strip() if len(parts) > 2 else ""
                })

        return stashes

    def merge_project_branch(
        self,
        target_branch: str = "main",
        delete_after: bool = False
    ) -> Dict:
        """
        Merge current project branch into target branch.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        if not self.current_project_branch:
            return {"success": False, "message": "No project branch active"}

        source_branch = self.current_project_branch

        # Switch to target
        success, _, stderr = self._run_git("checkout", target_branch)
        if not success:
            return {"success": False, "message": f"Could not switch to {target_branch}: {stderr}"}

        # Merge
        success, stdout, stderr = self._run_git("merge", source_branch, "--no-ff")

        if not success:
            # Abort merge on conflict
            self._run_git("merge", "--abort")
            self._run_git("checkout", source_branch)
            return {
                "success": False,
                "message": f"Merge conflict: {stderr}",
                "conflict": True
            }

        # Delete source branch if requested
        if delete_after:
            self._run_git("branch", "-d", source_branch)

        self.current_project_branch = None

        return {
            "success": True,
            "message": f"Merged {source_branch} into {target_branch}",
            "deleted_branch": delete_after
        }

    def get_file_history(self, file_path: str, limit: int = 10) -> List[Dict]:
        """
        Get commit history for a specific file.
        """
        if not self.git_available:
            return []

        success, log_output, _ = self._run_git(
            "log", f"--max-count={limit}",
            "--format=%H|%s|%ad",
            "--date=iso",
            "--", file_path
        )

        if not success:
            return []

        history = []
        for line in log_output.split("\n"):
            if "|" in line:
                parts = line.split("|", 2)
                if len(parts) >= 3:
                    history.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "date": parts[2]
                    })

        return history

    def restore_file(self, file_path: str, commit_hash: str) -> Dict:
        """
        Restore a file from a specific commit.
        """
        if not self.git_available:
            return {"success": False, "message": "Git not available"}

        success, _, stderr = self._run_git("checkout", commit_hash, "--", file_path)

        if success:
            return {
                "success": True,
                "message": f"Restored {file_path} from {commit_hash[:8]}"
            }
        else:
            return {
                "success": False,
                "message": f"Could not restore file: {stderr}"
            }
