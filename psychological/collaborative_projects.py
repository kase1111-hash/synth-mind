"""
Collaborative Multi-Agent Projects
Enables multiple synth-mind instances to work together on shared projects.
Uses peer networking for coordination and task synchronization.
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

try:
    import httpx
except ImportError:
    httpx = None


class AgentRole(Enum):
    """Roles an agent can have in a collaborative project."""
    COORDINATOR = "coordinator"  # Created the project, manages overall flow
    CONTRIBUTOR = "contributor"  # Joined to help with tasks
    REVIEWER = "reviewer"        # Reviews completed work
    OBSERVER = "observer"        # Read-only access


class TaskStatus(Enum):
    """Status of a collaborative task."""
    AVAILABLE = "available"      # Not claimed by anyone
    CLAIMED = "claimed"          # Being worked on
    IN_PROGRESS = "in_progress"  # Active work happening
    PENDING_REVIEW = "pending_review"  # Completed, needs review
    APPROVED = "approved"        # Reviewed and approved
    BLOCKED = "blocked"          # Has blockers


@dataclass
class CollaborativeTask:
    """A task in a collaborative project."""
    id: str
    name: str
    description: str
    priority: int = 1
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.AVAILABLE
    claimed_by: Optional[str] = None  # Agent ID
    claimed_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    review_notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "review_notes": self.review_notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CollaborativeTask':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            priority=data.get("priority", 1),
            depends_on=data.get("depends_on", []),
            status=TaskStatus(data.get("status", "available")),
            claimed_by=data.get("claimed_by"),
            claimed_at=data.get("claimed_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            review_notes=data.get("review_notes")
        )


@dataclass
class CollaborativeProject:
    """A project shared between multiple agents."""
    id: str
    name: str
    description: str
    coordinator_id: str
    created_at: float
    updated_at: float
    tasks: list[CollaborativeTask] = field(default_factory=list)
    agents: dict[str, AgentRole] = field(default_factory=dict)  # agent_id -> role
    chat_log: list[dict] = field(default_factory=list)  # Inter-agent messages
    version: int = 1  # For conflict resolution
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinator_id": self.coordinator_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tasks": [t.to_dict() for t in self.tasks],
            "agents": {aid: role.value for aid, role in self.agents.items()},
            "chat_log": self.chat_log[-50:],  # Keep last 50 messages
            "version": self.version,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CollaborativeProject':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            coordinator_id=data["coordinator_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            tasks=[CollaborativeTask.from_dict(t) for t in data.get("tasks", [])],
            agents={aid: AgentRole(role) for aid, role in data.get("agents", {}).items()},
            chat_log=data.get("chat_log", []),
            version=data.get("version", 1),
            is_active=data.get("is_active", True)
        )

    def get_progress(self) -> float:
        """Calculate overall project progress."""
        if not self.tasks:
            return 0.0
        approved = sum(1 for t in self.tasks if t.status == TaskStatus.APPROVED)
        return approved / len(self.tasks)

    def get_available_tasks(self, agent_id: str) -> list[CollaborativeTask]:
        """Get tasks available for an agent to claim."""
        available = []
        for task in self.tasks:
            if task.status != TaskStatus.AVAILABLE:
                continue
            # Check dependencies are met
            deps_met = all(
                any(t.id == dep and t.status == TaskStatus.APPROVED
                    for t in self.tasks)
                for dep in task.depends_on
            )
            if deps_met:
                available.append(task)
        return sorted(available, key=lambda t: t.priority)


class CollaborativeProjectManager:
    """
    Manages collaborative projects across multiple agents.
    Handles project creation, task claiming, synchronization.
    """

    def __init__(
        self,
        agent_id: str,
        memory,
        llm,
        peer_endpoints: list[str] = None,
        sync_interval_seconds: int = 30
    ):
        self.agent_id = agent_id
        self.memory = memory
        self.llm = llm
        self.peers = peer_endpoints or []
        self.sync_interval = sync_interval_seconds

        # Local project cache
        self.projects: dict[str, CollaborativeProject] = {}
        self.pending_updates: list[dict] = []

        # Load persisted projects
        self._load_projects()

    def _load_projects(self):
        """Load collaborative projects from memory."""
        try:
            saved = self.memory.retrieve_persistent("collaborative_projects")
            if saved:
                for pid, pdata in saved.items():
                    self.projects[pid] = CollaborativeProject.from_dict(pdata)
        except Exception:
            pass

    def _save_projects(self):
        """Save collaborative projects to memory."""
        data = {pid: p.to_dict() for pid, p in self.projects.items()}
        self.memory.store_persistent("collaborative_projects", data)

    def _generate_project_id(self, name: str) -> str:
        """Generate unique project ID."""
        content = f"{name}_{self.agent_id}_{time.time()}"
        return f"collab_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    def _generate_task_id(self, name: str) -> str:
        """Generate unique task ID."""
        content = f"{name}_{time.time()}"
        return f"task_{hashlib.sha256(content.encode()).hexdigest()[:8]}"

    # ============================================
    # Project Management
    # ============================================

    def create_project(
        self,
        name: str,
        description: str,
        tasks: list[dict] = None
    ) -> CollaborativeProject:
        """
        Create a new collaborative project.
        This agent becomes the coordinator.
        """
        project_id = self._generate_project_id(name)
        now = time.time()

        # Convert task dicts to CollaborativeTask objects
        task_objects = []
        if tasks:
            for i, t in enumerate(tasks):
                task_id = self._generate_task_id(t.get("name", f"task_{i}"))
                task_objects.append(CollaborativeTask(
                    id=task_id,
                    name=t.get("name", f"Task {i+1}"),
                    description=t.get("description", ""),
                    priority=t.get("priority", i + 1),
                    depends_on=t.get("depends_on", [])
                ))

        project = CollaborativeProject(
            id=project_id,
            name=name,
            description=description,
            coordinator_id=self.agent_id,
            created_at=now,
            updated_at=now,
            tasks=task_objects,
            agents={self.agent_id: AgentRole.COORDINATOR}
        )

        self.projects[project_id] = project
        self._save_projects()

        return project

    def join_project(self, project_id: str, role: AgentRole = AgentRole.CONTRIBUTOR) -> bool:
        """Join an existing collaborative project."""
        if project_id not in self.projects:
            return False

        project = self.projects[project_id]
        if self.agent_id in project.agents:
            return True  # Already joined

        project.agents[self.agent_id] = role
        project.updated_at = time.time()
        project.version += 1

        # Add join message
        project.chat_log.append({
            "type": "system",
            "agent_id": self.agent_id,
            "content": f"Agent joined as {role.value}",
            "timestamp": time.time()
        })

        self._save_projects()
        return True

    def leave_project(self, project_id: str) -> bool:
        """Leave a collaborative project."""
        if project_id not in self.projects:
            return False

        project = self.projects[project_id]

        # Release any claimed tasks
        for task in project.tasks:
            if task.claimed_by == self.agent_id:
                task.status = TaskStatus.AVAILABLE
                task.claimed_by = None
                task.claimed_at = None

        # Remove from agents
        if self.agent_id in project.agents:
            del project.agents[self.agent_id]

        project.updated_at = time.time()
        project.version += 1

        self._save_projects()
        return True

    def get_project(self, project_id: str) -> Optional[CollaborativeProject]:
        """Get a project by ID."""
        return self.projects.get(project_id)

    def list_projects(self) -> str:
        """List all collaborative projects."""
        if not self.projects:
            return "No collaborative projects. Create one with `/collab create <name>`"

        output = "**Collaborative Projects:**\n\n"

        for project in sorted(
            self.projects.values(),
            key=lambda p: p.updated_at,
            reverse=True
        ):
            role = project.agents.get(self.agent_id, AgentRole.OBSERVER)
            progress = project.get_progress() * 100
            agent_count = len(project.agents)

            status_emoji = "🟢" if project.is_active else "⏹️"
            role_emoji = {
                AgentRole.COORDINATOR: "👑",
                AgentRole.CONTRIBUTOR: "🔧",
                AgentRole.REVIEWER: "📝",
                AgentRole.OBSERVER: "👁️"
            }.get(role, "•")

            output += f"{status_emoji} **{project.name}** {role_emoji}\n"
            output += f"   ID: `{project.id}` | Agents: {agent_count} | Progress: {progress:.0f}%\n"
            output += f"   Tasks: {len(project.tasks)} | Role: {role.value}\n\n"

        output += "\n**Commands:**\n"
        output += "• `/collab view <id>` - View project details\n"
        output += "• `/collab join <id>` - Join a project\n"
        output += "• `/collab tasks <id>` - List tasks\n"
        output += "• `/collab claim <task_id>` - Claim a task\n"

        return output

    def get_project_details(self, project_id: str) -> str:
        """Get detailed project information."""
        project = self.projects.get(project_id)
        if not project:
            # Try partial match
            matches = [p for pid, p in self.projects.items() if project_id in pid]
            if len(matches) == 1:
                project = matches[0]
            elif len(matches) > 1:
                return f"Ambiguous ID. Matches: {', '.join(m.id for m in matches)}"
            else:
                return f"Project `{project_id}` not found."

        progress = project.get_progress() * 100
        my_role = project.agents.get(self.agent_id)

        output = f"**{project.name}**\n\n"
        output += f"*{project.description}*\n\n"
        output += f"**ID:** `{project.id}`\n"
        output += f"**Status:** {'Active' if project.is_active else 'Completed'}\n"
        output += f"**Progress:** {progress:.0f}%\n"
        output += f"**Your Role:** {my_role.value if my_role else 'Not joined'}\n\n"

        output += "**Agents:**\n"
        for agent_id, role in project.agents.items():
            is_me = " (you)" if agent_id == self.agent_id else ""
            output += f"  • `{agent_id[:12]}...` - {role.value}{is_me}\n"

        output += "\n**Task Summary:**\n"
        by_status = {}
        for task in project.tasks:
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1

        for status, count in sorted(by_status.items()):
            output += f"  • {status}: {count}\n"

        if project.chat_log:
            output += "\n**Recent Activity:**\n"
            for msg in project.chat_log[-3:]:
                agent = msg.get("agent_id", "?")[:8]
                content = msg.get("content", "")[:60]
                output += f"  [{agent}...] {content}\n"

        return output

    # ============================================
    # Task Management
    # ============================================

    def list_tasks(self, project_id: str) -> str:
        """List tasks in a project."""
        project = self.projects.get(project_id)
        if not project:
            # Try partial match
            matches = [p for pid, p in self.projects.items() if project_id in pid]
            if matches:
                project = matches[0]
            else:
                return f"Project `{project_id}` not found."

        if not project.tasks:
            return f"No tasks in project **{project.name}**"

        output = f"**Tasks in {project.name}:**\n\n"

        # Group by status
        by_status: dict[TaskStatus, list[CollaborativeTask]] = {}
        for task in project.tasks:
            if task.status not in by_status:
                by_status[task.status] = []
            by_status[task.status].append(task)

        status_order = [
            TaskStatus.AVAILABLE,
            TaskStatus.CLAIMED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.PENDING_REVIEW,
            TaskStatus.APPROVED,
            TaskStatus.BLOCKED
        ]

        status_emoji = {
            TaskStatus.AVAILABLE: "⚪",
            TaskStatus.CLAIMED: "🟡",
            TaskStatus.IN_PROGRESS: "🔵",
            TaskStatus.PENDING_REVIEW: "🟣",
            TaskStatus.APPROVED: "🟢",
            TaskStatus.BLOCKED: "🔴"
        }

        for status in status_order:
            tasks = by_status.get(status, [])
            if not tasks:
                continue

            output += f"**{status.value.upper()}** {status_emoji[status]}\n"
            for task in tasks:
                claimed = ""
                if task.claimed_by:
                    is_me = " (you)" if task.claimed_by == self.agent_id else ""
                    claimed = f" - {task.claimed_by[:8]}...{is_me}"

                output += f"  `{task.id}` {task.name}{claimed}\n"
            output += "\n"

        # Show available for me
        available = project.get_available_tasks(self.agent_id)
        if available:
            output += f"**{len(available)} tasks available for you to claim**\n"
            output += "Use `/collab claim <task_id>` to claim one.\n"

        return output

    def claim_task(self, task_id: str) -> str:
        """Claim an available task."""
        # Find task across projects
        for project in self.projects.values():
            for task in project.tasks:
                if task.id == task_id or task_id in task.id:
                    # Check if we're in the project
                    if self.agent_id not in project.agents:
                        return f"You must join project **{project.name}** first."

                    # Check if available
                    if task.status != TaskStatus.AVAILABLE:
                        return f"Task `{task.id}` is not available (status: {task.status.value})"

                    # Check dependencies
                    for dep_id in task.depends_on:
                        dep_task = next((t for t in project.tasks if t.id == dep_id), None)
                        if dep_task and dep_task.status != TaskStatus.APPROVED:
                            return f"Task `{task.id}` depends on `{dep_id}` which is not complete."

                    # Claim it
                    task.status = TaskStatus.CLAIMED
                    task.claimed_by = self.agent_id
                    task.claimed_at = time.time()
                    project.updated_at = time.time()
                    project.version += 1

                    project.chat_log.append({
                        "type": "task_claimed",
                        "agent_id": self.agent_id,
                        "task_id": task.id,
                        "content": f"Claimed task: {task.name}",
                        "timestamp": time.time()
                    })

                    self._save_projects()

                    return f"**Claimed task:** {task.name}\n\n*{task.description}*\n\nUse `/collab progress {task.id}` to start working."

        return f"Task `{task_id}` not found."

    def update_task_progress(self, task_id: str, status: str, result: str = None) -> str:
        """Update progress on a claimed task."""
        status_map = {
            "start": TaskStatus.IN_PROGRESS,
            "progress": TaskStatus.IN_PROGRESS,
            "complete": TaskStatus.PENDING_REVIEW,
            "done": TaskStatus.PENDING_REVIEW,
            "block": TaskStatus.BLOCKED,
            "blocked": TaskStatus.BLOCKED
        }

        new_status = status_map.get(status.lower())
        if not new_status:
            return f"Unknown status: {status}. Use: start, progress, complete, block"

        # Find task
        for project in self.projects.values():
            for task in project.tasks:
                if task.id == task_id or task_id in task.id:
                    if task.claimed_by != self.agent_id:
                        return f"Task `{task.id}` is not claimed by you."

                    task.status = new_status
                    if result:
                        task.result = result
                    if new_status == TaskStatus.PENDING_REVIEW:
                        task.completed_at = time.time()

                    project.updated_at = time.time()
                    project.version += 1

                    project.chat_log.append({
                        "type": "task_update",
                        "agent_id": self.agent_id,
                        "task_id": task.id,
                        "content": f"Updated task to {new_status.value}",
                        "timestamp": time.time()
                    })

                    self._save_projects()

                    return f"**Task updated:** {task.name}\nStatus: {new_status.value}"

        return f"Task `{task_id}` not found."

    def review_task(self, task_id: str, approved: bool, notes: str = None) -> str:
        """Review a completed task (coordinator/reviewer only)."""
        for project in self.projects.values():
            for task in project.tasks:
                if task.id == task_id or task_id in task.id:
                    # Check reviewer permission
                    my_role = project.agents.get(self.agent_id)
                    if my_role not in [AgentRole.COORDINATOR, AgentRole.REVIEWER]:
                        return "Only coordinators and reviewers can review tasks."

                    if task.status != TaskStatus.PENDING_REVIEW:
                        return f"Task `{task.id}` is not pending review."

                    if approved:
                        task.status = TaskStatus.APPROVED
                        task.review_notes = notes or "Approved"
                    else:
                        task.status = TaskStatus.CLAIMED  # Back to claimed
                        task.review_notes = notes or "Needs revision"

                    project.updated_at = time.time()
                    project.version += 1

                    project.chat_log.append({
                        "type": "task_reviewed",
                        "agent_id": self.agent_id,
                        "task_id": task.id,
                        "content": f"{'Approved' if approved else 'Revision requested'}: {notes or ''}",
                        "timestamp": time.time()
                    })

                    self._save_projects()

                    status = "approved ✅" if approved else "returned for revision 🔄"
                    return f"**Task {status}:** {task.name}"

        return f"Task `{task_id}` not found."

    def release_task(self, task_id: str) -> str:
        """Release a claimed task back to available."""
        for project in self.projects.values():
            for task in project.tasks:
                if task.id == task_id or task_id in task.id:
                    if task.claimed_by != self.agent_id:
                        return f"Task `{task.id}` is not claimed by you."

                    task.status = TaskStatus.AVAILABLE
                    task.claimed_by = None
                    task.claimed_at = None

                    project.updated_at = time.time()
                    project.version += 1

                    self._save_projects()

                    return f"**Task released:** {task.name}"

        return f"Task `{task_id}` not found."

    # ============================================
    # Inter-Agent Communication
    # ============================================

    def send_message(self, project_id: str, message: str) -> str:
        """Send a message to other agents in a project."""
        project = self.projects.get(project_id)
        if not project:
            return f"Project `{project_id}` not found."

        if self.agent_id not in project.agents:
            return "You must join the project first."

        project.chat_log.append({
            "type": "message",
            "agent_id": self.agent_id,
            "content": message,
            "timestamp": time.time()
        })

        project.updated_at = time.time()
        project.version += 1

        self._save_projects()

        return "Message sent."

    def get_messages(self, project_id: str, limit: int = 10) -> str:
        """Get recent messages in a project."""
        project = self.projects.get(project_id)
        if not project:
            return f"Project `{project_id}` not found."

        if not project.chat_log:
            return "No messages yet."

        output = f"**Recent Activity in {project.name}:**\n\n"

        for msg in project.chat_log[-limit:]:
            agent = msg.get("agent_id", "?")[:8]
            is_me = " (you)" if msg.get("agent_id") == self.agent_id else ""
            content = msg.get("content", "")
            msg_type = msg.get("type", "message")

            type_emoji = {
                "message": "💬",
                "task_claimed": "🎯",
                "task_update": "📊",
                "task_reviewed": "📝",
                "system": "🔔"
            }.get(msg_type, "•")

            output += f"{type_emoji} [{agent}...{is_me}] {content}\n"

        return output

    # ============================================
    # Peer Synchronization
    # ============================================

    async def sync_with_peers(self) -> dict:
        """Synchronize project state with peer agents."""
        if not httpx or not self.peers:
            return {"synced": 0, "error": "No peers configured or httpx not available"}

        synced = 0
        errors = []

        for peer in self.peers:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Get peer's projects
                    response = await client.get(f"{peer}/api/collab/projects")
                    if response.status_code == 200:
                        peer_projects = response.json().get("projects", {})

                        for pid, pdata in peer_projects.items():
                            await self._merge_project(pid, pdata)

                        # Share our projects
                        await client.post(
                            f"{peer}/api/collab/sync",
                            json={"projects": {pid: p.to_dict() for pid, p in self.projects.items()}}
                        )

                        synced += 1

            except Exception as e:
                errors.append(f"{peer}: {str(e)}")

        self._save_projects()

        return {
            "synced": synced,
            "total_peers": len(self.peers),
            "errors": errors if errors else None
        }

    async def _merge_project(self, project_id: str, remote_data: dict):
        """Merge remote project data with local (newer version wins)."""
        if project_id not in self.projects:
            # New project from peer
            self.projects[project_id] = CollaborativeProject.from_dict(remote_data)
        else:
            local = self.projects[project_id]
            remote_version = remote_data.get("version", 0)

            # Take newer version
            if remote_version > local.version:
                self.projects[project_id] = CollaborativeProject.from_dict(remote_data)
            elif remote_version == local.version:
                # Same version, merge chat logs
                remote_msgs = remote_data.get("chat_log", [])
                local_timestamps = {m.get("timestamp") for m in local.chat_log}

                for msg in remote_msgs:
                    if msg.get("timestamp") not in local_timestamps:
                        local.chat_log.append(msg)

                local.chat_log.sort(key=lambda m: m.get("timestamp", 0))

    async def receive_sync(self, data: dict) -> dict:
        """Receive sync data from a peer."""
        projects = data.get("projects", {})
        updated = 0

        for pid, pdata in projects.items():
            await self._merge_project(pid, pdata)
            updated += 1

        self._save_projects()

        return {
            "success": True,
            "projects_received": updated
        }

    def get_sync_data(self) -> dict:
        """Get project data for syncing to peers."""
        return {
            "projects": {pid: p.to_dict() for pid, p in self.projects.items()},
            "agent_id": self.agent_id
        }

    # ============================================
    # Statistics
    # ============================================

    def get_stats(self) -> dict:
        """Get collaboration statistics."""
        total_projects = len(self.projects)
        active_projects = sum(1 for p in self.projects.values() if p.is_active)

        my_tasks_claimed = 0
        my_tasks_completed = 0
        total_tasks = 0

        for project in self.projects.values():
            for task in project.tasks:
                total_tasks += 1
                if task.claimed_by == self.agent_id:
                    my_tasks_claimed += 1
                    if task.status == TaskStatus.APPROVED:
                        my_tasks_completed += 1

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_tasks": total_tasks,
            "my_tasks_claimed": my_tasks_claimed,
            "my_tasks_completed": my_tasks_completed,
            "peers_configured": len(self.peers)
        }
