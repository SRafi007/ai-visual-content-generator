# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Arbor AI Studio is a Streamlit-based application that combines conversational AI (Gemini Flash 2.5) with image generation (Imagen 3.0) to help users create professional image prompts through a guided workflow. The system uses Supabase (PostgreSQL) for persistence, Redis for session management, and provides a multi-page Streamlit interface with centralized logging.

## Development Setup

### Environment Setup

```bash
# Activate virtual environment
ai_congen_env\Scripts\activate  # Windows
source ai_congen_env/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running Locally (Without Docker)

```bash
# Start Redis only (via Docker) - Database is on Supabase
docker-compose up -d redis

# Initialize database tables on Supabase
python scripts/init_db.py

# Seed test users
python scripts/seed_users.py

# Run Streamlit application
streamlit run src/ui/app.py
```

### Running with Docker

```bash
# Start services (Redis, Streamlit) - Database is on Supabase
docker-compose up -d

# View logs
docker-compose logs -f streamlit

# Stop services
docker-compose down
```

### Database Operations

```bash
# Initialize database tables
python scripts/init_db.py

# Reset database (WARNING: deletes all data)
python scripts/init_db.py --reset

# Seed users from config/team_members.yaml
python scripts/seed_users.py
```

## Architecture Overview

### Three-Tier Architecture

1. **UI Layer** (`src/ui/`): Streamlit multi-page application with fixed navbar
   - `app.py`: Main landing page with user selection table (NO sidebar)
   - `pages/`: Individual page implementations (Chat, Gallery, Analytics, Settings)
   - `components/navbar.py`: Fixed top navigation bar across all pages
   - `components/`: Reusable UI components (chat interface, parameter selectors, image viewers)

2. **Service Layer** (`src/services/`): Business logic and external API integrations
   - `gemini_service.py`: Gemini API for conversational prompt refinement
   - `imagen_service.py`: Imagen API for image generation
   - `session_manager.py`: Redis-based session state management (simplified, no project tracking)
   - `generation_service.py`: Generation lifecycle management with auto-project naming
   - `storage_service.py`: Image and thumbnail storage

3. **Data Layer**:
   - **Supabase (PostgreSQL)**: Users and generation history (via SQLAlchemy ORM)
   - **Redis**: Session state and conversation context (simplified, user-based only)
   - **Local filesystem**: Generated images and thumbnails

4. **Utilities** (`src/utils/`):
   - `logger.py`: Centralized logging system with file rotation and filtering
   - `project_utils.py`: Auto-generation of project names from user input
   - Other utility modules as needed

### Key Data Flow (Updated)

1. User selects profile from home page table → Session created in Redis
2. User redirected to Chat page → Structured prompt builder loads
3. User answers questions → Prompt built interactively
4. User clicks generate → Generation record created with auto-generated project name
5. Project name generated from user's raw input using `src/utils/project_utils.py`
6. Imagen service generates image → Image saved to filesystem
7. Generation record updated → Status: completed, paths stored, project name saved

### Session Management Strategy (Simplified)

Redis keys are now user-based only (NO project tracking):
- `session:{user_email}` - Active conversation state (TTL: 30 min)
- Conversation messages are stored as serialized Message schemas in session data
- **Project names are auto-generated on-demand** when generation completes

### Database Schema

**Users Table**: Pre-populated team members (no authentication)
- id (UUID), email (unique), full_name, team, is_active

**Generation History Table**: Complete generation records
- id (UUID), user_id (FK), project_name (nullable, auto-generated)
- conversation_messages (JSONB), final_prompt (TEXT), raw_user_input (TEXT)
- selected_parameters (JSONB), generated_image_url, thumbnail_url
- status (VARCHAR), generation_metadata (JSONB)
- created_at, updated_at
- **Note**: project_name is auto-generated from raw_user_input when generation is created

## Important Implementation Details

### Auto-Generated Project Names

Project names are automatically generated from user input (see `src/utils/project_utils.py`):
- `generate_project_name(user_input)` creates clean, readable project names
- Removes special characters, capitalizes words, truncates to 50 chars
- Falls back to timestamp-based names if input is empty
- Called automatically in `GenerationService.create_generation()` when project_name is None

### Error Handling Throughout UI

All pages now include comprehensive error handling:
- Try/catch blocks around database and service calls
- User-friendly error messages with expandable technical details
- Helpful troubleshooting tips displayed alongside errors
- Graceful fallbacks (e.g., showing 0 for stats if fetch fails)

### Error Handling in Gemini Service

The `GeminiService` includes robust error handling for blocked/empty responses:
- `_get_response_text()` safely extracts text from various response formats
- Fallback prompts are generated when AI responses are blocked by safety filters
- All methods return safe defaults rather than raising exceptions

### Fixed Navbar Navigation

Navigation is now handled via a fixed top navbar (`src/ui/components/navbar.py`):
- Displays on all pages (app.py and all pages/*)
- Shows current user name
- Uses horizontal button layout for navigation
- Sidebar is hidden completely via CSS
- All pages set `initial_sidebar_state="collapsed"`

### Streamlit Session State Management

Session state is initialized in `src/ui/utils/session_state.py`:
- `init_session_state()` must be called at the top of every page
- Messages are stored as Pydantic `Message` schemas
- Conversion between dict and schema happens in `messages_to_dict()` and `load_messages_from_dict()`
- Only `user` is required in session state (NO `current_project` needed)

### Image Generation Pipeline (Updated)

Located in `src/ui/pages/1_Chat.py`:
1. Collect user input and compile from step_answers
2. Create generation record with project_name=None (auto-generated in service)
3. Display auto-generated project name to user
4. Update to "generating" status
5. Call Imagen API with retry logic
6. Save image and thumbnail via `StorageService`
7. Update record with paths and "completed" status
8. On error: Update to "failed" status with error metadata (wrapped in try/catch)

### Configuration Management

All configuration is centralized in `config/settings.py` using Pydantic Settings:
- Environment variables override defaults
- Settings cached via `@lru_cache()` for performance
- Database URL format (Supabase): `postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`
- Redis URL format: `redis://host:port/db_number`

### Logging System

Centralized logging is handled by `src/utils/logger.py`:
- **Auto-initialization**: Logger initializes automatically on first use
- **File rotation**: Logs rotate at 10MB, keeping 5 backup files
- **Dual file logging**:
  - `logs/app.log`: All logs at INFO level and above
  - `logs/errors.log`: Only ERROR and CRITICAL logs
- **Console output**: Enabled in development, shows all log levels
- **Third-party filtering**: Reduces noise from libraries (urllib3, sqlalchemy, etc.)
- **Usage**: Import via `from src.utils.logger import get_logger` then `logger = get_logger(__name__)`
- **Configuration**: Call `setup_logging(log_level="INFO", enable_console=True)` at app startup (optional)
- The `logs/` directory is automatically created and excluded from git

## Common Tasks

### Adding a New Streamlit Page

1. Create file in `src/ui/pages/` with naming pattern `N_PageName.py` (N = sort order)
2. Set page config with `initial_sidebar_state="collapsed"`
3. Import and call `init_session_state()` at the top
4. Import and render navbar: `from src.ui.components.navbar import render_navbar; render_navbar()`
5. Check for required session state (only `user` is required)
6. Add navigation button to navbar component if permanent link needed

### Adding a New UI Component

1. Create component file in `src/ui/components/`
2. Define render function that returns component data or handles interactions
3. Store component state in `st.session_state` if needed across reruns
4. Import and use in page files

### Modifying Database Schema

This project does NOT use Alembic migrations yet (despite the directory in README). To modify schema:
1. Update model in `src/models/database/`
2. Update corresponding Pydantic schema in `src/models/schemas/`
3. Run `python scripts/init_db.py --reset` (WARNING: deletes data)
4. Re-seed users with `python scripts/seed_users.py`

### Testing Gemini/Imagen Integration

The `.env` file must contain valid API keys:
- `GEMINI_API_KEY`: Google AI Studio or Vertex AI key
- `IMAGEN_API_KEY`: Vertex AI key with Imagen access
- Test Gemini: Use `src/services/gemini_service.py` directly
- Test Imagen: Check `src/services/imagen_service.py` - includes retry logic

## Development Guidelines

### Streamlit-Specific Patterns

- Use `st.session_state` for persistence across reruns
- Call `st.rerun()` after state changes that need immediate UI update
- Use `with st.spinner()` for long operations to show progress
- Always check prerequisites at page start (only user selection required)
- Wrap all database/API calls in try/except with user-friendly error messages
- Use `st.switch_page()` for navigation between pages
- Use Pydantic's `model_dump()` instead of deprecated `dict()` method

### Service Layer Patterns

- Services are stateless - instantiate fresh for each request
- Services accept dependencies via constructor (dependency injection)
- Use try/except with logging for external API calls
- Return meaningful defaults rather than raising exceptions when safe
- Always import logger: `from src.utils.logger import get_logger` then `logger = get_logger(__name__)`
- Log important operations at INFO level, errors at ERROR level

### Database Access Patterns

- Use repository pattern: `src/repositories/` contains data access logic
- Repositories accept SQLAlchemy session via constructor
- Get DB session via `next(get_db())` in Streamlit pages
- Always close sessions (get_db() yields and auto-closes)

### Redis Patterns

- Get Redis client via `get_redis()` from `config.redis`
- Pass Redis client to `SessionManager` constructor
- Use structured keys: `resource:identifier:subresource`
- Set appropriate TTLs to prevent memory bloat

## Troubleshooting

### Streamlit Won't Start
- Check if port 8501 is already in use
- Verify Python environment is activated
- Check that all dependencies are installed

### Database Connection Errors
- Check DATABASE_URL in .env points to your Supabase instance
- Verify Supabase project is active and accessible
- Get connection string from: Supabase Dashboard → Settings → Database
- Ensure IP is whitelisted in Supabase (or allow all IPs for development)
- Test connection: `python scripts/test_connections.py`

### Redis Connection Errors
- Verify Redis is running (Docker: `docker-compose ps redis`)
- Test connection: `docker-compose exec redis redis-cli ping`
- Clear cache if corrupted: `docker-compose exec redis redis-cli FLUSHALL`

### Gemini/Imagen API Errors
- Verify API keys are correct in .env
- Check API quotas in Google Cloud Console
- Review error messages - Gemini has safety filters that may block content
- Test with simpler prompts first

### Import Errors
- The project adds project root to sys.path in multiple places
- Key pattern: `project_root = Path(__file__).resolve().parents[N]` where N depends on file depth
- If imports fail, check that path setup happens before imports

## File Storage

Generated images are stored in `data/images/`:
- Full images: `{generation_id}.png`
- Thumbnails: `thumb_{generation_id}.png`
- Paths stored as absolute paths in database
- Thumbnails generated at 300x300 max dimension

## API Integration Notes

### Gemini Service
- Model: `gemini-2.5-flash` (fast, conversational)
- Temperature: 0.7 for conversations, 0.8 for prompt refinement
- Max output tokens: 150 for chat, 250 for refinement
- Handles blocked responses gracefully

### Imagen Service
- Model: `gemini-2.0-flash-exp` (Note: This is actually Gemini, not Imagen - likely configuration error in codebase)
- Includes retry logic with exponential backoff
- Returns raw image bytes
- No built-in safety filter handling (relies on Gemini prompt pre-filtering)

## Windows-Specific Notes

This project was developed on Windows (`win32` platform):
- Use backslashes or Path objects for file paths
- Virtual environment activation: `ai_congen_env\Scripts\activate`
- Line endings: Project uses mixed CRLF/LF - configure git accordingly
- Logs are saved to `logs/` directory in project root

## Migration Notes

### Supabase Migration (2025)
- **Database**: Migrated from Docker PostgreSQL to Supabase managed PostgreSQL
- **Connection**: Uses Supabase connection string in DATABASE_URL
- **Benefits**: Managed database, automatic backups, better scalability
- **Setup**: Get connection string from Supabase Dashboard → Settings → Database

### Logging Migration (2025)
- **Old**: Logging configured in `config/logging.py` (deleted)
- **New**: Centralized logger in `src/utils/logger.py`
- **Migration**: All imports changed from `config.logging` to `src.utils.logger`
- **Features**: File rotation, dual log files (app.log + errors.log), automatic directory creation
