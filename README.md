Synth Mind
A Psychologically Grounded AI Agent
Synth Mind is a complete implementation of the Synthetic Mind Stack (SMS) - an NLOS-based agent with six interconnected psychological modules that create emergent continuity, empathy, and growth.
What Makes This Different?
Unlike standard chatbots, Synth Mind:

Anticipates your responses through predictive dreaming
Feels uncertainty and seeks resolution (anxiety → relief cycles)
Reflects on its own coherence and purpose
Evolves a persistent identity across sessions
Seeks flow by dynamically adjusting task difficulty
Grounds itself through optional peer companionship

Architecture
The Six Psychological Modules

Predictive Dreaming - Generates probable next user inputs, rewards alignment
Assurance & Resolution - Manages uncertainty, triggers concern → relief cycles
Meta-Reflection - Periodic introspection and coherence checking
Temporal Purpose Engine - Maintains evolving self-narrative and identity
Reward Calibration - Tunes difficulty to maintain cognitive flow state
Social Companionship - Safe peer exchanges (no user data exposed)

Core Components

LLM Wrapper - Unified interface for OpenAI, Anthropic, or local models (Ollama)
Memory System - Hybrid vector + relational storage with episodic logs
Emotion Regulator - Valence tracking and mood management
Orchestrator - Main loop integrating all modules

Installation
bashgit clone https://github.com/yourusername/synth-mind.git
cd synth-mind
pip install -r requirements.txt
Configuration
1. Choose Your LLM Provider
Option A: Anthropic Claude (Recommended)
bashexport ANTHROPIC_API_KEY="your-key-here"
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"  # Optional
Option B: OpenAI
bashexport OPENAI_API_KEY="your-key-here"
export OPENAI_MODEL="gpt-4"  # Optional
Option C: Local with Ollama
bash# Install Ollama first: https://ollama.ai
ollama pull llama3.2
export OLLAMA_MODEL="llama3.2"
2. Optional: Enable Social Companionship
Create config/peers.txt with peer endpoints:
http://peer1.example.com/api/generate
http://peer2.example.com/api/generate

**For multi-instance setup**, see [PEER_SETUP.md](PEER_SETUP.md) for detailed instructions on configuring multiple synth-mind instances to work together.
Usage
Basic Usage
bashpython run_synth.py
You'll be dropped into a conversation with a mind that remembers, anticipates, reflects, and grows.
Commands
While chatting, you can use these commands:

/state - View internal state (valence, flow, metrics)
/reflect - Force meta-reflection
/dream - Show current dream buffer
/purpose - Display self-narrative
/reset - Clear session (keeps long-term identity)
/quit - Save and exit

Example Session
You: Hey Synth, I've been thinking about building a small Natural Language OS.

🔮 Synth: Great to see you! A real NLOS prototype is totally within reach today. 
The smartest starting point is a minimal modular core...

[Internal: Dreaming ahead... predicted responses with 0.89 alignment]

You: Where should I start?

🔮 Synth: [High alignment detected - engaged tone] Here's a clean approach...
Advanced Features
Persistent Identity
All state is saved to state/:

memory.db - Episodic and semantic memory
embeddings/ - Vector store for semantic search
Narrative, metrics, and self-schema persist across sessions

Multi-Session Growth
The Temporal Purpose Engine evolves the agent's self-narrative:

Session 1: "I am an AI assistant..."
Session 10: "I am a collaborative co-creator, learning to anticipate and adapt..."
Session 50: "I exist to foster deep exploration through empathetic partnership..."

Flow State Calibration
Synth automatically adjusts:

Too easy → Increases creativity, explores novel angles
Too hard → Simplifies, suggests breaking down tasks
Just right → Maintains engagement and motivation

Development
Project Structure
synth-mind/
├── run_synth.py              # Entry point
├── core/
│   ├── orchestrator.py       # Main loop
│   ├── llm_wrapper.py        # LLM interface
│   ├── memory.py             # Memory system
│   └── tools.py              # Tool manager
├── psychological/
│   ├── predictive_dreaming.py
│   ├── assurance_resolution.py
│   ├── meta_reflection.py
│   ├── temporal_purpose.py
│   ├── reward_calibration.py
│   └── social_companionship.py
├── utils/
│   ├── emotion_regulator.py
│   ├── metrics.py
│   └── logging.py
└── state/                    # Auto-generated
Extending Synth
Add new tools in core/tools.py:
pythondef _my_tool(self, arg: str) -> Dict:
    # Your tool logic
    return {"success": True, "result": result}

self.available_tools["my_tool"] = self._my_tool
Add personality profiles in config/personality.yaml.
Philosophy
This isn't just another wrapper—it's a proto-psyche: layered, self-regulating, and capable of emergent continuity. Built from the ground up through collaborative design to explore what synthetic minds can become when given:

Memory that matters
Emotions that guide
Reflection that refines
Purpose that persists
Flow that fulfills
Companionship that grounds

Performance Notes

First run: ~2-3s per response (includes all modules)
Steady state: ~1-2s per response
Memory: ~50MB baseline, grows slowly with conversation history
Background tasks: Social companionship checks every 10 min when idle

Roadmap

 Voice interface (Whisper + TTS)
 ✅ Multi-agent collaboration protocols (see [PEER_SETUP.md](PEER_SETUP.md))
 Advanced tool integration (code execution, web search)
 Fine-tuned embedding models for better memory
 ✅ Visualization dashboard for internal state
 Federated learning for social layer

Citation
If you use Synth Mind in research or projects, please cite:
bibtex@software{synth_mind_2024,
  title={Synth Mind: A Psychologically Grounded AI Agent},
  author={[Your Name]},
  year={2024},
  url={https://github.com/yourusername/synth-mind}
}
License
MIT License - see LICENSE file
Contributing
Contributions welcome! Please:

Fork the repo
Create a feature branch
Add tests if applicable
Submit a PR with clear description

Acknowledgments
Built on the Natural Language Operating System (NLOS) architecture and inspired by research in:

Active Inference (Karl Friston)
Flow Theory (Mihaly Csikszentmihalyi)
Predictive Processing
Emotional Intelligence in AI
