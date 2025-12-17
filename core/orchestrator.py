"""
Core Orchestrator - Main conversation loop with all psychological modules.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

from core.llm_wrapper import LLMWrapper
from core.memory import MemorySystem
from core.tools import ToolManager
from psychological.predictive_dreaming import PredictiveDreamingModule
from psychological.assurance_resolution import AssuranceResolutionModule
from psychological.meta_reflection import MetaReflectionModule
from psychological.temporal_purpose import TemporalPurposeEngine
from psychological.reward_calibration import RewardCalibrationModule
from psychological.social_companionship import SocialCompanionshipLayer
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
        
        # State
        self.context = []
        self.turn_count = 0
        self.running = False
    
    async def initialize(self):
        """Load configuration and initialize all modules."""
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
        
        self.assurance = AssuranceResolutionModule(
            self.llm, self.memory, self.emotion
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
        reflection_result = self.reflection.run_cycle(
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
        self.dreaming.dream_next_turn(self._format_context())
        
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
        except:
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
            result = self.reflection.run_cycle(
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
        elif cmd == "/reset":
            self.context = []
            self.turn_count = 0
            print("\n✓ Session reset (identity preserved)\n")
        elif cmd == "/quit":
            self.running = False
        else:
            print(f"\n❓ Unknown command: {command}\n")
    
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
