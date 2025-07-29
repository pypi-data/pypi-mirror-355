Changelog
=========

1.1.0 (2025-06-13)
------------------

**Major Improvements:**

* **Enhanced Error Handling:** Completely rewritten error handling system with specific exception types
* **Better Logging:** Added comprehensive logging throughout the authentication flow
* **Input Validation:** Added validation for provider names and access tokens
* **Rate Limiting:** Added optional rate limiting to prevent abuse
* **Production Ready:** Improved error messages and debugging capabilities

**New Features:**

* Added ``ProviderNotFoundError``, ``UserCreationError``, and ``RateLimitError`` exceptions
* Enhanced mutations now return ``success`` and ``errors`` fields for better error handling
* Added support for refresh tokens in JWT authentication
* Improved GraphQL field descriptions and documentation
* Added comprehensive production setup guide and troubleshooting documentation

**Bug Fixes:**

* Fixed issue where authentication errors weren't properly caught
* Improved handling of edge cases in token validation
* Better error messages for missing JWT dependencies

**Documentation:**

* Added ``PRODUCTION_GUIDE.md`` with complete setup instructions
* Added ``example_settings.py`` with comprehensive Django configuration
* Updated README with better installation and usage examples

**Breaking Changes:**

* Mutations now return additional fields (``success``, ``errors``) - this might affect existing GraphQL queries
* Some exception types have been renamed for clarity

1.1.0 (2025-06-12)
------------------

* Fixed README.rst rendering issues on PyPI
* Updated package name to django-graphene-social-auth
* Minor documentation improvements
* Initial release of maintained fork
* Updated maintainer information
* Compatible with modern Django and Python versions

0.2.0
-----

* **BREAKING CHANGES**: Removed Python 3.4-3.7 support
* **BREAKING CHANGES**: Removed Django 1.11-2.2 support  
* **BREAKING CHANGES**: Removed promise library dependency
* Added Python 3.8-3.13 support
* Added Django 3.2-5.1 support
* Updated graphene-django to >=3.0.0
* Updated social-auth-app-django to >=5.0.0
* Updated django-graphql-jwt to >=0.4.0
* Replaced promise library with native async/await support
* Added modern packaging with pyproject.toml
* Updated testing infrastructure (pytest >=7.0, coverage >=7.0)
* Added GitHub Actions CI/CD pipeline
* Updated code formatting tools (black, isort)
* Improved error handling and type hints compatibility

0.1.4
-----

* Updated locales

0.1.3
-----

* Replaced django login with social _do_login
* Added authenticated user to backend.do_auth

0.1.2
-----

* Added DoAuthError exception

0.1.1
-----

* Removed login() usage for JSON Web Token


0.1.0
-----

* Renamed do_auth() to resolve()


0.0.3
-----

* Locale up to date


0.0.2
-----

* SocialAuthMutation abstract class


0.0.1
-----

* xin chào!
