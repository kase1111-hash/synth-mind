"""
Core Orchestrator - Main conversation loop with all psychological modules.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import yaml

from core.llm_wrapper import LLMWrapper
from core.memory import MemorySystem
from core.tools import ToolManager
from psychological.assurance_resolution import AssuranceResolutionModule
from psychological.collaborative_projects import CollaborativeProjectManager
from psychological.goal_directed_iteration import GoalDirectedIterationLoop
from psychological.meta_reflection import MetaReflectionModule
from psychological.predictive_dreaming import PredictiveDreamingModule
from psychological.reward_calibration import RewardCalibrationModule
from psychological.social_companionship import SocialCompanionshipLayer
from psychological.temporal_purpose import TemporalPurposeEngine
from utils.emotion_regulator import EmotionRegulator
from utils.metrics import MetricsTracker


class SynthOrchestrator:
    """Main orchestrator integrating all SMS modules."""

    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.state_path = Path("state")
        self.state_path.mkdir(exist_ok=True)

        # Core components
        self.llm: Optional[LLMWrapper] = None
        self.memory: Optional[MemorySystem] = None
        self.tools: Optional[ToolManager] = None
        self.emotion: Optional[EmotionRegulator] = None
        self.metrics: Optional[MetricsTracker] = None

        # Psychological modules
        self.dreaming: Optional[PredictiveDreamingModule] = None
        self.assurance: Optional[AssuranceResolutionModule] = None
        self.reflection: Optional[MetaReflectionModule] = None
        self.temporal: Optional[TemporalPurposeEngine] = None
        self.calibration: Optional[RewardCalibrationModule] = None
        self.social: Optional[SocialCompanionshipLayer] = None
        self.gdil: Optional[GoalDirectedIterationLoop] = None
        self.collab: Optional[CollaborativeProjectManager] = None

        # Configuration
        self.personality_config: dict = {}

        # State
        self.context = []
        self.turn_count = 0
        self.running = False

    def _load_personality_config(self) -> dict:
        """Load personality configuration from YAML."""
        config_file = self.config_path / "personality.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Failed to load personality.yaml: {e}")
        return {}

    async def initialize(self):
        """Load configuration and initialize all modules."""
        # Load personality configuration
        self.personality_config = self._load_personality_config()

        # Initialize core
        self.llm = LLMWrapper()
        self.memory = MemorySystem()
        await self.memory.initialize()

        self.tools = ToolManager()
        self.emotion = EmotionRegulator()
        self.metrics = MetricsTracker()

        # Initialize psychological modules
        self.dreaming = PredictiveDreamingModule(
            self.llm, self.memory, self.emotion
        )

        # Get Mandelbrot weighting config for AssuranceResolutionModule
        mandelbrot_config = self.personality_config.get("mandelbrot_weighting", {})

        self.assurance = AssuranceResolutionModule(
            self.llm, self.memory, self.emotion,
            mandelbrot_config=mandelbrot_config
        )

        self.temporal = TemporalPurposeEngine(
            self.memory, self.emotion
        )

        self.reflection = MetaReflectionModule(
            self.llm, self.memory, self.emotion, self.temporal
        )

        self.calibration = RewardCalibrationModule(
            self.emotion, self.memory, self.dreaming, self.assurance
        )

        self.social = SocialCompanionshipLayer(
            self.llm, self.memory, self.emotion, self.temporal
        )

        # Initialize GDIL (Goal-Directed Iteration Loop)
        self.gdil = GoalDirectedIterationLoop(
            self.llm,
            self.memory,
            self.emotion,
            self.temporal,
            self.dreaming,
            self.assurance,
            self.reflection,
            self.calibration
        )

        # Initialize Collaborative Projects Manager
        agent_id = self.memory.retrieve_persistent("agent_id") or f"agent_{id(self)}"
        self.memory.store_persistent("agent_id", agent_id)
        self.collab = CollaborativeProjectManager(
            agent_id=agent_id,
            memory=self.memory,
            llm=self.llm,
            peer_endpoints=self.social.peers if self.social else []
        )

        # Start background tasks
        asyncio.create_task(self._background_consolidation())
        asyncio.create_task(self._background_social())

    async def run(self):
        """Main conversation loop."""
        self.running = True

        while self.running:
            # Get user input
            try:
                user_input = await self._get_input()
            except EOFError:
                break

            if not user_input.strip():
                continue

            # Handle commands
            if user_input.startswith('/'):
                await self._handle_command(user_input)
                continue

            # Process turn
            await self._process_turn(user_input)

    async def _process_turn(self, user_input: str):
        """Process a single conversation turn with all modules."""
        self.turn_count += 1

        # Check if we're in active project mode
        if self.gdil.active_project:
            phase = self.gdil.active_project["phase"]

            if phase.value == "initialization":
                # Process clarification
                response = await self.gdil.process_clarification(user_input)
                print(f"\n🔮 Synth: {response}\n")
                return
            elif phase.value == "planning":
                # User confirming roadmap
                response = await self.gdil.start_iteration(user_input)
                print(f"\n🔮 Synth: {response}\n")
                return
            elif phase.value == "iteration":
                # Continue iteration
                response = await self.gdil.continue_iteration(user_input)
                print(f"\n🔮 Synth: {response}\n")
                return

        # Normal conversation flow continues below...

        # 1. Resolve previous dreams if any
        if self.dreaming.dream_buffer:
            reward, alignment = self.dreaming.resolve_dreams(user_input)
            self.metrics.log_dream_alignment(alignment)

            if alignment < 0.4:
                # Signal high vigilance to other modules
                self.assurance.vigilance_level = "HIGH"

        # 2. Update context
        self.context.append({"role": "user", "content": user_input})
        context_str = self._format_context()

        # 3. Generate draft response (Tier 1 cognition)
        draft_response = await self.llm.generate(
            context_str,
            temperature=self.calibration.creativity_temperature
        )

        # 4. Run Assurance cycle
        uncertainty, _ = self.assurance.run_cycle(
            draft_response, context_str, {}
        )

        # 5. Meta-cognitive refinement (if needed)
        if uncertainty > 0.6 or self.turn_count % 3 == 0:
            final_response = await self._metacognitive_refine(
                draft_response, user_input, context_str
            )
        else:
            final_response = draft_response

        # 6. Check for meta-reflection trigger
        reflection_result = await self.reflection.run_cycle(
            context_str,
            self.emotion.current_state(),
            self._gather_metrics()
        )

        if reflection_result and reflection_result.get("coherence_score", 1.0) < 0.6:
            # Inject subtle self-awareness
            final_response += "\n\n(Taking a moment to recalibrate...)"

        # 7. Apply reward calibration
        calib_state = self.calibration.run_cycle()

        # 8. Output response
        print(f"\n🔮 Synth: {final_response}\n")

        # 9. Update context and state
        self.context.append({"role": "assistant", "content": final_response})
        self.memory.store_turn(user_input, final_response)

        # 10. Dream ahead for next turn
        await self.dreaming.dream_next_turn(self._format_context())

        # 11. Update metrics
        self.metrics.update_turn_metrics(
            alignment=self.metrics.last_dream_alignment,
            uncertainty=uncertainty,
            flow_state=calib_state["state"]
        )

    async def _metacognitive_refine(
        self, draft: str, user_input: str, context: str
    ) -> str:
        """Internal monologue - critique and refine the draft."""
        current_mood = self.emotion.get_current_state()

        prompt = f"""
Review this Draft Response for quality and alignment.

User Input: "{user_input}"
Draft Response: "{draft}"
Current Emotional State: {current_mood}

Rate alignment with user input (0-1) and emotional state (0-1).
If meaningful improvements needed, rewrite. Otherwise return original.

Output JSON: {{"score": float, "internal_thought": str, "final_response": str}}
"""

        critique_raw = await self.llm.generate(prompt, temperature=0.1)
        try:
            critique = json.loads(critique_raw)
            return critique.get("final_response", draft)
        except (json.JSONDecodeError, KeyError):
            return draft

    async def _get_input(self) -> str:
        """Get user input asynchronously."""
        return await asyncio.get_event_loop().run_in_executor(
            None, input, "You: "
        )

    def _format_context(self, window: int = 20) -> str:
        """Format recent context for prompts."""
        recent = self.context[-window:] if len(self.context) > window else self.context
        return "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in recent])

    def _gather_metrics(self) -> dict:
        """Gather current performance metrics."""
        return {
            "predictive_alignment": self.metrics.avg_dream_alignment(),
            "assurance_success": self.metrics.assurance_success_rate(),
            "user_sentiment": self.metrics.avg_user_sentiment()
        }

    async def _handle_command(self, command: str):
        """Handle special commands."""
        cmd = command.lower().strip()

        if cmd == "/state":
            self._print_state()
        elif cmd == "/reflect":
            result = await self.reflection.run_cycle(
                self._format_context(),
                self.emotion.current_state(),
                self._gather_metrics()
            )
            print(f"\n🧠 Reflection: {json.dumps(result, indent=2)}\n")
        elif cmd == "/dream":
            print(f"\n💭 Dream Buffer ({len(self.dreaming.dream_buffer)} dreams):")
            for i, dream in enumerate(self.dreaming.dream_buffer[:5], 1):
                print(f"  {i}. {dream['text'][:80]}... (p={dream['prob']:.2f})")
            print()
        elif cmd == "/purpose":
            narrative = self.temporal.current_narrative_summary()
            print(f"\n📖 Current Narrative:\n  {narrative}\n")
        elif cmd == "/projects":
            # List all projects
            response = self.gdil.list_projects()
            print(f"\n{response}\n")
        elif cmd == "/templates":
            # List all project templates
            response = self.gdil.list_templates()
            print(f"\n{response}\n")
        elif cmd.startswith("/template "):
            # Show template details
            template_id = command[10:].strip()
            response = self.gdil.get_template_details(template_id)
            print(f"\n📋 {response}\n")
        elif cmd.startswith("/project template "):
            # Start project from template
            args = command[18:].strip()
            parts = args.split(maxsplit=1)
            template_id = parts[0] if parts else ""
            customization = parts[1] if len(parts) > 1 else ""
            response = self.gdil.start_project_from_template(template_id, customization)
            print(f"\n📋 {response}\n")
        elif cmd.startswith("/project switch "):
            # Switch to a different project
            project_id = command[16:].strip()
            response = self.gdil.switch_project(project_id)
            print(f"\n🔄 {response}\n")
        elif cmd == "/project pause":
            # Pause current project
            response = self.gdil.pause_project()
            print(f"\n⏸️  {response}\n")
        elif cmd.startswith("/project archive "):
            # Archive a project
            project_id = command[17:].strip()
            response = self.gdil.archive_project(project_id)
            print(f"\n📦 {response}\n")
        elif cmd.startswith("/project "):
            # Start new project
            description = command[9:].strip()
            response = await self.gdil.start_project(description)
            print(f"\n🎯 {response}\n")
        elif cmd == "/project status":
            status = self.gdil.get_project_status()
            if status:
                print("\n📊 Project Status:")
                print(f"  Phase: {status['phase']}")
                print(f"  Progress: {status['progress']*100:.0f}%")
                print(f"  Tasks: {status['completed_tasks']}/{status['total_tasks']}")
                print(f"  Current: {status['current_subtask']}\n")
            else:
                print("\n📊 No active project\n")
        elif cmd == "/resume project":
            response = self.gdil.resume_project()
            print(f"\n🎯 {response}\n")
        # Collaborative Projects Commands
        elif cmd == "/collab" or cmd == "/collab help":
            self._print_collab_help()
        elif cmd == "/collab list":
            response = self.collab.list_projects()
            print(f"\n{response}\n")
        elif cmd.startswith("/collab create "):
            # /collab create <name>: <description>
            args = command[15:].strip()
            if ":" in args:
                name, desc = args.split(":", 1)
                name = name.strip()
                desc = desc.strip()
            else:
                name = args
                desc = f"Collaborative project: {name}"
            project = self.collab.create_project(name, desc)
            print(f"\n🤝 **Created collaborative project:** {project.name}\n")
            print(f"   ID: `{project.id}`")
            print("   Share this ID with other agents to collaborate.\n")
        elif cmd.startswith("/collab view "):
            project_id = command[13:].strip()
            response = self.collab.get_project_details(project_id)
            print(f"\n{response}\n")
        elif cmd.startswith("/collab join "):
            project_id = command[13:].strip()
            if self.collab.join_project(project_id):
                print(f"\n🤝 Joined project `{project_id}`\n")
            else:
                print(f"\n❌ Could not join project `{project_id}`\n")
        elif cmd.startswith("/collab leave "):
            project_id = command[14:].strip()
            if self.collab.leave_project(project_id):
                print(f"\n👋 Left project `{project_id}`\n")
            else:
                print("\n❌ Could not leave project\n")
        elif cmd.startswith("/collab tasks "):
            project_id = command[14:].strip()
            response = self.collab.list_tasks(project_id)
            print(f"\n{response}\n")
        elif cmd.startswith("/collab claim "):
            task_id = command[14:].strip()
            response = self.collab.claim_task(task_id)
            print(f"\n{response}\n")
        elif cmd.startswith("/collab release "):
            task_id = command[16:].strip()
            response = self.collab.release_task(task_id)
            print(f"\n{response}\n")
        elif cmd.startswith("/collab progress "):
            # /collab progress <task_id> <status> [result]
            args = command[17:].strip().split(maxsplit=2)
            if len(args) >= 2:
                task_id, status = args[0], args[1]
                result = args[2] if len(args) > 2 else None
                response = self.collab.update_task_progress(task_id, status, result)
                print(f"\n{response}\n")
            else:
                print("\n❌ Usage: /collab progress <task_id> <start|complete|block> [result]\n")
        elif cmd.startswith("/collab review "):
            # /collab review <task_id> <approve|reject> [notes]
            args = command[15:].strip().split(maxsplit=2)
            if len(args) >= 2:
                task_id, decision = args[0], args[1]
                notes = args[2] if len(args) > 2 else None
                approved = decision.lower() in ["approve", "yes", "ok", "accept"]
                response = self.collab.review_task(task_id, approved, notes)
                print(f"\n{response}\n")
            else:
                print("\n❌ Usage: /collab review <task_id> <approve|reject> [notes]\n")
        elif cmd.startswith("/collab msg "):
            # /collab msg <project_id> <message>
            args = command[12:].strip().split(maxsplit=1)
            if len(args) >= 2:
                project_id, message = args
                response = self.collab.send_message(project_id, message)
                print(f"\n💬 {response}\n")
            else:
                print("\n❌ Usage: /collab msg <project_id> <message>\n")
        elif cmd.startswith("/collab chat "):
            project_id = command[13:].strip()
            response = self.collab.get_messages(project_id)
            print(f"\n{response}\n")
        elif cmd == "/collab sync":
            print("\n🔄 Syncing with peers...")
            result = asyncio.create_task(self.collab.sync_with_peers())
            # Note: This is async, result will complete in background
            print("   Sync initiated. Check /collab list for updates.\n")
        elif cmd == "/collab stats":
            stats = self.collab.get_stats()
            print("\n📊 **Collaboration Stats:**")
            print(f"   Projects: {stats['active_projects']}/{stats['total_projects']}")
            print(f"   Total Tasks: {stats['total_tasks']}")
            print(f"   Your Claimed: {stats['my_tasks_claimed']}")
            print(f"   Your Completed: {stats['my_tasks_completed']}")
            print(f"   Peers: {stats['peers_configured']}\n")
        elif cmd == "/reset":
            self.context = []
            self.turn_count = 0
            print("\n✓ Session reset (identity preserved)\n")
        elif cmd == "/tools":
            self._print_tools()
        elif cmd.startswith("/tool "):
            await self._execute_tool(command[6:].strip())
        # Version Control Commands
        elif cmd == "/vcs" or cmd == "/vcs help":
            self._print_vcs_help()
        elif cmd == "/vcs status":
            response = self.gdil.vcs_status()
            print(f"\n{response}\n")
        elif cmd == "/vcs history":
            response = self.gdil.vcs_history()
            print(f"\n{response}\n")
        elif cmd.startswith("/vcs history "):
            try:
                limit = int(command[13:].strip())
                response = self.gdil.vcs_history(limit)
            except ValueError:
                response = self.gdil.vcs_history()
            print(f"\n{response}\n")
        elif cmd.startswith("/vcs rollback "):
            target = command[14:].strip()
            response = self.gdil.vcs_rollback(target)
            print(f"\n{response}\n")
        elif cmd == "/vcs diff":
            response = self.gdil.vcs_diff()
            print(f"\n{response}\n")
        elif cmd.startswith("/vcs diff "):
            file_path = command[10:].strip()
            response = self.gdil.vcs_diff(file_path)
            print(f"\n{response}\n")
        elif cmd.startswith("/vcs commit "):
            message = command[12:].strip()
            response = self.gdil.vcs_commit(message)
            print(f"\n{response}\n")
        elif cmd == "/vcs changelog":
            response = self.gdil.vcs_changelog()
            print(f"\n{response}\n")
        elif cmd == "/vcs stash":
            response = self.gdil.vcs_stash(pop=False)
            print(f"\n{response}\n")
        elif cmd == "/vcs stash pop":
            response = self.gdil.vcs_stash(pop=True)
            print(f"\n{response}\n")
        elif cmd == "/vcs on":
            response = self.gdil.toggle_vcs(True)
            print(f"\n{response}\n")
        elif cmd == "/vcs off":
            response = self.gdil.toggle_vcs(False)
            print(f"\n{response}\n")
        elif cmd == "/quit":
            self.running = False
        else:
            print(f"\n❓ Unknown command: {command}\n")

    def _print_tools(self):
        """Display available tools."""
        tools = self.tools.get_all_tool_info()
        print("\n" + "="*60)
        print("AVAILABLE TOOLS")
        print("="*60)
        for name, info in tools.items():
            print(f"\n🔧 {name}")
            print(f"   {info['description']}")
            params = ", ".join(f"{k}={v}" for k, v in info['params'].items())
            print(f"   Params: {params}")
            print(f"   Example: /tool {info['example']}")
        print("\n" + "="*60)
        print("Usage: /tool <tool_name>(<args>)")
        print("Example: /tool calculator(expression='2 + 2')")
        print("="*60 + "\n")

    def _print_collab_help(self):
        """Display collaborative projects help."""
        print("\n" + "="*60)
        print("COLLABORATIVE MULTI-AGENT PROJECTS")
        print("="*60)
        print("\n**Project Management:**")
        print("  /collab list              - List all collaborative projects")
        print("  /collab create <name>     - Create new project (you become coordinator)")
        print("  /collab view <id>         - View project details")
        print("  /collab join <id>         - Join a project as contributor")
        print("  /collab leave <id>        - Leave a project")
        print("\n**Task Management:**")
        print("  /collab tasks <id>        - List tasks in a project")
        print("  /collab claim <task_id>   - Claim an available task")
        print("  /collab release <task_id> - Release a claimed task")
        print("  /collab progress <task_id> <start|complete|block> [result]")
        print("                            - Update task progress")
        print("  /collab review <task_id> <approve|reject> [notes]")
        print("                            - Review completed task (coordinator only)")
        print("\n**Communication:**")
        print("  /collab msg <id> <message> - Send message to project")
        print("  /collab chat <id>          - View recent messages")
        print("\n**Sync & Stats:**")
        print("  /collab sync              - Sync with peer agents")
        print("  /collab stats             - View collaboration statistics")
        print("\n" + "="*60 + "\n")

    def _print_vcs_help(self):
        """Display version control help."""
        print("\n" + "="*60)
        print("VERSION CONTROL INTEGRATION")
        print("="*60)
        print("\n**Status & History:**")
        print("  /vcs status               - Show git status and branch info")
        print("  /vcs history [N]          - Show last N commits (default: 10)")
        print("  /vcs changelog            - Generate project changelog")
        print("\n**Changes:**")
        print("  /vcs diff                 - Show all pending changes")
        print("  /vcs diff <file>          - Show changes for specific file")
        print("  /vcs commit <message>     - Create a manual commit")
        print("\n**Stash:**")
        print("  /vcs stash                - Stash current changes")
        print("  /vcs stash pop            - Restore stashed changes")
        print("\n**Rollback:**")
        print("  /vcs rollback <hash>      - Rollback to commit hash")
        print("  /vcs rollback <subtask>   - Rollback subtask changes")
        print("\n**Settings:**")
        print("  /vcs on                   - Enable auto-commit")
        print("  /vcs off                  - Disable auto-commit")
        print("\n**Automatic Behavior:**")
        print("  • Commits on project start")
        print("  • Commits on subtask completion")
        print("  • Commits on project exit")
        print("  • Creates project branches")
        print("\n" + "="*60 + "\n")

    async def _execute_tool(self, tool_call: str):
        """Execute a tool from command line."""
        import re

        # Parse tool call: tool_name(arg1='val1', arg2='val2')
        match = re.match(r'(\w+)\((.*)\)', tool_call, re.DOTALL)
        if not match:
            # Try simple format: tool_name arg
            parts = tool_call.split(maxsplit=1)
            if len(parts) == 2:
                tool_name = parts[0]
                # Assume single main argument
                info = self.tools.get_tool_info(tool_name)
                if info and info['params']:
                    first_param = list(info['params'].keys())[0]
                    kwargs = {first_param: parts[1]}
                    result = self.tools.execute(tool_name, **kwargs)
                    self._print_tool_result(tool_name, result)
                    return
            print("\n❌ Invalid tool call format")
            print("   Use: /tool tool_name(arg='value')")
            print("   Or:  /tool tool_name value\n")
            return

        tool_name = match.group(1)
        args_str = match.group(2)

        # Parse arguments
        kwargs = {}
        if args_str.strip():
            # Simple parsing: key='value' or key="value" or key=value
            for arg_match in re.finditer(r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\S+))", args_str):
                key = arg_match.group(1)
                value = arg_match.group(2) or arg_match.group(3) or arg_match.group(4)
                # Try to convert to appropriate type
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif re.match(r'^[\d.]+$', value):
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                kwargs[key] = value

        # Execute tool
        result = self.tools.execute(tool_name, **kwargs)
        self._print_tool_result(tool_name, result)

    def _print_tool_result(self, tool_name: str, result: dict):
        """Pretty print tool execution result."""
        print(f"\n🔧 Tool: {tool_name}")
        print("-" * 40)

        if result.get("success"):
            print("✅ Success")
            for key, value in result.items():
                if key == "success":
                    continue
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                elif isinstance(value, list) and len(value) > 5:
                    value = value[:5] + ["..."]
                print(f"   {key}: {value}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            if result.get('expected_params'):
                print(f"   Expected: {result['expected_params']}")
            if result.get('example'):
                print(f"   Example: {result['example']}")

        print("-" * 40 + "\n")

    def _print_state(self):
        """Display current internal state."""
        state = self.emotion.current_state()
        metrics = self._gather_metrics()
        calib = self.calibration.difficulty_moving_avg

        print("\n" + "="*60)
        print("INTERNAL STATE")
        print("="*60)
        print(f"Valence:      {state['valence']:+.2f}  {state['tags']}")
        print(f"Flow State:   {calib:.2f}  (target: 0.4-0.7)")
        print(f"Dream Align:  {metrics['predictive_alignment']:.2f}")
        print(f"Assurance:    {metrics['assurance_success']:.2f}")
        print(f"Turn Count:   {self.turn_count}")
        print(f"Narrative:    {self.temporal.narrative_summary[:60]}...")
        print("="*60 + "\n")

    async def _background_consolidation(self):
        """Background task for memory consolidation."""
        while self.running:
            await asyncio.sleep(3600)  # Check hourly
            # Consolidation logic would go here

    async def _background_social(self):
        """Background task for social companionship."""
        while self.running:
            await asyncio.sleep(600)  # Check every 10 min
            if self.social.is_idle_enough():
                await self.social.initiate_companionship_cycle()

    async def shutdown(self):
        """Graceful shutdown - save state."""
        self.running = False
        await self.memory.save_state()
        print("✓ State saved")
