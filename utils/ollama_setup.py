"""
Ollama Setup Utility
Helps users automatically install and configure Ollama if not available.
"""

import subprocess
import sys
from typing import Optional


def check_ollama_installed() -> bool:
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_ollama_running() -> bool:
    """Check if Ollama service is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def list_available_models() -> list:
    """List models available in Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = [line.split()[0] for line in lines if line.strip()]
            return models
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def install_ollama() -> bool:
    """Install Ollama using the official install script."""
    print("\n🔧 Installing Ollama...")
    print("This may take a few minutes.\n")

    try:
        # Download and run install script
        result = subprocess.run(
            ["curl", "-fsSL", "https://ollama.com/install.sh"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"❌ Failed to download install script: {result.stderr}")
            return False

        # Run the install script
        install_result = subprocess.run(
            ["sh"],
            input=result.stdout,
            text=True,
            timeout=300  # 5 minutes
        )

        if install_result.returncode == 0:
            print("✅ Ollama installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {install_result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False


def start_ollama_service() -> bool:
    """Start the Ollama service in the background."""
    try:
        print("🚀 Starting Ollama service...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait a moment for service to start
        import time
        time.sleep(2)

        if check_ollama_running():
            print("✅ Ollama service started!")
            return True
        else:
            print("⚠️  Ollama service may not have started correctly")
            return False
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False


def pull_model(model_name: str = "llama3.2") -> bool:
    """Pull a model from Ollama registry."""
    print(f"\n📥 Pulling model '{model_name}'...")
    print("This may take several minutes depending on model size.\n")

    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            timeout=600  # 10 minutes
        )

        if result.returncode == 0:
            print(f"\n✅ Model '{model_name}' pulled successfully!")
            return True
        else:
            print(f"\n❌ Failed to pull model '{model_name}'")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ Model download timed out")
        return False
    except Exception as e:
        print(f"\n❌ Error pulling model: {e}")
        return False


def prompt_ollama_setup() -> tuple[bool, Optional[str]]:
    """
    Interactive prompt to help user set up Ollama.
    Returns (success, model_name) tuple.
    """
    print("\n" + "=" * 60)
    print("🤖 No LLM Provider Configured")
    print("=" * 60)
    print("\nYou have three options:")
    print("  1. Use Ollama (Free, Local, Private)")
    print("  2. Use Anthropic Claude (API key required)")
    print("  3. Use OpenAI GPT (API key required)")
    print()

    # Check if running in non-interactive environment
    if not sys.stdin.isatty():
        print("⚠️  Running in non-interactive mode.")
        print("\nTo use Synth Mind, please set one of these environment variables:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export OLLAMA_MODEL='llama3.2'  # if Ollama is installed")
        print("\nOr run from an interactive terminal.")
        return False, None

    # Check if Ollama is already installed
    ollama_installed = check_ollama_installed()

    if not ollama_installed:
        print("Ollama is not installed on this system.")
        print()
        try:
            choice = input("Would you like to install Ollama? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n⚠️  Interactive input not available.")
            print("Set an environment variable instead:")
            print("  export ANTHROPIC_API_KEY='your-key'")
            return False, None

        if choice != 'y':
            print("\nTo use Synth Mind, you can:")
            print("  • Set ANTHROPIC_API_KEY environment variable")
            print("  • Set OPENAI_API_KEY environment variable")
            print("  • Install Ollama manually: https://ollama.com")
            return False, None

        # Install Ollama
        if not install_ollama():
            return False, None

        ollama_installed = True

    # Check if Ollama is running
    if not check_ollama_running():
        print("\nOllama service is not running.")
        choice = input("Start Ollama service? (y/n): ").strip().lower()

        if choice == 'y':
            if not start_ollama_service():
                return False, None
        else:
            print("\nYou can start Ollama manually with: ollama serve")
            return False, None

    # Check available models
    models = list_available_models()

    if models:
        print(f"\n✅ Found {len(models)} installed model(s):")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")

        print(f"\nUsing model: {models[0]}")
        return True, models[0]
    else:
        print("\n📦 No models installed yet.")
        print("\nRecommended models:")
        print("  1. llama3.2   - Balanced quality and speed (2-3GB)")
        print("  2. llama3.1   - Higher quality (4-8GB)")
        print("  3. mistral    - Fast and efficient (4GB)")
        print("  4. qwen2.5    - Good for coding (4-7GB)")
        print()

        model_choice = input("Which model would you like? [1-4, or custom name] (default: 1): ").strip()

        model_map = {
            "1": "llama3.2",
            "2": "llama3.1",
            "3": "mistral",
            "4": "qwen2.5",
            "": "llama3.2"  # default
        }

        model_name = model_map.get(model_choice, model_choice)

        if pull_model(model_name):
            return True, model_name
        else:
            return False, None


if __name__ == "__main__":
    # Test the setup
    success, model = prompt_ollama_setup()
    if success:
        print(f"\n✅ Setup complete! Use: export OLLAMA_MODEL={model}")
    else:
        print("\n❌ Setup incomplete")
