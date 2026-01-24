---
applyTo: "{commands/*.md,skills/*/SKILL.md,agents/*.md}"
---

# Claude Code Plugin File Guidelines

## Commands (commands/*.md)

Required frontmatter:
```yaml
---
name: command-name
description: Brief description of what the command does
---
```

Content structure:
- Clear usage instructions
- Examples with expected behavior
- Error handling guidance

## Skills (skills/*/SKILL.md)

Required frontmatter:
```yaml
---
name: skill-name
description: What this skill provides
---
```

Content structure:
- Domain knowledge and context
- Step-by-step procedures
- Decision criteria
- Examples and templates

## Agents (agents/*.md)

Required frontmatter:
```yaml
---
name: agent-name
description: Agent's purpose and capabilities
---
```

Content structure:
- Agent role and responsibilities
- Available tools and actions
- Workflow patterns
- Integration points

## General Guidelines

- Use clear, imperative language
- Include practical examples
- Reference related commands/skills
- Keep frontmatter minimal but complete
