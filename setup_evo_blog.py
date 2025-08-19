#!/usr/bin/env python3
"""
Setup script for EvoBlog Public
Automates the installation and configuration process
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_prerequisites():
    """Check if prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check for uv or pip
    uv_available = subprocess.run("which uv", shell=True, capture_output=True).returncode == 0
    pip_available = subprocess.run("which pip", shell=True, capture_output=True).returncode == 0
    
    if not (uv_available or pip_available):
        print("❌ Neither uv nor pip found. Please install pip at minimum.")
        return False
    
    print(f"✅ Package manager available: {'uv' if uv_available else 'pip'}")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment"""
    if os.path.exists(".venv"):
        print("📁 Virtual environment already exists")
        return True
    
    # Try uv first, fall back to venv
    if subprocess.run("which uv", shell=True, capture_output=True).returncode == 0:
        return run_command("uv venv .venv", "Creating virtual environment with uv")
    else:
        return run_command("python -m venv .venv", "Creating virtual environment with venv")

def install_dependencies():
    """Install Python dependencies"""
    activate_cmd = "source .venv/bin/activate" if os.name != 'nt' else ".venv\\Scripts\\activate"
    
    # Try uv first, fall back to pip
    if subprocess.run("which uv", shell=True, capture_output=True).returncode == 0:
        return run_command("uv pip install -r requirements.txt", "Installing dependencies with uv")
    else:
        return run_command(f"{activate_cmd} && pip install -r requirements.txt", "Installing dependencies with pip")

def setup_configuration():
    """Set up configuration files"""
    print("⚙️  Setting up configuration files...")
    
    # Copy .env.example to .env if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Created .env from .env.example")
        else:
            print("⚠️  .env.example not found, skipping .env creation")
    else:
        print("📁 .env already exists")
    
    # Copy model_configs.json.example if needed
    config_dir = Path("config")
    if config_dir.exists():
        example_config = config_dir / "model_configs.json.example"
        config_file = config_dir / "model_configs.json"
        
        if example_config.exists() and not config_file.exists():
            shutil.copy(example_config, config_file)
            print("✅ Created config/model_configs.json from example")
        elif config_file.exists():
            print("📁 config/model_configs.json already exists")
    
    return True

def test_installation():
    """Test the installation with a simple command"""
    print("🧪 Testing installation...")
    
    activate_cmd = "source .venv/bin/activate" if os.name != 'nt' else ".venv\\Scripts\\activate"
    test_cmd = f"{activate_cmd} && python -c 'import anthropic; print(\"Anthropic library imported successfully\")'"
    
    return run_command(test_cmd, "Testing core dependencies")

def print_next_steps():
    """Print instructions for completing the setup"""
    print("\n🎉 Installation complete! Next steps:")
    print("\n1. Configure your API keys:")
    print("   Edit .env file and add your API keys:")
    print("   ANTHROPIC_API_KEY=your_key_here")
    print("   OPENAI_API_KEY=your_key_here (optional)")
    print("   GOOGLE_API_KEY=your_key_here (optional)")
    
    print("\n2. Activate the virtual environment:")
    if os.name == 'nt':
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    
    print("\n3. Test with a simple generation:")
    print("   python scripts/generate_blog_post.py \"Test topic: AI in startups\" --cycles 1")
    
    print("\n4. Read the README.md for advanced usage")

def main():
    """Main setup function"""
    print("🚀 EvoBlog Public Setup")
    print("=" * 30)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup steps
    steps = [
        setup_virtual_environment,
        install_dependencies,
        setup_configuration,
        test_installation,
    ]
    
    for step in steps:
        if not step():
            print(f"\n❌ Setup failed at: {step.__name__}")
            sys.exit(1)
    
    print_next_steps()
    print("\n✅ Setup completed successfully!")

if __name__ == "__main__":
    main()