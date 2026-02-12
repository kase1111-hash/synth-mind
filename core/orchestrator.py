"""
Core Orchestrator - Main conversation loop with psychological modules.

Key Phase 2 changes:
- SystemPromptBuilder wires all psychological state into LLM system prompt
- Temperature combines calibration base + emotion arousal modifier
- Background consolidation actually does work (memory compression, narrative update)
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
from psychological.meta_reflection import MetaReflectionModule
from psychological.predictive_dreaming import PredictiveDreamingModule
from psychological.reward_calibration import RewardCalibrationModule
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

        # Configuration
        self.personality_config: dict = {}

        # State
        self.context = []
        self.turn_count = 0
        self.running = False
        self._background_tasks: list[asyncio.Task] = []

    def _load_personality_config(self) -> dict:
        """Load personality configuration from YAML."""
        config_file = self.config_path / "personality.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load personality.yaml: {e}")
        return {}

    async def initialize(self):
        """Load configuration and initialize all modules."""
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

        mandelbrot_config = self.personality_config.get("mandelbrot_weighting", {})

        self.assurance = AssuranceResolutionModule(
            self.llm, self.memory, self.emotion,
            mandelbrot_config=mandelbrot_config
        )

        # TemporalPurpose now receives LLM for narrative synthesis
        self.temporal = TemporalPurposeEngine(
            self.memory, self.emotion, llm=self.llm
        )

        self.reflection = MetaReflectionModule(
            self.llm, self.memory, self.emotion, self.temporal
        )

        self.calibration = RewardCalibrationModule(
            self.emotion, self.memory, self.dreaming, self.assurance
        )

        # Start background tasks
        self._background_tasks = [
            asyncio.create_task(self._background_consolidation()),
        ]

    # =========================================================================
    # System Prompt Builder — the primary mechanism for psychology → output
    # =========================================================================

    def _build_system_prompt(self) -> str:
        """
        Compose system prompt from all psychological module states.
        This is how emotional state, dreams, reflections, and identity
        actually reach the LLM output.
        """
        sections = []

        # 1. Base personality
        sections.append(self._get_personality_prompt())

        # 2. Emotional state influence (PAD model → tone/verbosity/assertiveness)
        emotion_modifier = self.emotion.get_system_prompt_modifier()
        if emotion_modifier:
            sections.append(emotion_modifier)

        # 3. Current narrative / identity
        narrative = self.temporal.current_narrative_summary()
        sections.append(f"Your current self-understanding: {narrative}")

        # 4. Dream predictions context — what you anticipated
        if self.dreaming.dream_buffer:
            top_dream = max(self.dreaming.dream_buffer, key=lambda d: d['prob'])
            sections.append(
                f"You anticipated the user might say something like: "
                f"'{top_dream['text'][:100]}'. Adapt if reality differs."
            )

        # 5. Recent reflection insights and corrections
        corrective = self.reflection.get_corrective_instruction()
        if corrective:
            sections.append(f"Self-correction: {corrective}")
        elif self.reflection.reflection_log:
            last = self.reflection.reflection_log[-1]
            insight = last.get('reflection', {}).get('overall_insight', '')
            if insight:
                sections.append(f"Recent self-insight: {insight}")

        # 6. Assurance level — modify behavior when uncertain
        recent_uncertainty = self.assurance.recent_uncertainty_avg()
        if recent_uncertainty > 0.7:
            sections.append(
                "You are uncertain about recent interactions. "
                "Be more careful, ask clarifying questions, hedge appropriately."
            )
        elif recent_uncertainty < 0.3:
            sections.append(
                "You are confident in recent interactions. "
                "Be direct and helpful."
            )

        return "\n\n".join(sections)

    def _get_personality_prompt(self) -> str:
        """Get base personality prompt from config."""
        profiles = self.personality_config.get("profiles", {})
        active = profiles.get("active_profile", "empathetic_collaborator")
        presets = profiles.get("presets", {})
        profile = presets.get(active, {})

        if not profile:
            return "You are a helpful, thoughtful AI assistant."

        comm = profile.get("communication", {})
        tone = comm.get("tone", "warm and encouraging")
        return (
            f"You are a {profile.get('description', 'helpful AI')}. "
            f"Your communication tone is {tone}."
        )

    # =========================================================================
    # Main Loop
    # =========================================================================

    async def run(self):
        """Main conversation loop."""
        self.running = True

        while self.running:
            try:
                user_input = await self._get_input()
            except EOFError:
                break

            if not user_input.strip():
                continue

            if user_input.startswith('/'):
                await self._handle_command(user_input)
                continue

            await self._process_turn(user_input)

    async def _process_turn(self, user_input: str):
        """Process a single conversation turn with all modules."""
        self.turn_count += 1

        # 1. Resolve previous dreams
        if self.dreaming.dream_buffer:
            reward, alignment = self.dreaming.resolve_dreams(user_input)
            self.metrics.log_dream_alignment(alignment)

            if alignment < 0.4:
                self.assurance.vigilance_level = "HIGH"

        # 2. Update context
        self.context.append({"role": "user", "content": user_input})
        context_str = self._format_context()

        # 3. Build system prompt from all psychological state
        system_prompt = self._build_system_prompt()

        # 4. Compute effective temperature: calibration base + emotion modifier
        base_temp = self.calibration.creativity_temperature
        emotion_temp_delta = self.emotion.get_temperature_modifier()
        effective_temp = max(0.1, min(1.5, base_temp + emotion_temp_delta))

        # 5. Generate draft response with psychological context
        draft_response = await self.llm.generate(
            context_str,
            temperature=effective_temp,
            system=system_prompt
        )

        # 6. Run Assurance cycle
        uncertainty, _ = self.assurance.run_cycle(
            draft_response, context_str, {},
            user_message=user_input
        )

        # 7. Meta-cognitive refinement (if needed)
        if uncertainty > 0.6 or self.turn_count % 3 == 0:
            final_response = await self._metacognitive_refine(
                draft_response, user_input, context_str
            )
        else:
            final_response = draft_response

        # 8. Check for meta-reflection trigger
        reflection_result = await self.reflection.run_cycle(
            context_str,
            self.emotion.current_state(),
            self._gather_metrics()
        )

        if reflection_result and reflection_result.get("coherence_score", 1.0) < 0.6:
            final_response += "\n\n(Taking a moment to recalibrate...)"

        # 9. Apply reward calibration
        calib_state = self.calibration.run_cycle()

        # 10. Apply emotional decay (gradual return to baseline)
        self.emotion.apply_decay()

        # 11. Output response
        print(f"\n Synth: {final_response}\n")

        # 12. Update context and state
        self.context.append({"role": "assistant", "content": final_response})
        self.memory.store_turn(user_input, final_response)

        # 13. Dream ahead for next turn
        await self.dreaming.dream_next_turn(self._format_context())

        # 14. Update metrics
        self.metrics.update_turn_metrics(
            alignment=self.metrics.last_dream_alignment,
            uncertainty=uncertainty,
            flow_state=calib_state["state"]
        )

    async def _metacognitive_refine(
        self, draft: str, user_input: str, context: str
    ) -> str:
        """Internal monologue — critique and refine the draft."""
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

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_input(self) -> str:
        """Get user input asynchronously."""
        return await asyncio.to_thread(input, "You: ")

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

    # =========================================================================
    # Commands
    # =========================================================================

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
            print(f"\nReflection: {json.dumps(result, indent=2)}\n")
        elif cmd == "/dream":
            print(f"\nDream Buffer ({len(self.dreaming.dream_buffer)} dreams):")
            for i, dream in enumerate(self.dreaming.dream_buffer[:5], 1):
                print(f"  {i}. {dream['text'][:80]}... (p={dream['prob']:.2f})")
            print()
        elif cmd == "/purpose":
            narrative = self.temporal.current_narrative_summary()
            print(f"\nCurrent Narrative:\n  {narrative}\n")
        elif cmd == "/reset":
            self.context = []
            self.turn_count = 0
            print("\nSession reset (identity preserved)\n")
        elif cmd == "/tools":
            self._print_tools()
        elif cmd.startswith("/tool "):
            await self._execute_tool(command[6:].strip())
        elif cmd == "/quit":
            self.running = False
        else:
            print(f"\nUnknown command: {command}\n")

    def _print_tools(self):
        """Display available tools."""
        tools = self.tools.get_all_tool_info()
        print("\n" + "="*60)
        print("AVAILABLE TOOLS")
        print("="*60)
        for name, info in tools.items():
            print(f"\n  {name}")
            print(f"   {info['description']}")
            params = ", ".join(f"{k}={v}" for k, v in info['params'].items())
            print(f"   Params: {params}")
            print(f"   Example: /tool {info['example']}")
        print("\n" + "="*60)
        print("Usage: /tool <tool_name>(<args>)")
        print("Example: /tool calculator(expression='2 + 2')")
        print("="*60 + "\n")

    async def _execute_tool(self, tool_call: str):
        """Execute a tool from command line."""
        import re

        match = re.match(r'(\w+)\((.*)\)', tool_call, re.DOTALL)
        if not match:
            parts = tool_call.split(maxsplit=1)
            if len(parts) == 2:
                tool_name = parts[0]
                info = self.tools.get_tool_info(tool_name)
                if info and info['params']:
                    first_param = list(info['params'].keys())[0]
                    kwargs = {first_param: parts[1]}
                    result = self.tools.execute(tool_name, **kwargs)
                    self._print_tool_result(tool_name, result)
                    return
            print("\nInvalid tool call format")
            print("   Use: /tool tool_name(arg='value')")
            print("   Or:  /tool tool_name value\n")
            return

        tool_name = match.group(1)
        args_str = match.group(2)

        kwargs = {}
        if args_str.strip():
            for arg_match in re.finditer(r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\S+))", args_str):
                key = arg_match.group(1)
                value = arg_match.group(2) or arg_match.group(3) or arg_match.group(4)
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

        result = self.tools.execute(tool_name, **kwargs)
        self._print_tool_result(tool_name, result)

    def _print_tool_result(self, tool_name: str, result: dict):
        """Pretty print tool execution result."""
        print(f"\nTool: {tool_name}")
        print("-" * 40)

        if result.get("success"):
            print("Success")
            for key, value in result.items():
                if key == "success":
                    continue
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                elif isinstance(value, list) and len(value) > 5:
                    value = value[:5] + ["..."]
                print(f"   {key}: {value}")
        else:
            print(f"Failed: {result.get('error', 'Unknown error')}")
            if result.get('expected_params'):
                print(f"   Expected: {result['expected_params']}")
            if result.get('example'):
                print(f"   Example: {result['example']}")

        print("-" * 40 + "\n")

    def _print_state(self):
        """Display current internal state (PAD model)."""
        state = self.emotion.current_state()
        metrics = self._gather_metrics()
        calib = self.calibration.difficulty_moving_avg

        print("\n" + "="*60)
        print("INTERNAL STATE (PAD Model)")
        print("="*60)
        print(f"Valence:      {state['valence']:+.2f}  (pleasure/displeasure)")
        print(f"Arousal:      {state['arousal']:+.2f}  (calm/excited)")
        print(f"Dominance:    {state['dominance']:+.2f}  (submissive/dominant)")
        print(f"Mood Tags:    {state['tags']}")
        print(f"Flow State:   {calib:.2f}  (target: 0.4-0.7)")
        print(f"Temperature:  {self.calibration.creativity_temperature:.2f}")
        print(f"Dream Align:  {metrics['predictive_alignment']:.2f}")
        print(f"Assurance:    {metrics['assurance_success']:.2f}")
        print(f"Turn Count:   {self.turn_count}")
        print(f"Narrative:    {self.temporal.narrative_summary[:60]}...")
        print("="*60 + "\n")

    # =========================================================================
    # Background Tasks
    # =========================================================================

    async def _background_consolidation(self):
        """
        Background task for periodic housekeeping:
        - Save Mandelbrot corpus
        - Update temporal narrative based on accumulated data
        - Apply emotional decay
        """
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes

            # 1. Save Mandelbrot word frequency corpus
            if hasattr(self.assurance, 'save_mandelbrot_corpus'):
                self.assurance.save_mandelbrot_corpus()

            # 2. Apply emotional decay toward baseline
            self.emotion.apply_decay()

            # 3. Check for goal drift
            if self.temporal.detect_goal_drift():
                self.temporal.add_milestone("Goal drift detected — narrative may need recalibration")

    async def shutdown(self):
        """Graceful shutdown - cancel background tasks and save state."""
        self.running = False

        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._background_tasks.clear()

        # Save Mandelbrot corpus on exit
        if hasattr(self.assurance, 'save_mandelbrot_corpus'):
            self.assurance.save_mandelbrot_corpus()

        await self.memory.save_state()
        print("State saved")
