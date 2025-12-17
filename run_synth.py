#!/usr/bin/env python3
"""
Synth Mind - Main Entry Point
A psychologically grounded AI agent with full cognitive substrate.
"""

import asyncio
import sys
from pathlib import Path

from core.orchestrator import SynthOrchestrator
from utils.logging import setup_logging

def print_banner():
    """Display startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║                      SYNTH MIND                           ║
    ║                                                           ║
    ║        A Psychologically Grounded AI Agent                ║
    ║                                                           ║
    ║  Modules: Dreaming | Assurance | Reflection              ║
    ║           Purpose | Calibration | Companionship          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Commands:
      /state           - View internal state (valence, flow, metrics)
      /reflect         - Trigger meta-reflection
      /dream           - Show current dream buffer
      /purpose         - Display self-narrative
      /project [desc]  - Start systematic project (GDIL)
      /project status  - View active project progress
      /resume project  - Resume paused project
      /reset           - Clear session (keeps long-term identity)
      /quit            - Save and exit
    
    """
    print(banner)

async def main():
    """Main async entry point."""
    # Setup
    setup_logging()
    print_banner()
    
    # Initialize orchestrator (loads all modules)
    try:
        orchestrator = SynthOrchestrator()
        await orchestrator.initialize()
    except Exception as e:
        print(f"❌ Failed to initialize Synth: {e}")
        print("Check your config files and API keys.")
        sys.exit(1)
    
    print("✓ Synth is online. Type your message or a command.\n")
    
    # Main conversation loop
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nGracefully shutting down...")
    finally:
        await orchestrator.shutdown()
        print("Synth has been saved. Until next time, co-creator.")

if __name__ == "__main__":
    asyncio.run(main())
