# Commit2Jira

**Commit2Jira** is a simple Git hook that adds your commit messages as comments on Jira tickets. Just include the ticket ID (e.g. `ABC-123`) in your commit message, and it will automatically post the message to the corresponding Jira ticket.

## Installation

```bash
pip install commit2jira && commit2jira install
```

## How to Use

Simply commit using:

```bash
git commit -m "ABC-123 Your message here"
```

This will post your commit message as a comment on the `ABC-123` ticket in Jira.
