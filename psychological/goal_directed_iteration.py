"""
Goal-Directed Iteration Loop (GDIL)
Systematic project handling with clarification, iteration, and graceful exits.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ProjectPhase(Enum):
    """Project lifecycle phases."""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    ITERATION = "iteration"
    EXIT = "exit"
    PAUSED = "paused"

class GoalDirectedIterationLoop:
    """
    High-level orchestrator for multi-turn project handling.
    Integrates with all psychological modules for systematic progression.
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
        stall_iterations: int = 3  # Consecutive low-progress iterations before exit
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
        
        # Active project state
        self.active_project = None
        self.project_history = []
    
    def start_project(self, user_input: str) -> str:
        """
        Initialize a new project from user description.
        Phase 1: Clarify scope and goal.
        """
        # Create new project
        self.active_project = {
            "id": f"project_{int(time.time())}",
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
        
        return {
            "id": self.active_project["id"],
            "phase": self.active_project["phase"].value,
            "brief": self.active_project.get("brief", "In progress"),
            "progress": self.active_project["progress_score"],
            "iterations": len(self.active_project.get("iterations", [])),
            "completed_tasks": len(self.active_project.get("completed_tasks", [])),
            "total_tasks": len(self.active_project.get("roadmap", [])),
            "current_subtask": self.active_project.get("current_subtask", {}).get("name", "None")
        }
