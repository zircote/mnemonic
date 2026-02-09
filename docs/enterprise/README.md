# Mnemonic for Enterprise

Enterprise-grade AI memory with complete audit trails, data sovereignty, and research-validated performance.

## Quick Facts

| Metric | Value | Source |
|--------|-------|--------|
| **Accuracy** | 74.0% vs 68.5% for competitors | [Letta LoCoMo Benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory) |
| **Audit Trail** | Complete git history | Every change tracked with who, when, what |
| **Data Sovereignty** | 100% local storage | No cloud, no third-party dependencies |
| **Integration** | Claude Code plugin | Native integration with Claude Code |
| **Format** | MIF Level 3 | Open standard, human-readable |

---

## Research-Validated Performance

Traditional AI memory systems use vector databases or knowledge graphs. Research shows this adds complexity without improving accuracy.

**Letta's LoCoMo Benchmark Results:**

```
Filesystem approach:  ████████████████████████ 74.0%
Mem0 (graph-based):   ████████████████████   68.5%
                      ─────────────────────────────
                      0%                       100%
```

The reason? LLMs are pretrained on filesystem operations. Simple tools are more reliable than specialized abstractions.

Read more: ["From Everything is a File to Files Are All You Need"](https://arxiv.org/abs/2601.11672) (arXiv:2601.11672)

---

## For Enterprise Architects

**You need:** Compliance, governance, audit trails, data sovereignty

**Mnemonic delivers:**
- Full git history of every memory change (who, when, what, why)
- Local-only storage—no cloud, no third-party dependencies
- Human-readable markdown format for audit reviews
- Bi-temporal tracking (valid time vs recorded time) per SQL:2011 standard
- MIF schema validation for data quality assurance

[→ Read the Compliance & Governance Guide](./compliance-governance.md)

---

## For Engineering Managers

**You need:** Team productivity, knowledge retention, tool flexibility

**Mnemonic delivers:**
- Cross-session memory reduces context switching overhead
- Open format prevents vendor lock-in
- Shared patterns namespace accelerates team onboarding
- Episodic memory reduces repeated debugging efforts
- Zero infrastructure costs—pure filesystem storage

[→ Read the Productivity & ROI Guide](./productivity-roi.md)

---

## For Individual Developers

**You need:** Privacy, control, customization

**Mnemonic delivers:**
- Zero telemetry—your memories stay on your machine
- Git-based, readable format you can edit directly
- Scriptable via standard Unix tools (grep, find, ripgrep)
- Portable MIF Level 3 format works across all tools
- Works offline—no network required

[→ Read the Developer Experience Guide](./developer-experience.md)

---

## Technical Deep Dive

For technical decision-makers who need academic validation and competitive analysis:

[→ Research Validation & Benchmarks](./research-validation.md)

---

## Deployment

For platform teams and DevOps planning enterprise rollout:

[→ Enterprise Deployment Guide](./deployment-guide.md)

---

## Enterprise Advantages Summary

| Capability | Mnemonic | Cloud-Based Alternatives |
|------------|----------|-------------------------|
| **Audit Trail** | Full git history with diffs | Limited or API-only access |
| **Data Sovereignty** | 100% local storage | Data on third-party servers |
| **Offline Access** | Always available | Requires network |
| **Vendor Lock-in** | None (open format) | Proprietary formats |
| **Cost** | Zero (filesystem) | Per-seat or usage fees |
| **Compliance** | Self-hosted, auditable | Depends on vendor |
| **Research Validation** | 74% accuracy benchmark | Varies |

---

## Getting Started

```bash
# Install the plugin
claude settings plugins add /path/to/mnemonic

# Initialize for your project
/mnemonic:setup

# Capture your first memory
/mnemonic:capture decisions "Use PostgreSQL for storage"

# Recall happens automatically—memories load when relevant
```

---

## Navigation

- [Compliance & Governance](./compliance-governance.md) - For architects
- [Productivity & ROI](./productivity-roi.md) - For managers
- [Developer Experience](./developer-experience.md) - For developers
- [Research Validation](./research-validation.md) - Technical deep dive
- [Deployment Guide](./deployment-guide.md) - For operations

[← Back to Main Documentation](../../README.md)
