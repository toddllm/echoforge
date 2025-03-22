# EchoForge Development Notes

This document contains essential information about developing and testing the EchoForge application. Update this document as you discover new information to avoid repeating the same issues.

## Server Management

| Action | Command | Notes |
|--------|---------|-------|
| Start server | `./run_server.sh` | Waits ~60 seconds for model loading |
| Stop server | `./stop_server.sh` | Properly terminates all processes |

**Important**: The server has hot-reload capability and will automatically detect most file changes.

## Database Management

| Action | Command | Notes |
|--------|---------|-------|
| Run migrations | `python -m alembic upgrade heads` | Use `heads` (plural) to apply all pending migrations |
| Create migration | `python -m alembic revision -m "description"` | Creates a new migration file |

## Architecture Notes

### Session & Authentication

- User sessions are managed through the `SessionMiddleware` in `app/core/session_middleware.py`
- User profile data and theme preferences are stored in the `UserProfile` model with a `theme_preference` column
- Theme preference is submitted via the profile form and properly updated in the database
- Theme preferences are now loaded into the session during the login process in `app/api/auth_routes.py`
- Theme preferences are stored in the session data dictionary under the key `theme_preference`

### Templates & Routing

- Templates are stored in `/home/tdeshane/echoforge/templates/`
- The base template sets up common UI elements and theme handling
- Character showcase page has been converted from static HTML to a Jinja2 template

### Voice Generation

- Voice generation tasks are processed using a worker thread system
- Tasks are queued using `task_manager.enqueue_task` 
- Worker processes using `handle_character_voice_task` in `character_showcase_routes.py`

## Common Issues & Solutions

1. **Theme Inconsistency**
   - Ensure theme preference is consistently named `theme_preference` in all code
   - The theme is set using `data-bs-theme` attribute on the html element
   - LocalStorage uses `theme_preference` key
   - In UI routes, access theme preference using `session.data.get('theme_preference', config.DEFAULT_THEME)`
   - The login process fetches theme preference from user profile and stores it in `session.data['theme_preference']`

2. **Database Migration Issues**
   - If multiple migration heads exist, use `python -m alembic upgrade heads` (plural)
   - Set `down_revision` to `None` if creating a standalone migration

3. **FFmpeg-related Errors**
   - Always use `./run_server.sh` rather than directly invoking Python
   - Script sets up proper environment variables for audio processing

## Development Process

1. **Make small, focused changes**
   - Implement one feature at a time
   - Test each feature before moving on

2. **Test thoroughly**
   - Test both authenticated and non-authenticated paths
   - Verify UI elements appear correctly
   - Check that settings are saved to user profiles

3. **Commit frequently**
   - After each meaningful change is tested and working
   - Include clear commit messages describing the change

## Current Tasks & Status

See the [ux_improvement_plan.md](./ux_improvement_plan.md) for detailed task tracking.
