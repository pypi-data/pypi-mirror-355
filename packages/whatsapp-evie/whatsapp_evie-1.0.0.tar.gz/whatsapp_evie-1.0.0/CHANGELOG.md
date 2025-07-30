# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Enhanced error handling with custom exceptions
- Retry logic for failed API calls
- Rate limiting support
- Structured logging
- Configuration management
- CLI interface
- Comprehensive documentation
- Multiple practical examples
- Type hints throughout codebase
- Context manager support for client
- Plugin system for extensibility
- Message validation and sanitization
- Webhook verification
- Health check endpoints
- **PyArmor code obfuscation support** for commercial distributions
- Obfuscation build scripts and configuration
- Protected package creation with runtime security

### Changed
- Improved setup.py with modern packaging standards
- Enhanced README with detailed documentation
- Better error messages and debugging information
- Async context manager support for proper resource cleanup

### Fixed
- Memory leaks in long-running webhook servers
- Race conditions in message handling
- Proper session cleanup

## [0.1.0] - 2025-01-15

### Added
- Initial release
- Basic WhatsApp-Evie integration
- Support for text, image, audio, video, and document messages
- Webhook server for receiving messages
- Message handler registration system
- Asynchronous message processing
- Environment-based configuration
- Type-safe message models using Pydantic
- MIT License
