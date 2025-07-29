# Troubleshooting Guide for django-graphene-social-auth

This guide helps you diagnose and fix common issues with the django-graphene-social-auth package.

## Quick Diagnostic Checklist

Run through this checklist to identify common issues:

### 1. Basic Setup Issues

```python
# In Django shell (python manage.py shell)

# Check if social_django is installed and configured
try:
    import social_django
    print("✓ social_django is installed")
except ImportError:
    print("✗ social_django not installed - run: pip install social-auth-app-django")

# Check if graphene_django is installed
try:
    import graphene_django
    print("✓ graphene_django is installed")
except ImportError:
    print("✗ graphene_django not installed - run: pip install graphene-django")

# Check if our package is installed
try:
    import graphql_social_auth
    print("✓ django-graphene-social-auth is installed")
except ImportError:
    print("✗ django-graphene-social-auth not installed - run: pip install django-graphene-social-auth")
```

### 2. Django Settings Check

```python
# Check Django settings
from django.conf import settings

# Check INSTALLED_APPS
required_apps = ['social_django', 'graphene_django']
installed_apps = settings.INSTALLED_APPS
missing_apps = [app for app in required_apps if app not in installed_apps]
if missing_apps:
    print(f"✗ Missing apps in INSTALLED_APPS: {missing_apps}")
else:
    print("✓ Required apps are in INSTALLED_APPS")

# Check AUTHENTICATION_BACKENDS
auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
if not auth_backends:
    print("✗ No AUTHENTICATION_BACKENDS configured")
elif 'django.contrib.auth.backends.ModelBackend' not in auth_backends:
    print("✗ ModelBackend missing from AUTHENTICATION_BACKENDS")
else:
    print("✓ AUTHENTICATION_BACKENDS configured")
    social_backends = [b for b in auth_backends if 'social_core.backends' in b]
    print(f"Social backends found: {social_backends}")
```

### 3. Database Check

```python
# Check if migrations are applied
from django.db import connection

cursor = connection.cursor()
try:
    cursor.execute("SELECT COUNT(*) FROM social_auth_usersocialauth")
    print("✓ Social auth tables exist")
except:
    print("✗ Social auth tables missing - run: python manage.py migrate")
```

## Common Error Messages and Solutions

### Error: "Provider not found"

**Symptoms:**
- GraphQL mutation returns "Provider not found" error
- Backend name appears correct

**Causes & Solutions:**

1. **Backend not in AUTHENTICATION_BACKENDS:**
   ```python
   # Add to settings.py
   AUTHENTICATION_BACKENDS = [
       'social_core.backends.google.GoogleOAuth2',  # Add this
       'django.contrib.auth.backends.ModelBackend',
   ]
   ```

2. **Wrong provider name:**
   ```python
   # Correct provider names:
   # 'google-oauth2' (not 'google')
   # 'facebook' 
   # 'github'
   # 'twitter'
   # 'linkedin-oauth2'
   ```

3. **Missing social auth keys:**
   ```python
   # Add to settings.py
   SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'your-google-client-id'
   SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'your-google-client-secret'
   ```

### Error: "Invalid token"

**Symptoms:**
- Valid-looking token rejected
- Works in other applications

**Causes & Solutions:**

1. **Expired token:**
   - Tokens have limited lifetime (usually 1 hour)
   - Implement token refresh on frontend
   - Check token expiry before sending

2. **Wrong token format:**
   ```javascript
   // For Google, use access_token, not id_token
   const response = await fetch('https://accounts.google.com/o/oauth2/token', {
     method: 'POST',
     headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
     body: new URLSearchParams({
       client_id: 'your-client-id',
       client_secret: 'your-client-secret',
       refresh_token: 'your-refresh-token',
       grant_type: 'refresh_token'
     })
   });
   const data = await response.json();
   // Use data.access_token
   ```

3. **Token for wrong application:**
   - Ensure token was issued for your registered app
   - Check client ID matches your settings

### Error: "CORS blocked"

**Symptoms:**
- Request blocked by browser
- Works in Postman but not browser

**Solutions:**

1. **Install and configure django-cors-headers:**
   ```bash
   pip install django-cors-headers
   ```

   ```python
   # settings.py
   INSTALLED_APPS = [
       'corsheaders',
       # ... other apps
   ]

   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       'django.middleware.common.CommonMiddleware',
       # ... other middleware
   ]

   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",  # React dev server
       "https://yourdomain.com",  # Production
   ]
   
   CORS_ALLOW_CREDENTIALS = True
   ```

### Error: "User creation failed"

**Symptoms:**
- Authentication succeeds but user not created
- Missing user data

**Solutions:**

1. **Check pipeline configuration:**
   ```python
   # settings.py
   SOCIAL_AUTH_PIPELINE = (
       'social_core.pipeline.social_auth.social_details',
       'social_core.pipeline.social_auth.social_uid',
       'social_core.pipeline.social_auth.auth_allowed',
       'social_core.pipeline.social_auth.social_user',
       'social_core.pipeline.user.get_username',
       'social_core.pipeline.user.create_user',  # This creates the user
       'social_core.pipeline.social_auth.associate_user',
       'social_core.pipeline.social_auth.load_extra_data',
       'social_core.pipeline.user.user_details',
   )
   ```

2. **Check user creation settings:**
   ```python
   # settings.py
   SOCIAL_AUTH_CREATE_USERS = True
   SOCIAL_AUTH_USER_MODEL = 'auth.User'  # or your custom user model
   ```

### Error: "Rate limit exceeded"

**Symptoms:**
- Requests blocked after several attempts
- Error occurs for specific IP/provider combination

**Solutions:**

1. **Disable rate limiting for development:**
   ```python
   # settings.py
   SOCIAL_AUTH_RATE_LIMIT_ENABLED = False
   ```

2. **Adjust rate limits:**
   ```python
   # settings.py
   SOCIAL_AUTH_RATE_LIMIT_ATTEMPTS = 20  # Increase limit
   SOCIAL_AUTH_RATE_LIMIT_WINDOW = 60    # Time window in seconds
   ```

## Debugging Tools

### 1. Enable Debug Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'graphql_social_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'social_core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 2. Test Authentication Flow

```python
# Create a test script (test_auth.py)
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from social_django.utils import load_strategy, load_backend
from django.test import RequestFactory

# Create a mock request
factory = RequestFactory()
request = factory.get('/')
request.session = {}

# Load strategy and backend
strategy = load_strategy(request)
backend = load_backend(strategy, 'google-oauth2', redirect_uri=None)

print(f"Backend loaded: {backend}")
print(f"Backend name: {backend.name}")

# Test with a real token (replace with actual token)
# user = backend.do_auth('your-actual-access-token')
# print(f"Authentication result: {user}")
```

### 3. GraphQL Query Testing

```graphql
# Test the mutation in GraphiQL
mutation TestSocialAuth {
  socialAuth(provider: "google-oauth2", accessToken: "your-token") {
    success
    errors
    social {
      uid
      provider
      extraData
    }
    user {
      id
      username
      email
    }
  }
}
```

### 4. Check Provider Configuration

```python
# In Django shell
from django.conf import settings

# Check Google OAuth2 configuration
print("Google OAuth2 Key:", getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', 'Not set'))
print("Google OAuth2 Secret:", 'Set' if getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None) else 'Not set')

# List all social auth settings
social_settings = {k: v for k, v in vars(settings).items() if k.startswith('SOCIAL_AUTH_')}
for key, value in social_settings.items():
    if 'SECRET' in key or 'KEY' in key:
        print(f"{key}: {'Set' if value else 'Not set'}")
    else:
        print(f"{key}: {value}")
```

## Production Deployment Checklist

### Security
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS in production
- [ ] Configure proper CORS origins
- [ ] Set `DEBUG = False`
- [ ] Use secure session cookies

### Performance
- [ ] Enable database connection pooling
- [ ] Configure Redis for caching (optional)
- [ ] Set up proper logging
- [ ] Monitor error rates

### Monitoring
- [ ] Set up application monitoring (e.g., Sentry)
- [ ] Monitor authentication success/failure rates
- [ ] Track API response times
- [ ] Set up alerts for high error rates

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - Enable debug logging and review the output
2. **Search GitHub issues** - https://github.com/Ademic2022/django-graphene-social-auth/issues
3. **Create a minimal reproduction** - Share the simplest possible setup that reproduces the issue
4. **Include relevant information**:
   - Python version
   - Django version
   - Package versions
   - Full error traceback
   - Relevant settings (redact secrets)

## Common Integration Examples

### React Frontend Example

```javascript
// React component for Google authentication
import { gql, useMutation } from '@apollo/client';

const SOCIAL_AUTH_MUTATION = gql`
  mutation SocialAuth($provider: String!, $accessToken: String!) {
    socialAuth(provider: $provider, accessToken: $accessToken) {
      success
      errors
      social {
        uid
      }
      user {
        id
        username
        email
      }
    }
  }
`;

function GoogleLogin() {
  const [socialAuth] = useMutation(SOCIAL_AUTH_MUTATION);

  const handleGoogleSuccess = async (googleResponse) => {
    try {
      const result = await socialAuth({
        variables: {
          provider: 'google-oauth2',
          accessToken: googleResponse.access_token
        }
      });
      
      if (result.data.socialAuth.success) {
        // Handle successful authentication
        console.log('User:', result.data.socialAuth.user);
      } else {
        // Handle errors
        console.error('Auth errors:', result.data.socialAuth.errors);
      }
    } catch (error) {
      console.error('Network error:', error);
    }
  };

  // Use Google Sign-In library...
}
```
