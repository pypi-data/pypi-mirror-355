# Changelog

All notable changes to the Ophelos Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2024-06-14

### Added
- **Multi-tenant support**: Added `tenant_id` parameter to `OphelosClient` constructor
- **Thread-safe authentication**: Implemented thread-safe OAuth2 token management with `threading.RLock()`
- **Concurrent usage examples**: Added comprehensive examples for using the SDK with `ThreadPoolExecutor`
- **Thread safety tests**: Added dedicated test suite for concurrent usage patterns
- **Complete configuration reference**: Enhanced documentation with all client parameters

### Enhanced
- **Authentication**: OAuth2 authenticator now uses thread-safe token caching for concurrent requests
- **HTTP Client**: Automatic `OPHELOS_TENANT_ID` header injection when `tenant_id` is specified
- **Documentation**: Updated README.md and USAGE.md with multi-tenant usage patterns
- **Test coverage**: Added 5 new thread safety tests covering concurrent token access and refresh
- **Error handling**: Improved type safety with proper type casting in authentication flow

### Fixed
- **Code cleanup**: Removed obvious and redundant comments throughout the codebase
- **Type safety**: Fixed mypy type errors in authentication module
- **Code formatting**: Applied black formatting to all Python files for consistency

### Technical
- **Jittered retry**: Enhanced retry logic with additive jitter (0-1.5s) to prevent thundering herd
- **Performance**: Optimized authentication for high-concurrency scenarios
- **Memory efficiency**: Shared authentication tokens across concurrent threads

## [1.0.0] - 2024-01-15

### Added
- Initial release of the Ophelos Python SDK
- Complete API coverage for Ophelos API v20250401
- OAuth2 client credentials authentication
- Type-safe models using Pydantic
- Comprehensive error handling with custom exceptions
- Resource managers for all API endpoints:
  - Debts management (create, update, list, search, lifecycle operations)
  - Customer management (create, update, list, search)
  - Organisation management
  - Payment management (create, list, search)
  - Invoice management
  - Payment plan management
  - Communication management
  - Webhook management
  - Payout management
  - Tenant management
- Webhook signature validation and event parsing
- Built-in pagination support
- Search functionality with query language support
- Automatic token refresh and retry logic
- Expandable response fields support
- Comprehensive documentation and examples
- Type hints and mypy support
- Modern Python packaging with pyproject.toml

### Security
- HMAC-SHA256 webhook signature verification
- Secure credential handling
- Automatic token expiration and refresh

### Documentation
- Complete API reference documentation
- Usage examples and best practices
- Webhook handling examples
- Authentication setup guide

## [Unreleased]

### Changed
- **BREAKING CHANGE**: Package renamed from `ophelos` to `ophelos_sdk` for better namespace management
- Import statements now use `from ophelos_sdk import OphelosClient` instead of `from ophelos import OphelosClient`
- All module imports updated to use `ophelos_sdk.*` namespace

### Planned
- Async client support
- Enhanced error messages with suggestion
- CLI tool for API testing
- Additional utility functions
- Performance optimizations 