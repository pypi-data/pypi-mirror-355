import click
from .install import install_hooks

@click.group()
def cli():
    """Commit2Jira CLI"""
    pass

@cli.command()
def install():
    """Install Git hook into current repo"""
    import os
    repo_path = os.getcwd()
    install_hooks(repo_path)
