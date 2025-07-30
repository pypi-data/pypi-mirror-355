import click
from .installer import install_hooks

@click.group()
def cli():
    """PostHook CLI for setting up Git hooks."""
    pass

@cli.command()
@click.option('--target', prompt='Path to your repo', help='Target repo path')
def install(target):
    """Install all Git hooks into the target repository."""
    install_hooks(target)
    click.echo(f"✅ All hooks installed to {target}/.git/hooks/")
