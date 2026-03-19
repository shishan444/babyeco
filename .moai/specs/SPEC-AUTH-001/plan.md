# SPEC-AUTH-001: User Authentication and Account System

## Overview

Implement parent account registration/login and child profile management to establish the foundation of BabyEco's account system.

**Business Context**: BabyEco operates a dual-app architecture (Parent App + Child App). The authentication system must support a single parent account managing multiple child profiles, with secure device binding for children via invite codes.

**Target Users**:
- Parents (primary account holders)
- Children 6-12 years old (profiles managed by parents)

---

## Technical Constraints

| Constraint | Requirement |
|-----------|-------------|
| Backend Framework | FastAPI (Python) |
| ORM | SQLAlchemy 2.0 |
| Authentication | JWT Token (Access + Refresh) |
| Password Hashing | bcrypt |
| Token Expiry | Access: 1 hour, Refresh: 7 days |

---

## Functional Requirements

### Ubiquitous Requirements

These requirements apply universally across the system:

1. **Parent-First Registration**: Parents must complete registration before any system usage
2. **Child Profile Dependency**: Child profiles can only be created after parent account exists
3. **Device Binding via Invite**: Children access their profiles through parent-generated invite codes
4. **Single Parent Authority**: MVP supports only one parent account per family (no co-parents)

### Event-Driven Requirements

System behaviors triggered by specific events:

| Trigger | System Behavior |
|---------|----------------|
| Parent submits registration | Create parent account with phone number |
| Parent logs in successfully | Issue access token + refresh token |
| Parent creates child profile | Generate unique 6-character invite code |
| Parent deletes child profile | Invalidate associated invite code |
| Child enters valid invite code | Bind device to corresponding profile |
| Refresh token used | Issue new access token, optionally rotate refresh token |
| User clicks logout | Invalidate tokens server-side |

### State-Driven Requirements

Conditional behaviors based on system state:

| Condition | System Behavior |
|-----------|----------------|
| User not authenticated | Block all business API endpoints, redirect to login |
| Child profile unbound | Display invite code input interface on child app |
| Token expired | Return 401, prompt re-authentication |
| Invalid credentials | Return 401 with rate limiting after 5 failures |
| Device already bound | Prevent binding to another profile |

### Optional Requirements

Deferred to future releases:

- WeChat/Phone quick login (Phase 2)
- Biometric authentication (Phase 2)
- Passwordless login via SMS OTP (Phase 2)
- Multi-parent co-management (Phase 3)

### Unwanted Behavior Requirements

Behaviors explicitly excluded:

| Prohibition | Rationale |
|-------------|-----------|
| Children cannot self-register | Maintain parental control |
| One device cannot bind multiple profiles | Data isolation per child |
| Parents cannot modify child's device binding directly | Security - require re-invite |
| Invite codes are single-use per profile | Prevent unauthorized access |

---

## Technical Solution

### Data Models

```
User (Parent Account)
├── id: UUID (PK)
├── phone: String (unique, indexed)
├── password_hash: String (bcrypt)
├── nickname: String (optional)
├── avatar_url: String (optional)
├── role: Enum ['parent']
├── status: Enum ['active', 'suspended', 'deleted']
├── created_at: DateTime
├── updated_at: DateTime
└── last_login_at: DateTime

ChildProfile
├── id: UUID (PK)
├── parent_id: UUID (FK -> User.id)
├── name: String
├── age: Integer
├── avatar_url: String (optional)
├── invite_code: String (unique, 6 chars, indexed)
├── device_id: String (nullable, unique when set)
├── device_bound_at: DateTime (nullable)
├── status: Enum ['active', 'archived']
├── created_at: DateTime
└── updated_at: DateTime

TokenBlacklist
├── id: UUID (PK)
├── token_jti: String (indexed)
├── user_id: UUID (FK -> User.id)
├── revoked_at: DateTime
└── expires_at: DateTime
```

### API Endpoints

#### Parent Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new parent account |
| POST | `/api/v1/auth/login` | Authenticate and receive tokens |
| POST | `/api/v1/auth/logout` | Invalidate current session |
| POST | `/api/v1/auth/refresh` | Exchange refresh token for new access token |
| GET | `/api/v1/auth/me` | Get current user profile |
| PATCH | `/api/v1/auth/me` | Update user profile |

#### Child Profile Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/children` | Create child profile |
| GET | `/api/v1/children` | List all child profiles |
| GET | `/api/v1/children/{id}` | Get specific child profile |
| PATCH | `/api/v1/children/{id}` | Update child profile |
| DELETE | `/api/v1/children/{id}` | Archive child profile |
| POST | `/api/v1/children/{id}/regenerate-code` | Generate new invite code |

#### Child Device Binding

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/child/bind` | Bind device using invite code |
| GET | `/api/v1/child/me` | Get bound child profile |
| POST | `/api/v1/child/unbind` | Unbind current device |

### Request/Response Schemas

```python
# Registration
class RegisterRequest(BaseModel):
    phone: str  # E.164 format
    password: str  # Min 8 chars, complexity rules
    nickname: Optional[str]

class RegisterResponse(BaseModel):
    user_id: str
    phone: str
    access_token: str
    refresh_token: str
    expires_in: int

# Login
class LoginRequest(BaseModel):
    phone: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int

# Child Profile Creation
class CreateChildRequest(BaseModel):
    name: str
    age: int  # 6-12 range
    avatar_url: Optional[str]

class ChildProfileResponse(BaseModel):
    id: str
    name: str
    age: int
    avatar_url: Optional[str]
    invite_code: str
    device_bound: bool
    created_at: datetime

# Device Binding
class BindDeviceRequest(BaseModel):
    invite_code: str
    device_id: str

class BindDeviceResponse(BaseModel):
    profile_id: str
    name: str
    age: int
    access_token: str
    refresh_token: str
    expires_in: int
```

### Invite Code Generation Rules

```
Format: 6 alphanumeric characters (A-Z, 0-9)
Exclusion: Confusing characters (0/O, 1/I/L)
Generation: Cryptographically secure random
Uniqueness: Database constraint + retry on collision
Validity: Active until profile deleted or code regenerated
```

### Security Measures

1. **Rate Limiting**:
   - Login: 5 attempts per 15 minutes per IP
   - Registration: 3 per hour per IP
   - Bind: 10 attempts per hour per device

2. **Password Requirements**:
   - Minimum 8 characters
   - At least one uppercase, one lowercase, one digit
   - Cannot be phone number or sequential

3. **Token Security**:
   - JWT signed with RS256 (asymmetric)
   - JTI claim for revocation support
   - Short-lived access tokens (1 hour)
   - Refresh token rotation on use

4. **Invite Code Protection**:
   - 6 characters = 36^6 ≈ 2 billion combinations
   - Rate limiting prevents brute force
   - Codes expire when profile is archived

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| Database setup | Required | PostgreSQL or SQLite for MVP |
| FastAPI project structure | Required | Base project scaffolding |
| SQLAlchemy models | Part of this SPEC | Core models defined here |

**No upstream SPEC dependencies** - This is the foundation SPEC.

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Invite code brute force | High | Medium | Rate limiting + monitoring alerts |
| Device ID spoofing | Medium | Low | Combine with app instance fingerprint |
| Token theft | High | Low | Short expiry + refresh rotation + IP binding |
| Phone number verification | Medium | Medium | MVP allows unverified, Phase 2 adds SMS |
| Password reuse attack | High | Medium | Enforce strong passwords, consider breach detection |

---

## Acceptance Criteria

### Parent Account

- [ ] Parent can register with phone number and password
- [ ] Password complexity rules are enforced
- [ ] Parent can log in and receive valid tokens
- [ ] Parent can log out (tokens invalidated)
- [ ] Parent can refresh access token using refresh token
- [ ] Parent can view and update their profile
- [ ] Duplicate phone registration is rejected with clear error

### Child Profile

- [ ] Parent can create child profile with name and age
- [ ] Unique invite code is auto-generated for each profile
- [ ] Parent can view all their children's profiles
- [ ] Parent can update child's name, age, avatar
- [ ] Parent can archive (soft delete) child profile
- [ ] Invite code is invalidated when profile is archived
- [ ] Parent can regenerate invite code for a profile

### Child Device Binding

- [ ] Child can enter invite code to bind device
- [ ] Valid invite code binds device to profile
- [ ] Bound child receives authentication tokens
- [ ] Invalid invite code shows appropriate error
- [ ] Already-bound device cannot bind to another profile
- [ ] Child can view their bound profile
- [ ] Child can unbind their device

### Security

- [ ] Rate limiting works for login, registration, and bind endpoints
- [ ] Expired tokens return 401 with proper error message
- [ ] Blacklisted tokens are rejected
- [ ] Passwords are hashed with bcrypt before storage
- [ ] API responses never include password hashes

---

## Implementation Phases

### Phase 1: Core Authentication (Priority: P0)

1. Set up database models (User, ChildProfile)
2. Implement password hashing and validation
3. Build registration endpoint
4. Build login endpoint with JWT generation
5. Build token refresh endpoint
6. Add authentication middleware

### Phase 2: Profile Management (Priority: P0)

1. Child profile CRUD endpoints
2. Invite code generation logic
3. Profile listing and retrieval
4. Profile update and archive

### Phase 3: Device Binding (Priority: P0)

1. Device binding endpoint
2. Invite code validation
3. Child authentication flow
4. Device unbind functionality

### Phase 4: Security Hardening (Priority: P1)

1. Rate limiting implementation
2. Token blacklist for logout
3. Request validation and sanitization
4. Error handling standardization

---

## Testing Strategy

### Unit Tests

- Password hashing and verification
- JWT token generation and validation
- Invite code generation uniqueness
- Model validation rules

### Integration Tests

- Full registration flow
- Login and token refresh cycle
- Child profile CRUD operations
- Device binding flow

### Security Tests

- Rate limiting verification
- Token expiration handling
- Invalid token rejection
- SQL injection prevention
- XSS prevention in inputs

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-DB-001 | Alternative approach | Could be merged if preferred |
| SPEC-TASK-001 | Downstream | Requires User and ChildProfile |
| SPEC-POINT-001 | Downstream | Requires ChildProfile for accounts |
| SPEC-ONBOARD-001 | Downstream | Uses registration flow |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
