# Contributing to the Mnemonic Community

How to share your experience, stories, and improvements with the community.

---

## Ways to Contribute

### Share Your Story

Help others by sharing your experience:

1. **Adoption stories** - How you're using mnemonic
2. **Migration guides** - Specific setups you've migrated from
3. **Tips and tricks** - Patterns you've discovered
4. **Integration guides** - Tool-specific configurations

### Improve Documentation

Found something unclear? Help us improve:

1. **Fix typos and errors** - Small improvements matter
2. **Add examples** - Real-world usage examples
3. **Clarify explanations** - If something confused you, others may struggle too
4. **Translate** - Help make mnemonic accessible globally

### Report Issues

Encountered a problem? Let us know:

1. **Bug reports** - Something not working as expected
2. **Feature requests** - Ideas for improvement
3. **Compatibility issues** - Problems with specific tools or setups

---

## Submitting an Adoption Story

### Option 1: Pull Request

1. Fork the repository
2. Create a new branch:
   ```bash
   git checkout -b story/your-story-name
   ```
3. Add your story to `docs/community/adoption-stories.md`:
   ```markdown
   ### [Your Title]

   **Author:** Your Name / Anonymous
   **Setup:** [Tool(s) used, team size, context]
   **Migrated from:** [Memory Bank / Other / None]

   #### Challenge
   [What problem were you trying to solve?]

   #### Solution
   [How did mnemonic help?]

   #### Results
   [What changed? Be specific where possible.]

   #### Tips
   [What would you tell others adopting mnemonic?]
   ```
4. Commit and push:
   ```bash
   git commit -m "Add adoption story: [Your Title]"
   git push origin story/your-story-name
   ```
5. Open a Pull Request

### Option 2: GitHub Discussion

Don't want to open a PR? Share your story in [GitHub Discussions](https://github.com/zircote/mnemonic/discussions).

1. Go to the Discussions tab
2. Create a new discussion in the "Show and tell" category
3. Share your experience

We may reach out to feature your story in the docs (with permission).

### Option 3: Issue

Open an [issue](https://github.com/zircote/mnemonic/issues) with the "story" label.

---

## Documentation Improvements

### Style Guide

When contributing documentation:

- **Be concise** - Developers appreciate brevity
- **Show, don't tell** - Use code examples
- **Test your examples** - Make sure they work
- **Use consistent formatting** - Follow existing patterns

### File Structure

```
docs/
├── community/           # Community-focused docs (you are here)
│   ├── README.md
│   ├── quickstart-memory-bank.md
│   ├── migration-from-memory-bank.md
│   ├── mnemonic-vs-memory-bank.md
│   ├── adoption-stories.md
│   └── CONTRIBUTING-COMMUNITY.md
├── enterprise/          # Enterprise-focused docs
├── integrations/        # Tool-specific guides
└── ...
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b docs/your-improvement
   ```
3. Make your changes
4. Test locally (if applicable)
5. Commit with clear message:
   ```bash
   git commit -m "docs: clarify migration process for Cursor users"
   ```
6. Push and open PR

---

## Bug Reports and Feature Requests

### Bug Reports

Use the [issue tracker](https://github.com/zircote/mnemonic/issues) with this template:

```markdown
**Description**
A clear description of the bug.

**Steps to Reproduce**
1. Run this command...
2. Then do this...
3. See error

**Expected Behavior**
What should have happened.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., macOS 14.2]
- Claude Code version: [e.g., 1.0.0]
- Mnemonic version: [e.g., 1.0.0]

**Additional Context**
Any other relevant information.
```

### Feature Requests

```markdown
**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
What would you like to happen?

**Alternatives Considered**
Any alternative solutions you've considered?

**Additional Context**
Any other relevant information.
```

---

## Community Guidelines

### Be Respectful

- Treat everyone with respect
- Be patient with newcomers
- Give constructive feedback

### Be Helpful

- Share your knowledge
- Answer questions when you can
- Point to relevant resources

### Be Honest

- Share both successes and failures
- Acknowledge limitations
- Credit others' contributions

---

## Recognition

We appreciate all contributions! Contributors are recognized in:

- **CONTRIBUTORS.md** - All contributors
- **Release notes** - Significant contributions
- **Adoption stories** - Featured community members

---

## Questions?

- **GitHub Issues**: [Ask questions](https://github.com/zircote/mnemonic/issues)
- **Discussions**: [Community forum](https://github.com/zircote/mnemonic/discussions)

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [Issues](https://github.com/zircote/mnemonic/issues) | Report bugs, request features |
| [Discussions](https://github.com/zircote/mnemonic/discussions) | Ask questions, share ideas |
| [Pull Requests](https://github.com/zircote/mnemonic/pulls) | Contribute code and docs |
| [Main CONTRIBUTING](../../CONTRIBUTING.md) | Full contribution guide |

[← Back to Community](./README.md)
