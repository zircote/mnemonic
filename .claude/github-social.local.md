---
# Image generation provider
provider: svg

# SVG-specific settings
svg_style: geometric

# Dark mode support
dark_mode: true

# Output settings
output_path: .github/social-preview.svg
dimensions: 1280x640
include_text: true
colors: dark

# README infographic settings
infographic_output: .github/readme-infographic.svg
infographic_style: hybrid

# Upload to repository (requires gh CLI)
upload_to_repo: false
---

# GitHub Social Plugin Configuration

This configuration was created by `/github-social:setup`.

## Current Settings

- **Provider**: SVG (Claude-generated graphics)
- **Style**: Geometric (8-15 shapes representing domain metaphors)
- **Dark Mode**: Dark only
- **Output**: `.github/social-preview.svg`

## Commands

- `/github-social:social-preview` - Generate social preview image
- `/github-social:readme-enhance` - Add badges and infographic to README
- `/github-social:repo-metadata` - Generate optimized description and topics
- `/github-social:all` - Run all skills in sequence

## Overrides

Override settings via command flags:
```bash
/social-preview --style=minimal --dark-mode=both
```
