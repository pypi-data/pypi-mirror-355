# Commit2Jira

Commit2Jira is a simple Git hook that adds your commit messages as comments on Jira tickets. Just include the ticket ID in your commit, and it takes care of the rest.


## Installation

```bash
pip install commit2jira && commit2jira install```

## How to use

Just commit like this:
```bash
git commit -m "TICKET NR Message"```
It will post the message to the ABC-123 ticket in Jira.
