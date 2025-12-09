# Tools Directory

Development and utility scripts for the 2025-Public-Friend project.

## Scripts

### batch_update_examples.py

Batch vocabulary example updater using OpenAI API. Generates contextual example sentences for vocabulary entries.

**Usage:**
```bash
# Set API key via environment variable (recommended)
export OPENAI_API_KEY=sk-...
python3 tools/batch_update_examples.py

# Or specify API key directly (less secure)
python3 tools/batch_update_examples.py --api-key sk-...

# Specify custom data file
python3 tools/batch_update_examples.py --data-file /path/to/vocabulary.json
```

**Requirements:**
- OpenAI API key
- slava_talk/modules/ai_example_generator.py

### openai_responses_diagnose.py

OpenAI API diagnostic tool for testing API connectivity and troubleshooting issues.

**Usage:**
```bash
# Basic diagnostic
export OPENAI_API_KEY=sk-...
python3 tools/openai_responses_diagnose.py

# Custom model and prompt
python3 tools/openai_responses_diagnose.py --model gpt-4o-mini --prompt "Hello!"
```

**Features:**
- Tests API connectivity
- Provides error diagnosis with resolution guides
- Displays token usage and response details

## Configuration

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY`: Your OpenAI API key

### Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** instead of command-line arguments
3. Command-line `--api-key` is visible in:
   - Shell history (`~/.bash_history`)
   - Process lists (`ps aux`)
   - System logs

## Dependencies

```
openai>=1.12.0
```

For batch_update_examples.py, the slava_talk modules must be available in the Python path.

## Audit Status

See [../_DevDoc/2025-12-10_Claude_tools_v1.0.0.md](../_DevDoc/2025-12-10_Claude_tools_v1.0.0.md) for detailed code audit.

| Script | Status | Score |
|--------|--------|-------|
| openai_responses_diagnose.py | Production Ready | 7.8/10 |
| batch_update_examples.py | Fixed | 7/10 |

## Known Issues

1. batch_update_examples.py depends on slava_talk modules
2. API key exposure risk with `--api-key` flag (use env vars instead)

---

*Last Updated: 2025-12-10*
