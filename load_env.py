"""
Environment loader for agent_system5

Loads environment variables from .env file if it exists.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print(f"   Please create one based on .env.example")

    # Validate required variables
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key or api_key == "your-api-key-here" or api_key == "":
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set or invalid")
        print("   Please add your API key to .env file")
        print(f"   Location: {env_path}")
        return False

    print(f"✅ ANTHROPIC_API_KEY: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ DASHBOARD_URL: {os.environ.get('DASHBOARD_URL', 'http://localhost:4000')}")

    return True


if __name__ == "__main__":
    # Test loading
    if load_environment():
        print("\n✅ Environment configured correctly")
    else:
        print("\n❌ Environment configuration failed")
        exit(1)
