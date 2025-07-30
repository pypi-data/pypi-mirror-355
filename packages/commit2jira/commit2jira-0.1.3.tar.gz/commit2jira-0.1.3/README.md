# Posthook

A simple Git hook installer that integrates with Jira and GPT.

## Features

- Copies custom Git hooks into your repository.
- Generates commit messages with GPT.
- Posts commits as comments to Jira tickets.
- Automatically creates a `.env` config file.

## Installation

```bash
pip install posthook && posthook install --target .
