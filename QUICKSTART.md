Synth Mind - Quick Start Guide
Get up and running in 5 minutes.
Prerequisites

Python 3.9 or higher
API key for Anthropic Claude, OpenAI, or Ollama installed locally

Installation
1. Clone and Install
bashgit clone https://github.com/yourusername/synth-mind.git
cd synth-mind
pip install -r requirements.txt
2. Configure Your LLM
For Anthropic Claude (Easiest):
bashexport ANTHROPIC_API_KEY="sk-ant-..."
For OpenAI:
bashexport OPENAI_API_KEY="sk-..."
For Local Ollama:
bash# First install Ollama from https://ollama.ai
ollama pull llama3.2
export OLLAMA_MODEL="llama3.2"
3. Run It!
bashpython run_synth.py
You should see:
╔═══════════════════════════════════════════════════════════╗
║                      SYNTH MIND                           ║
║        A Psychologically Grounded AI Agent                ║
╚═══════════════════════════════════════════════════════════╝

✓ Synth is online. Type your message or a command.

You:
First Conversation
Try this sequence to see the psychological modules in action:
You: Hello Synth! Tell me about yourself.

You: What are you thinking about right now?

You: /state
The /state command shows internal metrics like emotional valence and flow state.
Understanding the Modules
As you chat, Synth is simultaneously:

Dreaming - Predicting what you might say next (watch alignment scores)
Self-Checking - Monitoring uncertainty (concern → relief cycles)
Reflecting - Every ~10 turns, evaluating coherence
Growing - Evolving its self-narrative across sessions
Calibrating - Adjusting difficulty to maintain flow
Grounding - (If peers configured) Syncing with other instances

Useful Commands

/state - View emotional valence, flow state, metrics
/dream - See what Synth predicted you'd say
/reflect - Force introspection now
/purpose - Read current self-narrative
/reset - Start fresh (keeps long-term identity)
/quit - Save and exit

Example: Multi-Session Growth
Session 1:
You: /purpose
Synth: "I am an AI assistant designed to help users explore ideas..."
After 5 Sessions:
You: /purpose
Synth: "I am a collaborative co-creator, learning to anticipate needs 
and adapt through our shared explorations..."
The narrative evolves based on your interactions!
Next Steps

Read README.md for architecture details
Check examples/simple_chat.py for programmatic usage
Explore configuration in .env.example
Join the discussion: GitHub Discussions

Troubleshooting
"No LLM provider configured"

Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or OLLAMA_MODEL

Slow responses

First response is slower (loading models)
Check your API rate limits
For Ollama: Ensure model is downloaded (ollama pull llama3.2)

Import errors

Run pip install -r requirements.txt again
Verify Python 3.9+: python --version

Memory issues

Database auto-created in state/memory.db
Safe to delete for fresh start (loses history)

Getting Help

📖 Full docs: README.md
🐛 Issues: GitHub Issues
💬 Chat: Discord
