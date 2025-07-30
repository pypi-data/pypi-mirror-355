#!/usr/bin/env python3
"""
GatherSDK CLI - Simple commands to get started with GatherChat agents
"""

import os
import shutil
import click
from pathlib import Path

# Get the package directory to find templates
PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"


@click.group()
@click.version_option()
def main():
    """
    GatherSDK - Build AI agents for GatherChat in minutes
    
    Get started with: gathersdk init
    """
    pass


@main.command()
@click.option('--force', '-f', is_flag=True, help='Overwrite existing files')
def init(force):
    """
    Initialize a new GatherChat agent project
    
    Creates:
    - agent.py (Pydantic AI example)
    - .env.example (configuration template)
    """
    current_dir = Path.cwd()
    
    # Files to create
    files_to_create = [
        ("agent.py", "agent.py"),
        (".env.example", ".env.example")
    ]
    
    click.echo("🚀 Initializing GatherChat agent project...")
    
    # Check if files already exist
    existing_files = []
    for dest_name, _ in files_to_create:
        dest_path = current_dir / dest_name
        if dest_path.exists():
            existing_files.append(dest_name)
    
    if existing_files and not force:
        click.echo(f"❌ Files already exist: {', '.join(existing_files)}")
        click.echo("   Use --force to overwrite")
        return
    
    # Copy template files
    for dest_name, template_name in files_to_create:
        template_path = TEMPLATES_DIR / template_name
        dest_path = current_dir / dest_name
        
        if not template_path.exists():
            click.echo(f"❌ Template not found: {template_path}")
            continue
            
        try:
            shutil.copy2(template_path, dest_path)
            click.echo(f"✅ Created {dest_name}")
        except Exception as e:
            click.echo(f"❌ Failed to create {dest_name}: {e}")
            continue
    
    # Make agent.py executable
    agent_path = current_dir / "agent.py"
    if agent_path.exists():
        agent_path.chmod(0o755)
    
    click.echo("")
    click.echo("🎉 Project initialized successfully!")
    click.echo("")
    click.echo("Next steps:")
    click.echo("1. Copy .env.example to .env and add your keys:")
    click.echo("   cp .env.example .env")
    click.echo("")
    click.echo("2. Get your agent key from https://gather.is/developer")
    click.echo("")
    click.echo("3. Add your OpenAI API key to .env")
    click.echo("")
    click.echo("4. Run your agent:")
    click.echo("   python agent.py")
    click.echo("")
    click.echo("🤖 Your agent will be live in GatherChat!")


if __name__ == "__main__":
    main()