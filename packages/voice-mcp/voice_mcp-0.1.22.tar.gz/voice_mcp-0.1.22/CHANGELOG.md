# Changelog

All notable changes to voice-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Documentation about gpt-4o-mini-tts being best for emotional speech
- Warning to never use coral voice and default to af_sky for Kokoro

### Changed
- Voice parameter changed from Literal to str for flexibility in voice selection

## [0.1.20] - 2025-06-15

### Changed
- Voice parameter changed from Literal to str type for more flexibility

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
