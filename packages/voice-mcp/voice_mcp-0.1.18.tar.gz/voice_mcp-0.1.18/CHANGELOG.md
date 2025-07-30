# Changelog

All notable changes to voice-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.18] - 2025-06-15

## [0.1.17] - 2025-06-15

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

## [0.1.14] - 2025-06-14

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

### Fixed
- Audio playback dimension mismatch when adding silence buffer
- MCP server connection persistence (was disconnecting after each request)
- Event loop cleanup errors on shutdown
- Wrapper script path resolution for symlinked execution

### Removed
- Unused python-dotenv dependency
- Temporary test files (test_audio.py, test_minimal_mcp.py)
- Redundant test dependencies in pyproject.toml

## [0.1.12] - 2025-06-14

### Added
- Kokoro TTS support with configuration examples
- Export examples in .env.example for various setups

### Changed
- Simplified project structure with top-level package

## [0.1.11] - Previous

### Added
- Initial voice-mcp implementation
- OpenAI-compatible STT/TTS support
- LiveKit integration
- MCP tool interface
