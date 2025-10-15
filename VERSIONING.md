# Versioning System - My Chauffe Web Application

## Overview
Starting with version 1.0.0, My Chauffe Web Application follows a **Major Version Compatibility System** with CloudManager.py to ensure stable API integration.

## Version Format
We use [Semantic Versioning](https://semver.org/) format: `MAJOR.MINOR.PATCH`

- **MAJOR**: API breaking changes or major feature changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Major Version Compatibility Rule

> **Applications with the same MAJOR version number are guaranteed to be compatible**

### Compatibility Matrix
| My Chauffe | CloudManager.py | Compatible |
|------------|-----------------|------------|
| v1.x.x     | v1.x.x         | ✅ Yes     |
| v1.x.x     | v2.x.x         | ❌ No      |
| v2.x.x     | v2.x.x         | ✅ Yes     |

## Breaking Change Policy

When **either** application introduces a breaking change:
1. **BOTH** applications must increment their major version
2. Update compatibility documentation
3. Coordinate release timing
4. Provide migration guides

### What Constitutes a Breaking Change?

#### My Chauffe Web App:
- Changes to expected CloudManager API endpoints
- Changes to required data formats (DLOID, UUID, etc.)
- Changes to authentication/authorization requirements
- Removal of supported CloudManager API features

#### CloudManager.py:
- Changes to API endpoint URLs or methods
- Changes to response data formats
- Changes to required request parameters
- Removal of API endpoints used by My Chauffe

## Current Version: v1.0.0

### Release Notes
- **Major Release:** Established versioning compatibility system
- **Features:** Purchase success page, async profile loading
- **Compatibility:** Requires CloudManager.py v1.x.x
- **API:** Full CloudManager.py integration

### Next Planned Releases
- **v1.1.0**: Additional user features (backward compatible)
- **v1.2.0**: Enhanced UI/UX improvements (backward compatible)
- **v2.0.0**: Future major architecture changes (breaking)

## Version Checking

### In Code
```python
from mychauffe import __version__
print(f"My Chauffe Version: {__version__}")
```

### Via Git
```bash
git describe --tags
cat VERSION
```

### Runtime Check
The application includes version information in:
- HTTP User-Agent headers to CloudManager
- Admin interface
- API responses (future feature)

## Deployment Guidelines

### Production Deployments
1. Verify CloudManager.py major version compatibility
2. Run integration tests before deployment
3. Update version documentation
4. Tag release in git

### Development
- Use semantic versioning for all releases
- Update VERSION file with each release
- Maintain CHANGELOG.md (future)
- Test with corresponding CloudManager.py version

---

**Current Version:** 1.0.0  
**Last Updated:** October 15, 2025  
**Next Review:** January 2026