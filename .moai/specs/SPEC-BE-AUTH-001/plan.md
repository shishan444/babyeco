# SPEC-BE-AUTH-001: Authentication & Account API

## Overview

Implement the authentication and account management API for both parent and child applications.

**Business Context**: This API handles all authentication flows including parent registration/login, child device binding via invite codes, and session management for both user types.

**Target Users**:
- Primary: Frontend applications (Parent & Child)
- Secondary: Internal services requiring auth validation

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- Redis for session caching
- JWT tokens

### Dependencies
- None (Foundation module)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall validate all authentication tokens on protected endpoints.

```
Given a request to a protected endpoint
When the request is received
Then the Authorization header is validated
And the token is verified for integrity and expiration
And the user context is attached to the request
```

**UR-002**: The system shall use secure password hashing (bcrypt).

```
Given a password is stored or compared
When authentication occurs
Then bcrypt with appropriate cost factor is used
And plain-text passwords are never logged
```

**UR-003**: The system shall enforce unique email addresses per parent account.

```
Given a parent registration request
When the email already exists
Then registration is rejected with appropriate error
And the existing account is not revealed
```

### Event-Driven Requirements

**EDR-001**: When a parent registers, the system shall create a family and parent profile.

```
Given a valid registration request
When processed successfully
Then a new family record is created
And a parent profile is created and linked
And an invite code is generated for the family
And a session token is returned
```

**EDR-002**: When a parent logs in, the system shall validate credentials and return tokens.

```
Given valid login credentials
When authentication succeeds
Then an access token (short-lived) is generated
And a refresh token (long-lived) is generated
And both tokens are returned
```

**EDR-003**: When a refresh token is used, the system shall issue new tokens.

```
Given a valid refresh token
When a refresh request is made
Then a new access token is generated
And optionally a new refresh token is generated
And old tokens may be invalidated
```

**EDR-004**: When a child binds via invite code, the system shall link device to profile.

```
Given a valid unused invite code
When a bind request is received
Then the child's device is registered
And the invite code is marked as used
And a child session token is generated
```

**EDR-005**: When a parent requests password reset, the system shall send reset email.

```
Given an email exists in the system
When password reset is requested
Then a reset token is generated
And a reset email is sent
And the token has limited validity (e.g., 1 hour)
```

**EDR-006**: When a parent resets password, the system shall update the password.

```
Given a valid reset token
When a new password is submitted
Then the password is hashed and stored
And the reset token is invalidated
And all existing sessions may be invalidated
```

### State-Driven Requirements

**SDR-001**: While a session is active, the system shall allow access to protected resources.

```
Given a valid session token
When a protected resource is requested
Then access is granted based on user permissions
And rate limiting may apply
```

**SDR-002**: While an invite code is unused, it shall remain valid.

```
Given an invite code is generated
When it has not been used
Then it remains available for binding
And it may have an expiration date
```

**SDR-003**: While a token is expired, the system shall reject requests.

```
Given an expired token
When a request is made
Then the request is rejected with 401
And a clear error message indicates expiration
```

### Optional Requirements

**OR-001**: The system MAY support OAuth providers (Google, Apple).

```
Given an OAuth callback
When received
Then the user is authenticated via provider
And a local account is created or linked
And standard tokens are returned
```

**OR-002**: The system MAY support multi-device sessions per user.

```
Given a user logs in from multiple devices
When sessions are created
Then each device has a separate session
And sessions can be managed independently
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow SQL injection in authentication queries.

```
Given any input in auth fields
When processed
Then parameterized queries are used
And no SQL injection is possible
```

**UBR-002**: The system shall NOT expose internal errors in authentication responses.

```
Given an authentication error
When a response is sent
Then only user-friendly error messages are included
And no stack traces or internal details are revealed
```

---

## Technical Solution

### API Endpoints

```yaml
# Parent Authentication
POST /api/v1/auth/register
  Request: { email, password, name, family_name }
  Response: { user, family, access_token, refresh_token }

POST /api/v1/auth/login
  Request: { email, password }
  Response: { user, family, access_token, refresh_token }

POST /api/v1/auth/logout
  Headers: Authorization: Bearer {token}
  Response: { success: true }

POST /api/v1/auth/refresh
  Request: { refresh_token }
  Response: { access_token, refresh_token? }

POST /api/v1/auth/forgot-password
  Request: { email }
  Response: { success: true }

POST /api/v1/auth/reset-password
  Request: { token, new_password }
  Response: { success: true }

GET /api/v1/auth/profile
  Headers: Authorization: Bearer {token}
  Response: { user, family }

# Child Authentication
POST /api/v1/child/bind
  Request: { code, device_id, device_name? }
  Response: { child, access_token, refresh_token }

POST /api/v1/child/refresh
  Request: { refresh_token }
  Response: { access_token }

# Invite Code Management (Parent only)
POST /api/v1/family/invite-codes
  Headers: Authorization: Bearer {token}
  Request: { child_id }
  Response: { code, expires_at }

GET /api/v1/family/invite-codes
  Headers: Authorization: Bearer {token}
  Response: [{ code, child_id, used, used_at, expires_at }]
```

### Data Models

```python
# models/auth.py
class Family(Base):
    __tablename__ = "families"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_login_at: Mapped[datetime | None]

class Child(Base):
    __tablename__ = "children"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    name: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[date]
    avatar_url: Mapped[str | None]
    points: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    used: Mapped[bool] = mapped_column(default=False)
    used_at: Mapped[datetime | None]
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class DeviceBinding(Base):
    __tablename__ = "device_bindings"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    device_id: Mapped[str] = mapped_column(String(255), index=True)
    device_name: Mapped[str | None]
    bound_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_active_at: Mapped[datetime]
    is_active: Mapped[bool] = mapped_column(default=True)
```

### Token Structure

```python
# JWT Token Payload
class TokenPayload(BaseModel):
    sub: str  # User ID
    type: Literal["parent", "child"]
    family_id: str
    permissions: list[str]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation

# Access Token: 15 minutes
# Refresh Token: 7 days
# Reset Token: 1 hour
```

### Security Implementation

```python
# security.py
from passlib.context import CryptContext
from jose import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def generate_invite_code() -> str:
    # 6-character alphanumeric, easy to type
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No confusing chars
    return ''.join(secrets.choice(chars) for _ in range(6))
```

### Rate Limiting

```python
# Rate limits by endpoint
RATE_LIMITS = {
    "login": "5/minute",
    "register": "3/hour",
    "forgot_password": "3/hour",
    "reset_password": "5/hour",
    "child_bind": "10/hour",
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| PostgreSQL | Database | Required | Primary data store |
| Redis | Cache | Required | Session/token caching |
| SMTP Service | Service | Required | Email sending |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Credential stuffing | High | Medium | Rate limiting, 2FA (future) |
| Session hijacking | High | Low | HttpOnly cookies, secure flags |
| Token theft | High | Low | Short expiry, refresh rotation |
| Invite code sharing | Medium | Medium | Single-use, expiration |

---

## Acceptance Criteria

### Parent Authentication
- [ ] Given valid registration, when processed, then family and parent created
- [ ] Given valid login, when processed, then tokens returned
- [ ] Given invalid credentials, when login attempted, then rejected with error
- [ ] Given refresh token, when used, then new tokens issued

### Child Authentication
- [ ] Given valid invite code, when binding, then device linked
- [ ] Given used code, when binding attempted, then rejected
- [ ] Given expired code, when binding attempted, then rejected

### Password Management
- [ ] Given email exists, when reset requested, then email sent
- [ ] Given valid reset token, when password reset, then updated
- [ ] Given expired reset token, when reset attempted, then rejected

### Security
- [ ] All endpoints require proper authentication
- [ ] Rate limiting enforced on auth endpoints
- [ ] Passwords never returned in responses

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-AUTH-001 | Upstream | Parent auth frontend |
| SPEC-FE-AUTH-002 | Upstream | Child auth frontend |
| SPEC-BE-TASK-001 | Downstream | Requires auth context |
| All BE SPECs | Downstream | Require auth validation |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
