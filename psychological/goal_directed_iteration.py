"""
Goal-Directed Iteration Loop (GDIL)
Systematic project handling with clarification, iteration, and graceful exits.
Supports multiple concurrent projects with project switching.
Includes project templates for quick-start common project types.
Integrates version control for automatic commit tracking.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from psychological.project_templates import ProjectTemplateLibrary
from utils.version_control import VersionControlManager, CommitType

class ProjectPhase(Enum):
    """Project lifecycle phases."""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    ITERATION = "iteration"
    EXIT = "exit"
    PAUSED = "paused"
    ARCHIVED = "archived"


class GoalDirectedIterationLoop:
    """
    High-level orchestrator for multi-turn project handling.
    Integrates with all psychological modules for systematic progression.
    Supports multiple concurrent projects with context switching.
    """

    def __init__(
        self,
        llm,
        memory,
        emotion_regulator,
        temporal_purpose,
        predictive_dreaming,
        assurance_module,
        meta_reflection,
        reward_calibration,
        iteration_threshold: float = 0.1,  # Min improvement to continue
        max_iterations: int = 10,
        stall_iterations: int = 3,  # Consecutive low-progress iterations before exit
        max_concurrent_projects: int = 5  # Limit active projects
    ):
        self.llm = llm
        self.memory = memory
        self.emotion = emotion_regulator
        self.temporal = temporal_purpose
        self.dreaming = predictive_dreaming
        self.assurance = assurance_module
        self.reflection = meta_reflection
        self.calibration = reward_calibration

        # Configuration
        self.iteration_threshold = iteration_threshold
        self.max_iterations = max_iterations
        self.stall_iterations = stall_iterations
        self.max_concurrent_projects = max_concurrent_projects

        # Multi-project state
        self.projects: Dict[str, Dict] = {}  # All active projects
        self.current_project_id: Optional[str] = None  # Currently focused project
        self.project_history: List[Dict] = []  # Archived/completed projects

        # Template library
        self.templates = ProjectTemplateLibrary(memory)

        # Version Control Integration
        self.vcs = VersionControlManager(
            auto_commit=True,
            commit_on_subtask=True,
            create_branches=True,
            generate_changelog=True
        )
        self.vcs_enabled = True  # Can be toggled via config

        # Load persisted projects on init
        self._load_persisted_projects()

    @property
    def active_project(self) -> Optional[Dict]:
        """Get the currently focused project."""
        if self.current_project_id and self.current_project_id in self.projects:
            return self.projects[self.current_project_id]
        return None

    @active_project.setter
    def active_project(self, project: Optional[Dict]):
        """Set the currently focused project."""
        if project is None:
            self.current_project_id = None
        else:
            project_id = project.get("id")
            if project_id:
                self.projects[project_id] = project
                self.current_project_id = project_id

    def _load_persisted_projects(self):
        """Load any persisted projects from memory."""
        try:
            saved_projects = self.memory.retrieve_persistent("gdil_projects")
            if saved_projects:
                self.projects = saved_projects
                # Set current to most recently updated if any
                if self.projects:
                    most_recent = max(
                        self.projects.values(),
                        key=lambda p: p.get("updated_at", 0)
                    )
                    self.current_project_id = most_recent.get("id")
        except Exception:
            pass

    def _save_all_projects(self):
        """Persist all projects to memory."""
        self.memory.store_persistent("gdil_projects", self.projects)
    
    def start_project(self, user_input: str, project_name: Optional[str] = None) -> str:
        """
        Initialize a new project from user description.
        Phase 1: Clarify scope and goal.
        Supports multiple concurrent projects.
        """
        # Check concurrent project limit
        active_count = len([
            p for p in self.projects.values()
            if p.get("phase") not in [ProjectPhase.EXIT, ProjectPhase.ARCHIVED, "exit", "archived"]
        ])
        if active_count >= self.max_concurrent_projects:
            return (
                f"You have {active_count} active projects (max: {self.max_concurrent_projects}).\n"
                f"Use `/projects` to see them, `/project switch <id>` to switch, "
                f"or `/project archive <id>` to archive one."
            )

        # Generate short name if not provided
        if not project_name:
            project_name = self._generate_project_name(user_input)

        project_id = f"project_{int(time.time())}"

        # Create new project
        new_project = {
            "id": project_id,
            "name": project_name,
            "initial_input": user_input,
            "phase": ProjectPhase.INITIALIZATION,
            "brief": None,
            "end_transformation": None,
            "roadmap": [],
            "current_subtask": None,
            "iterations": [],
            "progress_score": 0.0,
            "blockers": [],
            "created_at": time.time(),
            "updated_at": time.time()
        }

        # Add to projects and set as current
        self.projects[project_id] = new_project
        self.current_project_id = project_id

        # Version Control: Initialize and create project branch
        if self.vcs_enabled:
            self.vcs.initialize_repo()
            self.vcs.create_project_branch(project_id, project_name)
            self.vcs.commit_changes(
                CommitType.PROJECT_START,
                f"Started project: {project_name}",
                project_id=project_id
            )

        # Apply empathetic acknowledgment
        self.emotion.apply_reward_signal(valence=0.5, label="project_start", intensity=0.6)

        # Generate clarification questions using Predictive Dreaming
        clarification = self._generate_clarification_questions(user_input)

        # Store in memory
        self.memory.store_episodic(
            event="project_started",
            content=self.active_project,
            valence=0.5
        )

        return clarification
    
    def _generate_clarification_questions(self, user_input: str) -> str:
        """Use Predictive Dreaming to identify ambiguities."""
        prompt = f"""
You're starting a project with this description:
"{user_input}"

Your task: Generate 3-5 focused clarifying questions to understand:
1. The desired end transformation (what should the final output look like?)
2. Key constraints (time, resources, preferences)
3. Ambiguous aspects that need definition

Be empathetic and excited. Start with "Sounds exciting—let's make this happen!"

Output format:
{{
  "acknowledgment": "...",
  "end_transformation_query": "...",
  "clarifying_questions": ["...", "...", "..."],
  "identified_uncertainties": ["...", "..."]
}}
"""
        
        try:
            response = self.llm.generate(prompt, temperature=0.7, max_tokens=800)
            parsed = self._parse_json_response(response)
            
            # Store uncertainties for Assurance module
            for uncertainty in parsed.get("identified_uncertainties", []):
                self.assurance.trigger_concern(
                    response=user_input,
                    context=user_input,
                    reasoning_trace={},
                    uncertainty_score=0.7,
                    signals={"project_ambiguity": 0.7}
                )
            
            # Format response
            output = f"{parsed['acknowledgment']}\n\n"
            output += f"**End Goal**: {parsed['end_transformation_query']}\n\n"
            output += "**Questions to refine our approach:**\n"
            for i, q in enumerate(parsed['clarifying_questions'], 1):
                output += f"{i}. {q}\n"
            
            return output
            
        except Exception as e:
            # Fallback
            return (
                "Sounds exciting—let's make this happen!\n\n"
                f"To start, I need to understand:\n"
                f"1. What should the final output look like?\n"
                f"2. Any constraints or deadlines?\n"
                f"3. What aspects matter most to you?"
            )
    
    def process_clarification(self, user_response: str) -> str:
        """
        Process user's clarification responses.
        Transition to Planning phase.
        """
        if not self.active_project or self.active_project["phase"] != ProjectPhase.INITIALIZATION:
            return "No active project initialization. Start with /project [description]"
        
        # Store clarification
        self.active_project["clarification_response"] = user_response
        self.active_project["phase"] = ProjectPhase.PLANNING
        self.active_project["updated_at"] = time.time()
        
        # Resolve assurance concerns
        for concern in self.assurance.pending_concerns[:]:
            self.assurance.seek_resolution(concern, user_response)
        
        # Generate project brief and roadmap
        brief_and_roadmap = self._generate_roadmap(
            self.active_project["initial_input"],
            user_response
        )
        
        self.active_project["brief"] = brief_and_roadmap["brief"]
        self.active_project["end_transformation"] = brief_and_roadmap["end_transformation"]
        self.active_project["roadmap"] = brief_and_roadmap["roadmap"]
        
        # Update Temporal Purpose
        self.temporal.incorporate_reflection(
            f"Collaborating on project: {brief_and_roadmap['brief'][:100]}",
            "I am a project partner"
        )
        
        # Persist
        self.memory.store_persistent(f"project_{self.active_project['id']}", self.active_project)
        
        return brief_and_roadmap["presentation"]
    
    def _generate_roadmap(self, initial_input: str, clarification: str) -> Dict:
        """Generate project brief and decomposed roadmap."""
        prompt = f"""
Based on the project description and clarifications, create a structured plan.

Initial Request: {initial_input}
Clarifications: {clarification}

Generate:
1. A concise project brief (2-3 sentences)
2. The end transformation: "From [current state] to [desired state]"
3. A roadmap: 4-8 subtasks with dependencies
4. A confirmation question for the user

Output JSON:
{{
  "brief": "...",
  "end_transformation": "From ... to ...",
  "roadmap": [
    {{"name": "...", "description": "...", "priority": 1-3, "depends_on": []}},
    ...
  ],
  "confirmation_question": "..."
}}
"""
        
        try:
            response = self.llm.generate(prompt, temperature=0.6, max_tokens=1200)
            parsed = self._parse_json_response(response)
            
            # Format presentation
            presentation = f"**Project Brief:**\n{parsed['brief']}\n\n"
            presentation += f"**End Transformation:**\n{parsed['end_transformation']}\n\n"
            presentation += "**Roadmap:**\n"
            for i, task in enumerate(parsed['roadmap'], 1):
                presentation += f"{i}. **{task['name']}** (Priority: {task['priority']})\n"
                presentation += f"   {task['description']}\n"
            presentation += f"\n{parsed['confirmation_question']}"
            
            parsed["presentation"] = presentation
            return parsed
            
        except Exception as e:
            # Fallback
            return {
                "brief": f"Work on: {initial_input[:100]}",
                "end_transformation": "From concept to implementation",
                "roadmap": [{"name": "Define requirements", "description": "...", "priority": 1, "depends_on": []}],
                "presentation": "I've outlined a basic plan. Should we proceed?"
            }
    
    def start_iteration(self, user_confirmation: str) -> str:
        """
        Begin iteration phase.
        Execute first subtask.
        """
        if not self.active_project or self.active_project["phase"] != ProjectPhase.PLANNING:
            return "Project not in planning phase"
        
        # Check confirmation
        if "no" in user_confirmation.lower() or "wait" in user_confirmation.lower():
            return "Understood. What adjustments should we make to the roadmap?"
        
        self.active_project["phase"] = ProjectPhase.ITERATION
        self.active_project["iteration_count"] = 0
        self.active_project["low_progress_count"] = 0
        
        # Select first subtask
        next_task = self._select_next_subtask()
        return self._execute_subtask(next_task)
    
    def _select_next_subtask(self) -> Dict:
        """
        Select next subtask based on priority and dependencies.
        Uses Reward Calibration for optimal challenge.
        """
        roadmap = self.active_project["roadmap"]
        completed = [task["name"] for task in self.active_project.get("completed_tasks", [])]
        
        # Find highest priority incomplete task with satisfied dependencies
        for task in sorted(roadmap, key=lambda t: t["priority"], reverse=True):
            if task["name"] not in completed:
                deps_met = all(dep in completed for dep in task.get("depends_on", []))
                if deps_met:
                    return task
        
        # Fallback: first incomplete
        for task in roadmap:
            if task["name"] not in completed:
                return task
        
        return None
    
    def _execute_subtask(self, task: Dict) -> str:
        """
        Execute a subtask, asking questions as needed.
        Phase 3: Iteration cycle.
        """
        if task is None:
            return self._initiate_exit("All subtasks completed!")
        
        self.active_project["current_subtask"] = task
        self.active_project["iteration_count"] += 1
        
        # Check max iterations
        if self.active_project["iteration_count"] > self.max_iterations:
            return self._initiate_exit("Maximum iterations reached")
        
        # Generate execution with questions
        prompt = f"""
You're working on this subtask of a project:

Project Brief: {self.active_project['brief']}
Current Subtask: {task['name']} - {task['description']}
End Transformation: {self.active_project['end_transformation']}

Execute this subtask. If you need clarification, ask focused questions.
Provide concrete output (code, plan, analysis, etc.) with explanation.

Output JSON:
{{
  "output": "...",  // Main deliverable
  "explanation": "...",  // What you did
  "questions": ["...", "..."],  // Empty if none needed
  "progress_estimate": 0.0-1.0,  // How much of subtask is complete
  "blockers": ["..."]  // Empty if none
}}
"""
        
        try:
            response = self.llm.generate(prompt, temperature=0.7, max_tokens=2000)
            parsed = self._parse_json_response(response)
            
            # Store iteration
            iteration = {
                "task": task["name"],
                "output": parsed["output"],
                "questions": parsed["questions"],
                "progress": parsed["progress_estimate"],
                "timestamp": time.time()
            }
            self.active_project["iterations"].append(iteration)
            
            # Update progress
            old_score = self.active_project["progress_score"]
            self.active_project["progress_score"] = self._calculate_overall_progress()
            improvement = self.active_project["progress_score"] - old_score
            
            # Check for diminishing returns
            if improvement < self.iteration_threshold:
                self.active_project["low_progress_count"] += 1
            else:
                self.active_project["low_progress_count"] = 0
            
            # Emotional response based on progress
            if improvement > 0.15:
                self.emotion.apply_reward_signal(valence=0.7, label="good_progress", intensity=0.6)
            elif improvement < 0.05:
                self.emotion.apply_reward_signal(valence=-0.3, label="slow_progress", intensity=0.4)
            
            # Format output
            output = f"**{task['name']}** - Progress: {parsed['progress_estimate']*100:.0f}%\n\n"
            output += f"{parsed['output']}\n\n"
            output += f"*{parsed['explanation']}*\n\n"
            
            if parsed["questions"]:
                output += "**Questions:**\n"
                for i, q in enumerate(parsed["questions"], 1):
                    output += f"{i}. {q}\n"
                output += "\n"
            
            if parsed["blockers"]:
                self.active_project["blockers"].extend(parsed["blockers"])
                output += "**Blockers identified:**\n"
                for b in parsed["blockers"]:
                    output += f"- {b}\n"
                output += "\n"
            
            # Check for exit condition
            if self.active_project["low_progress_count"] >= self.stall_iterations:
                output += "\n" + self._initiate_exit("Progress has stalled")
            elif parsed["progress_estimate"] >= 1.0:
                # Mark complete and move to next
                if "completed_tasks" not in self.active_project:
                    self.active_project["completed_tasks"] = []
                self.active_project["completed_tasks"].append(task)

                # Version Control: Commit on subtask completion
                if self.vcs_enabled:
                    self.vcs.commit_changes(
                        CommitType.SUBTASK_COMPLETE,
                        f"Completed: {task['name']}",
                        project_id=self.active_project["id"],
                        subtask_name=task["name"]
                    )

                next_task = self._select_next_subtask()
                if next_task:
                    output += f"\n✓ Subtask complete! Moving to: **{next_task['name']}**\n"
                    output += "Ready to continue?"
                else:
                    output += "\n" + self._initiate_exit("All subtasks completed!")
            else:
                output += f"\nOverall project progress: {self.active_project['progress_score']*100:.0f}%\n"
                output += "Should I continue or adjust course?"
            
            # Persist
            self.memory.store_persistent(f"project_{self.active_project['id']}", self.active_project)
            
            return output
            
        except Exception as e:
            return f"Error executing subtask: {e}\nWhat should we do?"
    
    def continue_iteration(self, user_feedback: str) -> str:
        """
        Process user feedback and continue iteration.
        """
        if not self.active_project or self.active_project["phase"] != ProjectPhase.ITERATION:
            return "No active iteration"
        
        # Check if user wants to stop
        stop_signals = ["stop", "pause", "enough", "done"]
        if any(signal in user_feedback.lower() for signal in stop_signals):
            return self._initiate_exit("User requested pause")
        
        # Process feedback and continue
        current_task = self.active_project.get("current_subtask")
        if current_task:
            return self._execute_subtask(current_task)
        else:
            next_task = self._select_next_subtask()
            return self._execute_subtask(next_task)
    
    def _calculate_overall_progress(self) -> float:
        """Calculate overall project progress."""
        total_tasks = len(self.active_project["roadmap"])
        if total_tasks == 0:
            return 0.0
        
        completed = len(self.active_project.get("completed_tasks", []))
        
        # Weight current task progress
        current_progress = 0.0
        if self.active_project.get("iterations"):
            last_iter = self.active_project["iterations"][-1]
            current_progress = last_iter.get("progress", 0.0) / total_tasks
        
        return (completed / total_tasks) + current_progress
    
    def _initiate_exit(self, reason: str) -> str:
        """
        Phase 4: Exit phase - summarize and hand off.
        """
        self.active_project["phase"] = ProjectPhase.EXIT
        self.active_project["exit_reason"] = reason
        
        # Generate comprehensive summary
        completed_count = len(self.active_project.get("completed_tasks", []))
        total_count = len(self.active_project["roadmap"])
        progress_pct = self.active_project["progress_score"] * 100
        
        summary = f"**Project Summary**\n\n"
        summary += f"**Status:** {reason}\n\n"
        summary += f"**Completion:** {progress_pct:.0f}% ({completed_count}/{total_count} subtasks)\n\n"
        
        summary += f"**What we accomplished:**\n"
        for task in self.active_project.get("completed_tasks", []):
            summary += f"✓ {task['name']}\n"
        
        if self.active_project["blockers"]:
            summary += f"\n**Blockers:**\n"
            for blocker in set(self.active_project["blockers"]):
                summary += f"- {blocker}\n"
            
            remaining = total_count - completed_count
            impact_pct = (remaining / total_count * 100) if total_count > 0 else 0
            summary += f"\n*These affect the remaining {impact_pct:.0f}% of the project.*\n"
        
        summary += f"\n**Next Steps:**\n"
        summary += "- Provide missing information to continue\n"
        summary += "- Use `/resume project` to pick up where we left off\n"
        summary += "- Or start a new approach\n"
        
        # Apply relief through Assurance
        self.emotion.apply_reward_signal(valence=0.5, label="project_exit_clarity", intensity=0.5)

        # Version Control: Final commit and optional merge
        if self.vcs_enabled:
            self.vcs.commit_changes(
                CommitType.EXIT,
                f"Project exit: {reason} ({progress_pct:.0f}% complete)",
                project_id=self.active_project["id"]
            )
            # Generate changelog for the project
            changelog = self.vcs.generate_changelog(self.active_project["id"])
            if changelog:
                self.active_project["changelog"] = changelog

        # Store final state
        self.memory.store_persistent(f"project_{self.active_project['id']}_final", self.active_project)
        self.project_history.append(self.active_project)

        return summary
    
    def resume_project(self, project_id: Optional[str] = None) -> str:
        """Resume a paused or exited project."""
        if project_id:
            project = self.memory.retrieve_persistent(f"project_{project_id}")
        else:
            # Resume most recent
            project = self.project_history[-1] if self.project_history else None
        
        if not project:
            return "No project to resume. Start a new one with /project [description]"
        
        self.active_project = project
        self.active_project["phase"] = ProjectPhase.ITERATION
        self.active_project["low_progress_count"] = 0
        
        summary = f"**Resuming Project**\n\n"
        summary += f"Brief: {project['brief']}\n"
        summary += f"Progress: {project['progress_score']*100:.0f}%\n\n"
        summary += "Continuing from where we left off...\n"
        
        return summary
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response with fallback."""
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        
        # Fallback
        return {
            "acknowledgment": "Let's work on this together.",
            "end_transformation_query": "What should the final output look like?",
            "clarifying_questions": ["What are the key requirements?"],
            "identified_uncertainties": []
        }
    
    def get_project_status(self) -> Optional[Dict]:
        """Get current project status for dashboard."""
        if not self.active_project:
            return None

        phase = self.active_project["phase"]
        phase_value = phase.value if isinstance(phase, ProjectPhase) else str(phase)

        return {
            "id": self.active_project["id"],
            "name": self.active_project.get("name", "Unnamed"),
            "phase": phase_value,
            "brief": self.active_project.get("brief", "In progress"),
            "progress": self.active_project["progress_score"],
            "iterations": len(self.active_project.get("iterations", [])),
            "completed_tasks": len(self.active_project.get("completed_tasks", [])),
            "total_tasks": len(self.active_project.get("roadmap", [])),
            "current_subtask": self.active_project.get("current_subtask", {}).get("name", "None"),
            "total_projects": len(self.projects)
        }

    # ============================================
    # Multi-Project Management
    # ============================================

    def _generate_project_name(self, user_input: str) -> str:
        """Generate a short project name from user input."""
        # Take first few meaningful words
        words = user_input.split()[:5]
        name = " ".join(words)
        if len(name) > 40:
            name = name[:37] + "..."
        return name

    def list_projects(self) -> str:
        """List all active and paused projects."""
        if not self.projects:
            return "No active projects. Start one with `/project [description]`"

        output = "**Your Projects:**\n\n"

        # Sort by updated_at descending
        sorted_projects = sorted(
            self.projects.values(),
            key=lambda p: p.get("updated_at", 0),
            reverse=True
        )

        for project in sorted_projects:
            project_id = project["id"]
            name = project.get("name", "Unnamed")
            phase = project.get("phase")
            phase_str = phase.value if isinstance(phase, ProjectPhase) else str(phase)
            progress = project.get("progress_score", 0) * 100

            # Current indicator
            current = " ← current" if project_id == self.current_project_id else ""

            # Phase emoji
            phase_emoji = {
                "initialization": "🔄",
                "planning": "📋",
                "iteration": "⚡",
                "paused": "⏸️",
                "exit": "✓",
                "archived": "📦"
            }.get(phase_str, "•")

            output += f"{phase_emoji} **{name}**{current}\n"
            output += f"   ID: `{project_id}` | Phase: {phase_str} | Progress: {progress:.0f}%\n\n"

        output += "\n**Commands:**\n"
        output += "• `/project switch <id>` - Switch to a project\n"
        output += "• `/project pause` - Pause current project\n"
        output += "• `/project archive <id>` - Archive a project\n"

        return output

    def switch_project(self, project_id: str) -> str:
        """Switch to a different project."""
        # Handle short IDs (allow matching by suffix)
        matching = [
            pid for pid in self.projects.keys()
            if pid == project_id or pid.endswith(project_id)
        ]

        if not matching:
            return f"Project `{project_id}` not found. Use `/projects` to see all projects."

        if len(matching) > 1:
            return f"Ambiguous ID. Matches: {', '.join(matching)}"

        target_id = matching[0]
        target = self.projects[target_id]

        # Pause current if different
        if self.current_project_id and self.current_project_id != target_id:
            current = self.projects.get(self.current_project_id)
            if current:
                current["phase"] = ProjectPhase.PAUSED
                current["updated_at"] = time.time()

        # Switch
        self.current_project_id = target_id
        target["updated_at"] = time.time()

        # Save state
        self._save_all_projects()

        name = target.get("name", "Unnamed")
        phase = target.get("phase")
        phase_str = phase.value if isinstance(phase, ProjectPhase) else str(phase)
        progress = target.get("progress_score", 0) * 100

        output = f"**Switched to:** {name}\n\n"
        output += f"Phase: {phase_str} | Progress: {progress:.0f}%\n"

        if target.get("brief"):
            output += f"\nBrief: {target['brief']}\n"

        if target.get("current_subtask"):
            output += f"\nCurrent task: {target['current_subtask'].get('name', 'None')}\n"

        output += "\nReady to continue?"
        return output

    def pause_project(self, project_id: Optional[str] = None) -> str:
        """Pause a project (defaults to current)."""
        target_id = project_id or self.current_project_id

        if not target_id or target_id not in self.projects:
            return "No project to pause."

        target = self.projects[target_id]
        target["phase"] = ProjectPhase.PAUSED
        target["updated_at"] = time.time()

        # If pausing current, clear current
        if target_id == self.current_project_id:
            self.current_project_id = None

        self._save_all_projects()

        name = target.get("name", "Unnamed")
        return f"Project **{name}** paused. Use `/project switch {target_id}` to resume."

    def archive_project(self, project_id: str) -> str:
        """Archive a project (remove from active list)."""
        # Handle short IDs
        matching = [
            pid for pid in self.projects.keys()
            if pid == project_id or pid.endswith(project_id)
        ]

        if not matching:
            return f"Project `{project_id}` not found."

        target_id = matching[0]
        target = self.projects[target_id]

        # Archive
        target["phase"] = ProjectPhase.ARCHIVED
        target["archived_at"] = time.time()

        # Move to history
        self.project_history.append(target)
        del self.projects[target_id]

        # If archived current, clear current
        if target_id == self.current_project_id:
            self.current_project_id = None
            # Auto-switch to next most recent if any
            if self.projects:
                most_recent = max(
                    self.projects.values(),
                    key=lambda p: p.get("updated_at", 0)
                )
                self.current_project_id = most_recent.get("id")

        self._save_all_projects()

        name = target.get("name", "Unnamed")
        return f"Project **{name}** archived."

    def get_all_projects_status(self) -> List[Dict]:
        """Get status of all projects for dashboard."""
        statuses = []
        for project in self.projects.values():
            phase = project.get("phase")
            phase_str = phase.value if isinstance(phase, ProjectPhase) else str(phase)

            statuses.append({
                "id": project["id"],
                "name": project.get("name", "Unnamed"),
                "phase": phase_str,
                "progress": project.get("progress_score", 0),
                "is_current": project["id"] == self.current_project_id,
                "updated_at": project.get("updated_at", 0)
            })

        return sorted(statuses, key=lambda p: p["updated_at"], reverse=True)

    # ============================================
    # Project Templates
    # ============================================

    def list_templates(self, category: Optional[str] = None) -> str:
        """List available project templates."""
        return self.templates.list_templates(category)

    def get_template_details(self, template_id: str) -> str:
        """Get detailed information about a template."""
        return self.templates.get_template_details(template_id)

    def start_project_from_template(
        self,
        template_id: str,
        customization: str = ""
    ) -> str:
        """
        Start a new project from a template.
        Skips some clarification since template provides structure.
        """
        # Check concurrent project limit
        active_count = len([
            p for p in self.projects.values()
            if p.get("phase") not in [ProjectPhase.EXIT, ProjectPhase.ARCHIVED, "exit", "archived"]
        ])
        if active_count >= self.max_concurrent_projects:
            return (
                f"You have {active_count} active projects (max: {self.max_concurrent_projects}).\n"
                f"Use `/projects` to see them, `/project switch <id>` to switch, "
                f"or `/project archive <id>` to archive one."
            )

        # Get template configuration
        template_config = self.templates.create_project_from_template(template_id, customization)
        if not template_config:
            return f"Template `{template_id}` not found. Use `/templates` to see available templates."

        project_id = f"project_{int(time.time())}"
        project_name = template_config["template_name"]
        if customization:
            project_name = f"{project_name}: {customization[:30]}"

        # Create new project with template data
        new_project = {
            "id": project_id,
            "name": project_name,
            "initial_input": template_config["initial_input"],
            "phase": ProjectPhase.INITIALIZATION,
            "brief": template_config["suggested_brief"],
            "end_transformation": template_config["end_transformation"],
            "roadmap": template_config["roadmap"],
            "current_subtask": None,
            "iterations": [],
            "progress_score": 0.0,
            "blockers": [],
            "created_at": time.time(),
            "updated_at": time.time(),
            "template_id": template_config["template_id"],
            "template_questions": template_config["clarifying_questions"]
        }

        # Add to projects and set as current
        self.projects[project_id] = new_project
        self.current_project_id = project_id

        # Apply empathetic acknowledgment
        self.emotion.apply_reward_signal(valence=0.5, label="template_project_start", intensity=0.6)

        # Store in memory
        self.memory.store_episodic(
            event="template_project_started",
            content={"project_id": project_id, "template": template_id},
            valence=0.5
        )

        # Format response with template questions
        output = f"**Starting from template: {template_config['template_name']}**\n\n"
        output += f"*{template_config['suggested_brief']}*\n\n"
        output += f"**End Goal:** {template_config['end_transformation']}\n\n"

        output += "**Pre-defined Roadmap:**\n"
        for i, task in enumerate(template_config["roadmap"][:5], 1):
            output += f"  {i}. {task['name']}\n"
        if len(template_config["roadmap"]) > 5:
            output += f"  ... and {len(template_config['roadmap']) - 5} more tasks\n"

        output += "\n**Quick Questions to Customize:**\n"
        for i, q in enumerate(template_config["clarifying_questions"][:3], 1):
            output += f"  {i}. {q}\n"

        output += "\nAnswer these or say 'skip' to use defaults and start immediately."
        return output

    def process_template_clarification(self, user_response: str) -> str:
        """
        Process clarification for template-based project.
        If user says 'skip', jump directly to iteration.
        """
        if not self.active_project or self.active_project.get("template_id") is None:
            return self.process_clarification(user_response)

        # Check for skip
        if user_response.lower().strip() in ["skip", "start", "go", "begin", "defaults"]:
            # Jump to iteration phase with template defaults
            self.active_project["phase"] = ProjectPhase.ITERATION
            self.active_project["iteration_count"] = 0
            self.active_project["low_progress_count"] = 0
            self.active_project["updated_at"] = time.time()

            # Update Temporal Purpose
            self.temporal.incorporate_reflection(
                f"Starting template project: {self.active_project.get('name', '')}",
                "I am a project partner"
            )

            # Select first subtask
            next_task = self._select_next_subtask()
            return self._execute_subtask(next_task)

        # Process as normal clarification
        return self.process_clarification(user_response)

    # ============================================
    # Version Control Integration
    # ============================================

    def vcs_status(self) -> str:
        """Get version control status for current project."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        status = self.vcs.get_status()

        if not status.get("git_available"):
            return "Git is not available on this system."

        if not status.get("initialized"):
            return "No git repository initialized. Start a project to initialize."

        output = "**Version Control Status**\n\n"
        output += f"**Branch:** {status.get('branch', 'unknown')}\n"
        output += f"**Commits:** {status.get('commit_count', 0)}\n"

        if status.get("has_changes"):
            output += "\n**Pending Changes:**\n"
            if status.get("staged_files"):
                output += f"  Staged: {len(status['staged_files'])} files\n"
            if status.get("modified_files"):
                output += f"  Modified: {len(status['modified_files'])} files\n"
            if status.get("untracked_files"):
                output += f"  Untracked: {len(status['untracked_files'])} files\n"
        else:
            output += "\n✓ Working directory clean\n"

        if status.get("current_project_branch"):
            output += f"\n**Project Branch:** {status['current_project_branch']}\n"

        return output

    def vcs_history(self, limit: int = 10) -> str:
        """Get commit history for current project."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        project_id = self.current_project_id
        history = self.vcs.get_project_history(project_id, limit)

        if not history:
            return "No commits found for this project."

        output = "**Commit History**\n\n"

        for commit in history:
            hash_short = commit.get("hash", "")[:8]
            message = commit.get("message", "")
            date = commit.get("date", "")[:10]
            metadata = commit.get("metadata", {})

            # Icon based on commit type
            commit_type = metadata.get("commit_type", "")
            icon = {
                "project": "🚀",
                "feat": "✅",
                "wip": "⚙️",
                "milestone": "🏆",
                "pause": "⏸️",
                "resume": "▶️",
                "exit": "🏁",
                "revert": "↩️",
                "fix": "🔧"
            }.get(commit_type, "•")

            output += f"{icon} `{hash_short}` {message}\n"
            output += f"   {date}\n\n"

        return output

    def vcs_rollback(self, target: str) -> str:
        """
        Rollback to a previous state.
        Target can be a commit hash or subtask name.
        """
        if not self.vcs_enabled:
            return "Version control is disabled."

        # Check if target is a subtask name
        if not target.startswith(("project_", "feat(", "wip(")):
            # Try to find by subtask name
            result = self.vcs.rollback_subtask(
                self.current_project_id or "",
                target
            )
        else:
            # Assume it's a commit hash
            result = self.vcs.rollback_to_commit(target, soft=True)

        if result.get("success"):
            output = f"✓ **Rollback successful**\n\n"
            output += f"{result.get('message', '')}\n"
            if result.get("backup_branch"):
                output += f"\nBackup created: `{result['backup_branch']}`\n"
            return output
        else:
            return f"❌ Rollback failed: {result.get('message', 'Unknown error')}"

    def vcs_diff(self, file_path: Optional[str] = None) -> str:
        """Show current changes or diff for a file."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        result = self.vcs.get_diff(file_path=file_path)

        if not result.get("success"):
            return f"Could not get diff: {result.get('message', '')}"

        if not result.get("has_changes"):
            return "No changes detected."

        diff = result.get("diff", "")
        if len(diff) > 2000:
            diff = diff[:2000] + "\n... (truncated)"

        return f"**Changes:**\n\n```diff\n{diff}\n```"

    def vcs_commit(self, message: str) -> str:
        """Manually create a commit."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        result = self.vcs.commit_changes(
            CommitType.ITERATION,
            message,
            project_id=self.current_project_id
        )

        if result.get("success"):
            if result.get("skipped"):
                return "No changes to commit."
            return f"✓ Committed: {result.get('message', message)}\n  Hash: `{result.get('hash', '')[:8]}`"
        else:
            return f"❌ Commit failed: {result.get('message', 'Unknown error')}"

    def vcs_changelog(self) -> str:
        """Generate changelog for current project."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        changelog = self.vcs.generate_changelog(self.current_project_id)
        return changelog if changelog else "No changelog available."

    def vcs_stash(self, pop: bool = False) -> str:
        """Stash or pop stashed changes."""
        if not self.vcs_enabled:
            return "Version control is disabled."

        if pop:
            result = self.vcs.pop_stash()
        else:
            result = self.vcs.stash_changes(
                f"Stash from project {self.current_project_id or 'unknown'}"
            )

        if result.get("success"):
            action = "Popped" if pop else "Stashed"
            return f"✓ {action} changes successfully."
        else:
            return f"❌ Stash operation failed: {result.get('message', '')}"

    def toggle_vcs(self, enabled: bool) -> str:
        """Enable or disable version control integration."""
        self.vcs_enabled = enabled
        status = "enabled" if enabled else "disabled"
        return f"Version control integration {status}."
