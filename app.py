#!/usr/bin/env python3
"""
HeroHours Easy Launcher
Run this file directly to start the HeroHours system.
It will automatically set up the virtual environment and start the server.

Usage:
    python3 app.py              # Start development server
    python3 app.py test         # Run test suite
    python3 app.py migrate      # Run database migrations
    python3 app.py createsuperuser  # Create admin user
"""
import os
import sys
import subprocess
import platform
import secrets


def get_venv_python():
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python3")


def get_venv_pip():
    """Get the path to pip in the virtual environment."""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    else:
        return os.path.join("venv", "bin", "pip3")


def venv_exists():
    """Check if virtual environment exists."""
    return os.path.exists("venv") and os.path.exists(get_venv_python())


def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    if os.path.exists(".env"):
        return True
    
    if not os.path.exists(".env.example"):
        print("⚠️  No .env.example found. Creating basic .env file...")
    
    print("🔐 Creating .env file for development...")
    
    # Generate a secure random secret key
    secret_key = secrets.token_urlsafe(50)
    
    env_content = f"""SECRET_KEY={secret_key}
DEBUG=True
DJANGO_DATABASE=local
APP_SCRIPT_URL=https://script.google.com/macros/s/PLACEHOLDER/exec
DATABASE_URL=sqlite:///./db.sqlite3
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("   Using local SQLite database for development")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def create_venv():
    """Create a virtual environment."""
    print("🔧 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def install_requirements():
    """Install dependencies from requirements.txt."""
    if not os.path.exists("requirements.txt"):
        print("⚠️  No requirements.txt found. Skipping dependency installation.")
        return True
    
    print("📦 Installing dependencies...")
    pip_path = get_venv_pip()
    try:
        subprocess.run([pip_path, "install", "-q", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_migrations():
    """Run Django database migrations."""
    print("🔄 Running database migrations...")
    python_path = get_venv_python()
    try:
        subprocess.run([python_path, "manage.py", "migrate"], check=True)
        print("✅ Migrations completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Migration warning: {e}")
        # Continue anyway as migrations might already be applied
        return True


def register_superusers():
    """Register superusers from superusers.json file."""
    python_path = get_venv_python()
    try:
        result = subprocess.run([python_path, "manage.py", "register_superusers"], 
                               check=True, capture_output=True, text=True)
        # Print the output from the command
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        # Print any output even if command failed
        if e.stdout:
            print(e.stdout.strip())
        if e.stderr:
            print(e.stderr.strip())
        # Continue anyway
        return True


def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    python_path = get_venv_python()
    try:
        subprocess.run([python_path, "manage.py", "test"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False


def start_server():
    """Start the Django development server."""
    print("\n" + "="*60)
    print("🚀 Starting HeroHours development server...")
    print("="*60)
    print("\n📍 Server will be available at: http://127.0.0.1:8000")
    print("📍 Admin panel at: http://127.0.0.1:8000/admin")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    python_path = get_venv_python()
    try:
        subprocess.run([python_path, "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server error: {e}")
        return False
    return True


def run_management_command(command):
    """Run a Django management command."""
    python_path = get_venv_python()
    try:
        subprocess.run([python_path, "manage.py"] + command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False


def setup_environment():
    """Set up the environment (env file, venv, dependencies, migrations)."""
    # Create .env file if it doesn't exist
    if not create_env_file():
        return False
    
    # Check if venv exists, create if not
    if not venv_exists():
        print("📦 Virtual environment not found.")
        if not create_venv():
            return False
    else:
        print("✅ Virtual environment found.")
    
    # Install dependencies
    if not install_requirements():
        print("⚠️  Continuing despite installation issues...")
    
    # Run migrations
    if not run_migrations():
        print("⚠️  Continuing despite migration issues...")
    
    # Register superusers from configuration file
    register_superusers()
    
    return True


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🦸 HeroHours - FRC Time Tracking System")
    print("="*60 + "\n")
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Handle special commands
    if args and args[0] == "test":
        if not setup_environment():
            sys.exit(1)
        sys.exit(0 if run_tests() else 1)
    elif args and args[0] in ["migrate", "createsuperuser", "collectstatic", "shell"]:
        if not setup_environment():
            sys.exit(1)
        sys.exit(0 if run_management_command(args) else 1)
    elif args and args[0] == "setup":
        # Just run setup without starting server
        sys.exit(0 if setup_environment() else 1)
    elif args and args[0] == "help":
        print(__doc__)
        sys.exit(0)
    else:
        # Default: setup and start server
        if not setup_environment():
            print("\n❌ Setup failed. Please fix the errors above and try again.")
            sys.exit(1)
        
        # Start the server
        start_server()


if __name__ == "__main__":
    main()