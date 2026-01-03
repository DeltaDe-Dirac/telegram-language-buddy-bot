<!-- Copilot instructions for contributors and AI coding agents -->
# Project-specific Copilot instructions

This file contains concise, actionable guidance for AI coding agents working on this repository.

1. Big picture
- App: a small Flask service started from `src/main.py` (registered routes come from `src/controllers`).
- Major components:
  - `src/controllers/` — HTTP routes and webhook handling (e.g., `bot_controller.py`).
  - `src/models/` — core business logic: `telegram_bot.py`, `database.py`, `free_translator.py`, `voice_transcriber.py`, `language_detector.py`.
  - `tests/` — pytest-based unit/integration tests. See `tests/run_tests.py`.

2. How to run & test (explicit, reproducible)
- Run bot locally (must run as a module because code uses relative imports):
  - `python -m src.main`
- Run tests:
  - `pytest -q` (or `python -m pytest`)
- Environment: prefer a `.env` file or set vars in shell. Required: `TELEGRAM_BOT_TOKEN`, `FLASK_ENV`, `DATABASE_URL` (default: `sqlite:///bot_data.db`).

3. Important project-specific conventions and pitfalls
- Always run the app as a module (`python -m src.main`) — running `python src/main.py` will cause ImportError due to package relative imports.
- Database:
  - `src/models/database.py` uses SQLAlchemy and defaults to SQLite for dev. Production expects `DATABASE_URL` (Postgres) and the manager includes schema-fix logic for `BIGINT` chat/user IDs.
  - Use `DatabaseManager.get_session()` (context-managed usage) and prefer `with db.get_session() as session:` patterns already in the code.
- Bot instance: `src/controllers/bot_controller.py` creates a module-level `TelegramBot` instance that is shared across request handlers.
- Voice transcription:
  - `src/models/voice_transcriber.py` orchestrates multiple services (Whisper, AssemblyAI, Google). Service availability depends on env vars: `ASSEMBLYAI_API_KEY` and a Google credentials variable.
  - Important: the code looks for `GOOGLE_APPLICATION_CREDENTIALS_JSON` (a JSON string) rather than a file path. Prefer setting the JSON string if using Google Speech. README mentions a file path variant; follow code.
- Translation and detection:
  - `FreeTranslator` uses `googletrans` with heuristics (script detection, romanization handling). Maintain its fallback heuristics when changing detection/translation logic.

4. Integration points and external deps to be careful with
- Network calls: Telegram API (`api.telegram.org`), AssemblyAI, Google Speech, and `googletrans` network calls. Mock these in tests (see `tests/mock_googletrans.py`).
- Rate-limiting: `VoiceTranscriber` enforces per-service minimum intervals. Avoid introducing hot loops that bypass `self._respect_rate_limit()`.

5. Testing & debugging notes
- Tests use `pytest` with fixtures in `tests/conftest.py`; inspect test fixtures before changing DB APIs.
- For local debugging, use SQLite (default) to avoid Postgres schema reconstructions.
- To reproduce webhook flows in tests, inspect `tests/test_telegram_bot.py` and `tests/test_bot_controller.py` for example `update` payloads.

6. Style and code conventions (derived from repo rules)
- Python style: snake_case, type hints where present, early-return guard clauses, small focused functions.
- Prefer reusing existing helpers: database manager methods, `telegram_bot.send_message`, and `send_keyboard` — these encapsulate Telegram payload shapes.

7. What agents should do when modifying code
- Preserve external behavior unless the change is explicitly a breaking change and documented.
- Add or update unit tests for new logic; use `tests/` patterns and mocks already present.
- When changing environment usage (e.g., switching from JSON env to a file path), update README and add safe migration code that supports both variables.

8. Quick file references (examples)
- Flask entry: `src/main.py`
- Controllers / webhook: `src/controllers/bot_controller.py`
- Bot logic: `src/models/telegram_bot.py`
- DB manager & models: `src/models/database.py`
- Voice transcription orchestration: `src/models/voice_transcriber.py`
- Translator heuristics: `src/models/free_translator.py`
- Tests: `tests/` (look at `tests/mock_googletrans.py` for mocking example)

If anything here is unclear or you'd like more examples (e.g., request payloads, a focused guideline for tests or mocking network calls), tell me which part to expand.
