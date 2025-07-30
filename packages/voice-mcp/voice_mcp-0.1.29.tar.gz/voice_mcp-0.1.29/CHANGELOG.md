# Changelog

All notable changes to voice-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.29] - 2025-06-17

## [0.1.28] - 2025-06-17

### Added
- MCP prompts for Kokoro TTS management:
  - `kokoro-start` - Start the local Kokoro TTS service
  - `kokoro-stop` - Stop the local Kokoro TTS service
  - `kokoro-status` - Check the status of Kokoro service
  - `voice-status` - Check comprehensive status of all voice services
- Instructions in CLAUDE.md for AI assistants on when to use Kokoro tools

## [0.1.27] - 2025-06-17

### Added
- Voice chat prompt/command (`/voice-mcp:converse`) for interactive voice conversations
- Automatic local provider preference with VOICE_MCP_PREFER_LOCAL environment variable
- Documentation improvements with better organization and cross-linking

### Changed
- Renamed voice_chat prompt to converse for clarity
- Simplified voice_chat prompt to take no arguments


## [0.1.26] - 2025-06-17

### Fixed
- Added missing voice_mode() function to cli.py for voice-mode command

## [0.1.25] - 2025-06-17

### Added
- Build tooling improvements for dual package maintenance

### Fixed
- Missing psutil dependency in voice-mode package

## [0.1.24] - 2025-06-17

### Fixed
- Improved signal handling for proper Ctrl-C shutdown
  - First Ctrl-C attempts graceful shutdown
  - Second Ctrl-C forces immediate exit

## [0.1.23] - 2025-06-17

### Added
- Provider registry system MVP for managing TTS/STT providers
  - Dynamic provider discovery and registration
  - Automatic availability checking
  - Feature-based provider filtering
- Dual package name support (voice-mcp and voice-mode)
  - Both commands now available in voice-mode package
  - Maintains backward compatibility
- Service management tools for Kokoro TTS:
  - `start_kokoro` - Start the Kokoro TTS service using uvx
  - `stop_kokoro` - Stop the running Kokoro service
  - `kokoro_status` - Check service status with CPU/memory usage
- Automatic cleanup of services on server shutdown
- psutil dependency for process monitoring
- `list_tts_voices` tool to list all available TTS voices by provider
  - Shows OpenAI standard and enhanced voices with characteristics
  - Lists Kokoro voices with descriptions
  - Includes usage examples and emotional speech guidance
  - Checks API/service availability for each provider

### Changed
- Default TTS voices updated: alloy for OpenAI, af_sky for Kokoro

## [0.1.22] - 2025-06-16

### Added
- Local STT/TTS configuration support in .mcp.json
- Split TTS metrics into generation and playback components for better performance insights
  - Tracks TTS generation time (API call) separately from playback time
  - Displays metrics as tts_gen, tts_play, and tts_total

### Changed
- Modified text_to_speech() to return (success, metrics) tuple
- Updated all tests to handle new TTS return format

## [0.1.21] - 2025-06-16

### Added
- VOICE_MCP_SAVE_AUDIO environment variable to save all TTS/STT audio files
- Audio files saved to ~/voice-mcp_audio/ with timestamps
- Improved voice selection documentation and guidance

### Changed
- Voice parameter changed from Literal to str for flexibility in voice selection


## [0.1.19] - 2025-06-15

### Added
- TTS provider selection parameter to converse function ("openai" or "kokoro")
- Auto-detection of TTS provider based on voice selection
- Support for multiple TTS endpoints with provider-specific clients

## [0.1.18] - 2025-06-15

### Changed
- Removed mcp-neovim-server from .mcp.json configuration

## [0.1.17] - 2025-06-15

### Changed
- Minor version bump (no functional changes)

## [0.1.16] - 2025-06-15

## [0.1.16] - 2025-06-15

### Added
- Voice parameter to converse function for dynamic TTS voice selection
- Support for Kokoro voices: af_sky, af_sarah, am_adam, af_nicole, am_michael
- Python 3.13 support with conditional audioop-lts dependency

### Fixed
- BrokenResourceError when concurrent voice operations interfere with MCP stdio communication
- Enhanced sounddevice stderr redirection workaround to prevent stdio corruption
- Added concurrency lock to serialize audio operations and prevent race conditions
- Protected stdio file descriptors during audio recording and playback operations
- Added anyio.BrokenResourceError to exception handling for MCP disconnections
- Configure pytest to exclude manual test scripts from CI builds

## [0.1.15] - 2025-06-14

### Fixed
- Removed load_dotenv call that was causing import error

## [0.1.14] - 2025-06-14

### Fixed
- Updated GitHub workflows for new project structure

## [0.1.13] - 2025-06-14

### Added
- Performance timing in voice responses showing TTS, recording, and STT durations
- Local STT/TTS documentation for Whisper.cpp and Kokoro
- CONTRIBUTING.md with development setup instructions
- CHANGELOG.md for tracking changes

### Changed
- Refactored from python-package subdirectory to top-level Python package
- Moved MCP server symlinks from mcp-servers/ to bin/ directory
- Updated wrapper script to properly resolve symlinks for venv detection
- Improved signal handlers to prevent premature exit
- Configure build to only include essential files in package

### Fixed
- Audio playback dimension mismatch when adding silence buffer
- MCP server connection persistence (was disconnecting after each request)
- Event loop cleanup errors on shutdown
- Wrapper script path resolution for symlinked execution
- Critical syntax errors in voice-mcp script

### Removed
- Unused python-dotenv dependency
- Temporary test files (test_audio.py, test_minimal_mcp.py)
- Redundant test dependencies in pyproject.toml
- All container/Docker support

## [0.1.12] - 2025-06-14

### Added
- Kokoro TTS support with configuration examples
- Export examples in .env.example for various setups
- Centralized version management and automatic PyPI publishing

### Changed
- Simplified project structure with top-level package

## [0.1.11] - 2025-06-13

### Added
- Initial voice-mcp implementation
- OpenAI-compatible STT/TTS support
- LiveKit integration for room-based voice communication
- MCP tool interface with converse, listen_for_speech, check_room_status, and check_audio_devices
- Debug mode with audio recording capabilities
- Support for multiple transport methods (local microphone and LiveKit)

## [0.1.0 - 0.1.10] - 2025-06-13

### Added
- Initial development and iteration of voice-mcp
- Basic MCP server structure
- OpenAI API integration for STT/TTS
- Audio recording and playback functionality
- Configuration via environment variables
