# SlavaTalk - Ukrainian Language Learning App

A Streamlit-based Ukrainian language learning application with AI-powered tutoring, vocabulary management, and interactive quizzes.

## Features

- **AI Tutor**: Generate personalized learning content using OpenAI
- **Interactive Quiz**: Test vocabulary with keyboard shortcuts and TTS
- **Vocabulary Builder**: Web scraping and PDF extraction for vocabulary
- **Progress Dashboard**: Track learning statistics and streaks

## Requirements

- Python 3.9+
- OpenAI API key
- Dependencies in `requirements.txt`

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional, for NLP features)
python -m spacy download uk_core_news_sm

# Run the application
streamlit run streamlit_app.py
```

## Configuration

### Environment Variables

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-openai-api-key"

[openai]
api_key = "your-openai-api-key"  # Alternative format
```

Or set via environment:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Access Policy

This application provides:

1. **Public Features** (no API key required):
   - Vocabulary browsing
   - Basic quiz with existing vocabulary
   - Progress viewing

2. **AI Features** (requires OpenAI API key):
   - AI tutoring and lesson generation
   - Automatic example generation
   - Web content vocabulary extraction
   - Advanced quiz generation

### API Key Security

- Store API keys in `.streamlit/secrets.toml` (gitignored)
- Never commit API keys to version control
- Use environment variables in production
- Set rate limits to control costs

## Project Structure

```
slava_talk/
|-- streamlit_app.py       # Main application entry
|-- pages/                  # Streamlit multi-page setup
|   |-- 1_Document_Study.py
|   |-- 2_Quiz.py
|   |-- 3_Progress_Dashboard.py
|   |-- 4_AI_Tutor.py
|   `-- 5_Vocabulary_Builder.py
|-- modules/               # Core functionality
|   |-- ai_client.py       # OpenAI integration
|   |-- crawler.py         # Web scraping
|   |-- pdf_processor.py   # PDF extraction
|   |-- vocab_manager.py   # Vocabulary CRUD
|   `-- ui_components.py   # Reusable UI elements
|-- data/                  # Vocabulary data (JSON)
|-- assets/                # CSS, images
|-- .streamlit/            # Streamlit configuration
`-- _DevDoc/               # Development documentation
```

## Development Status

**Version**: 1.0.0
**Status**: Pre-Production (Security fixes needed)

See [_DevDoc/CODE_AUDIT_REPORT.md](_DevDoc/CODE_AUDIT_REPORT.md) for detailed audit findings.

### Known Issues

1. **Security**: URL validation needed for web crawler (SSRF risk)
2. **Security**: XSS sanitization improvements needed
3. **Testing**: No automated test suite yet
4. **Performance**: Quiz page needs refactoring (800+ lines)

### Roadmap

- [ ] Add comprehensive test suite
- [ ] Implement URL validation
- [ ] Add HTML sanitization
- [ ] Refactor Quiz page into components
- [ ] Add structured logging

## Documentation

| Document | Description |
|----------|-------------|
| [BATON_TOUCH.md](BATON_TOUCH.md) | Handoff notes and improvement directives |
| [UI_UX.md](UI_UX.md) | UI/UX design documentation |
| [_DevDoc/CODE_AUDIT_REPORT.md](_DevDoc/CODE_AUDIT_REPORT.md) | Comprehensive code audit |

## Contributing

1. Ensure all security fixes are applied before production
2. Add tests for any new features
3. Follow existing code style and patterns
4. Update documentation as needed

## License

Private repository - See project owner for license terms.

---

*Last Updated: 2025-12-10*
