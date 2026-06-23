# AI-Assisted Development

## Purpose

This document describes how AI tools can support engineering work when used with clear context, review, and constraints.

The goal is not to blindly trust AI, but to use it as an assistant for understanding, drafting, refactoring, documenting, testing, and reviewing work. Human judgment remains the final authority.

## What Are Generative LLMs?

Generative LLMs generate text or code based on patterns and context.
They do not truly understand systems the way humans do.
They can produce useful drafts but can also produce wrong or outdated answers.
They need clear context and human review.

> [!NOTE]
> LLM output can be a very useful starting point, but it may be incorrect, incomplete, or outdated. Always verify the results against documentation and reality.

## What Is Gemini CLI?

Gemini CLI is a terminal-based AI coding assistant that can work with local project context.

Typical use cases:
- understanding a codebase
- explaining files
- drafting documentation
- writing or improving tests
- proposing refactors
- generating scripts
- reviewing changes
- summarizing errors and logs

## Markdown Files and AI Context

Markdown files are useful for AI-assisted work because they are:
- easy to read
- easy to version in Git
- easy to review in pull requests
- easy for AI tools to consume
- good for documenting conventions and decisions

Common examples:
- `README.md`
- `GEMINI.md`
- `docs/*.md`
- ADR documents
- runbooks
- troubleshooting notes

## What Is GEMINI.md?

`GEMINI.md` is used to provide persistent project context and instructions to Gemini CLI.

It should include:
- project purpose
- tech stack
- coding conventions
- test commands
- lint commands
- formatting rules
- project structure
- rules for safe changes
- documentation style
- commands that should not be run without approval

It should not include:
- secrets
- passwords
- tokens
- private credentials
- temporary personal notes
- huge duplicated documentation
- vague instructions

> [!WARNING]
> Secrets, tokens, passwords, and private credentials must never be stored in `GEMINI.md` or any other committed context file.

## Example GEMINI.md for a Python Project

```markdown
# Project Context

This is a Python project.

## Tech Stack

- Python 3.x
- pytest
- ruff
- mypy

## Common Commands

- Run tests: `pytest`
- Run linting: `ruff check .`
- Run formatting: `ruff format .`
- Run type checks: `mypy .`

## Coding Rules

- Keep changes small and reviewable.
- Prefer simple code over clever code.
- Add or update tests when behavior changes.
- Do not change public APIs without explaining why.
- Do not introduce new dependencies without approval.

## AI Assistant Rules

- Explain the plan before making large changes.
- Do not run destructive commands.
- Do not modify secrets or credentials.
- Show diffs or summarize changed files.
- Ask for clarification if requirements are unclear.
```

## What Are Skills?

Skills are reusable instructions or behavior packs that help AI assistants perform specific types of work more consistently.

Examples:
- Python development skill
- documentation writing skill
- testing skill
- Terraform review skill
- API integration skill

Skills should be specific and practical, not generic.

## What Are MCP Servers?

MCP servers are a way to connect the AI assistant to external tools, data, or documentation.

Examples:
- documentation search
- GitHub integration
- issue tracker integration
- cloud documentation
- local tools
- internal APIs

MCP increases capability but also increases risk, because the agent may gain access to tools or data.

> [!NOTE]
> Connecting an MCP server gives the assistant access to external tools or data, depending entirely on what the configured server exposes.

## MCP Examples

### Documentation MCP

Purpose:
- Search official documentation.
- Help answer questions about libraries, tools, APIs, or cloud services.

Useful for:
- checking current syntax
- reading API docs
- comparing configuration options
- reducing outdated answers

Risk:
- The assistant may still summarize incorrectly, so important claims should be verified.

### GitHub MCP

Purpose:
- Read repositories, issues, pull requests, branches, and commits.
- Help summarize changes or review context.

Useful for:
- understanding pull requests
- summarizing issues
- finding related code
- drafting PR descriptions

Risk:
- Write access can be dangerous if enabled.
- Creating branches, comments, issues, or pull requests should require review.

### Local Filesystem MCP

Purpose:
- Give the assistant structured access to local project files.

Useful for:
- reading project structure
- finding references
- updating documentation
- reviewing code

Risk:
- File write access should be controlled.
- Destructive changes must not be approved blindly.

### Cloud Provider MCP

Purpose:
- Query cloud resources, documentation, or account metadata depending on the server.

Useful for:
- reading cloud documentation
- checking resource configuration
- helping with troubleshooting

Risk:
- Never expose credentials in prompts or config files.
- Prefer read-only access.
- Production-changing actions must require human approval.

### Internal Tools MCP

Purpose:
- Connect the assistant to internal APIs, ticketing systems, dashboards, or knowledge bases.

Useful for:
- finding runbooks
- reading incidents
- searching tickets
- summarizing operational context

Risk:
- Access control matters.
- Internal data may be sensitive.
- Avoid sending unnecessary private data to the model.

## Safe Use of MCP

When using MCP:
- only connect trusted MCP servers
- avoid exposing secrets
- understand what tools the MCP server provides
- prefer read-only access where possible
- review actions before execution
- keep project and global configuration separate
- do not blindly approve tool calls

> [!CAUTION]
> Write-capable MCP servers should be treated carefully because the assistant may be able to create issues, modify files, call APIs, or trigger automated actions.

### Example MCP Configuration

This generic example illustrates the shape of an MCP configuration. Real configuration depends on the chosen MCP server. Secrets should not be committed to this configuration file, and read-only access should be preferred first.

```json
{
  "mcpServers": {
    "docs": {
      "command": "example-docs-mcp",
      "args": []
    },
    "github-readonly": {
      "command": "example-github-mcp",
      "args": ["--read-only"]
    }
  }
}
```

## How to Use Gemini CLI in a Python Project

1. Start with context
   - Make sure `README.md` and `GEMINI.md` are clear.
2. Ask for understanding first
   - Example prompt: "Read the project structure and summarize how the application works."
3. Ask for a plan before changes
   - Example prompt: "Before editing files, propose a short plan."
4. Keep changes small
   - Example prompt: "Refactor only this module and do not change behavior."
5. Require tests
   - Example prompt: "Add or update pytest tests for this behavior."
6. Review the diff
   - Example prompt: "Summarize the changed files and explain why each change was needed."
7. Run validation
   - Example prompt: "Run tests and linting. If something fails, explain the failure before fixing it."

> [!TIP]
> The safest workflow is: understand first, plan second, change third, review last.

## AI-Assisted Feature Development Workflow

![AI-assisted feature development workflow](images/ai-assisted-feature-development-flow.png)

### 1. Feature Request

A new feature request is received.

Inputs may include:
- Jira ticket
- product request
- internal requirement
- bug report
- customer request

Goal:

Understand what problem is being solved before discussing implementation details.

Output:
- feature description
- acceptance criteria
- known constraints

### 2. Repository Review

Before writing any code, analyze the existing system.

Questions:
- Which components are affected?
- Which services are involved?
- Are there existing implementations of similar functionality?
- What dependencies exist?
- What areas are considered high-risk?

AI should first explain the current architecture before proposing changes.

Output:
- repository summary
- impacted files
- potential risks

### 3. Feature Plan

Create an implementation plan before generating code.

The plan should answer:
- What files will change?
- Why are they changing?
- What alternative approaches exist?
- What can break?
- How can the feature be rolled back?

Output:
- implementation plan
- testing strategy
- rollback strategy

No code should be written at this stage.

### 4. Human Approval

The engineer reviews the implementation plan.

Purpose:

Prevent AI from making architectural decisions without review.

Questions:
- Does the approach make sense?
- Is the scope reasonable?
- Is the implementation too complex?
- Does it violate existing architecture?

Output:
- approved plan
- revised plan
- rejected plan

### 5. AI Implementation

AI generates code based on the approved plan.

Rules:
- modify only required files
- avoid unrelated refactoring
- explain every change
- explain why each file was modified

Output:
- code changes
- implementation summary

### 6. Local Testing

Verify functionality before opening a PR.

Checks:
- feature works as expected
- no obvious regressions
- unit tests pass
- integration tests pass
- logs look healthy

Output:
- test results
- known issues

### 7. AI Pull Request Review

Use a separate AI review pass.

Prompt example:

```text
Review this pull request as a Staff Engineer.
```

Check:
- correctness
- maintainability
- security risks
- duplicated logic
- production risks
- rollback concerns
- missing tests

Purpose:

Force a second opinion before merge.

Output:
- review findings
- improvement recommendations

### 8. Human Review

Final human verification.

Questions:
- Do I understand the code?
- Can I explain the implementation?
- Can I explain rollback steps?
- Am I comfortable supporting this in production?

Rule:

If the engineer cannot explain the implementation, the PR is not ready.

Output:
- approve
- request changes

### 9. Merge and Deploy

Deploy through the normal delivery pipeline.

Checks:
- deployment succeeded
- application health checks pass
- monitoring shows no regressions
- rollback procedure validated

Output:
- production deployment

### 10. Update Documentation

Capture project knowledge.

Update:
- changelog
- feature notes
- ADRs
- operational documentation

Purpose:

Avoid losing context between AI sessions.

Output:
- documented implementation

### 11. Next Feature Context

Before starting the next feature, review:
- changelog
- feature notes
- ADRs
- previous PR reviews

Purpose:

Provide historical context to AI.

This prevents future sessions from re-discovering information that already exists.

Output:
- project context package
- informed implementation decisions

## Good Prompt Examples

```text
Read this repository and summarize the main components, entry points, and test setup. Do not change files.
```

```text
Review this module for readability and possible bugs. Do not edit anything yet. Give me findings first.
```

```text
Create a small refactor plan for this function. Keep behavior unchanged and include test impact.
```

```text
Add pytest coverage for this edge case. Keep the production code unchanged unless required.
```

```text
Explain this error log and suggest the most likely root cause. Do not make changes yet.
```

```text
Update the documentation to match the current code. Do not invent features that are not present.
```

## Bad Prompt Examples

```text
Fix everything.
```
Too broad.

```text
Rewrite the whole project.
```
Too risky.

```text
Make it production ready.
```
Too vague.

```text
Run whatever commands you need.
```
Unsafe.

## What Not to Delegate Blindly

Do not delegate the following blindly:
- security decisions
- production changes
- infrastructure changes
- dependency upgrades
- authentication/authorization changes
- data migrations
- secrets handling
- incident response actions
- cost-impacting cloud changes

AI can help draft and analyze these, but a human must review and approve.

## Practical Review Checklist

- Did the AI understand the project context?
- Are the changes small and reviewable?
- Are tests included or updated?
- Were new dependencies introduced?
- Were secrets or credentials touched?
- Were commands safe?
- Is the reasoning clear?
- Does the final diff match the original request?

## Recommended Repository Structure

`GEMINI.md` belongs at the repository root because it provides project-level context to the AI assistant.

### Example structure for this repository

```text
.
├── GEMINI.md
├── README.md
├── ansible/
├── docs/
│   ├── ai-assisted-development.md
│   ├── adr-template.md
│   └── runbooks/
└── aws-azure-service-comparison.md
```

### Example structure for a Python project

```text
.
├── GEMINI.md
├── README.md
├── docs/
│   ├── ai-assisted-development.md
│   ├── adr-template.md
│   └── runbooks/
├── src/
└── tests/
```

## Final Notes

- AI is useful when context is clear.
- Markdown makes context reviewable.
- `GEMINI.md` gives project-specific instructions.
- MCP adds tool access, but must be controlled.
- Small changes, tests, and human review are still required.
