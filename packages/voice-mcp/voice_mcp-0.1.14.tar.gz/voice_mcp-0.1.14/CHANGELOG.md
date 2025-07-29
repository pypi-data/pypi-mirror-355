# Changelog

All notable changes to voice-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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