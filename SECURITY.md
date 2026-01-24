# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Mnemonic, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to the maintainers privately
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Initial response**: Within 48 hours
- **Assessment**: Within 7 days
- **Fix timeline**: Based on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: Next release

## Security Considerations

### Memory Storage

Mnemonic stores memories as plaintext markdown files. Consider:

- **Sensitive data**: Do not store secrets, credentials, or PII in memories
- **File permissions**: Memory directories should have appropriate permissions
- **Git history**: Memories are version-controlled; sensitive data persists in history

### Hook Execution

Hooks execute Python code with user privileges:

- Review hook code before installation
- Hooks can read/write files and execute commands
- Only install plugins from trusted sources

### Integration Security

When integrating with other tools:

- API keys and tokens should not be stored in memory files
- Use environment variables for sensitive configuration
- Review integration templates before deploying

## Best Practices

1. **Review before capture**: Don't automatically capture sensitive information
2. **Audit memories**: Periodically review stored memories for sensitive content
3. **Access control**: Ensure memory directories have appropriate permissions
4. **Backup encryption**: If backing up memories, encrypt the backups
