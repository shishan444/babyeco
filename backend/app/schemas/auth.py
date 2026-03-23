"""Authentication and user schemas for API validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Enum as SQLAlchemyEnum

from app.models.child_profile import ChildProfileStatus
from app.models.user import UserStatus, UserRole


class PhoneNumberValidation:
    """Phone number validation utilities.

    @MX:NOTE
    Validates E.164 format phone numbers.
    Format: +[country_code][number] (e.g., +8613812345678)
    """

    # Common country codes for validation
    COUNTRY_CODES = {
        "+1": "US/CA",  # United States, Canada
        "+86": "CN",    # China
        "+44": "UK",    # United Kingdom
        "+81": "JP",    # Japan
        "+82": "KR",    # South Korea
        "+49": "DE",    # Germany
        "+33": "FR",    # France
        "+61": "AU",    # Australia
    }

    @classmethod
    def is_valid_e164(cls, phone: str) -> bool:
        """Check if phone number matches E.164 format.

        E.164 format: +[country_code][number]
        - Must start with +
        - Must be 8-15 digits total (excluding +)
        - Must only contain digits after +
        """
        if not phone or not phone.startswith("+"):
            return False

        # Remove + and check if remaining is all digits
        number_part = phone[1:]
        if not number_part.isdigit():
            return False

        # E.164 allows max 15 digits for the subscriber number
        # Total length including country code is typically 8-15 digits
        if not 8 <= len(number_part) <= 15:
            return False

        return True

    @classmethod
    def format_e164(cls, country_code: str, number: str) -> str:
        """Format a phone number to E.164 format."""
        # Remove all non-digit characters
        clean_number = "".join(filter(str.isdigit, number))
        return f"{country_code}{clean_number}"


class PasswordValidation:
    """Password complexity validation.

    @MX:NOTE
    Enforces strong password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - Cannot be phone number or sequential
    """

    @classmethod
    def is_valid_password(cls, password: str, phone: str | None = None) -> tuple[bool, str | None]:
        """Validate password strength.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        # Check if password is phone number (without formatting)
        if phone:
            clean_phone = "".join(filter(str.isdigit, phone))
            clean_password = "".join(filter(str.isdigit, password))
            if clean_phone and clean_password == clean_phone:
                return False, "Password cannot be your phone number"

        # Check for sequential patterns
        if cls._is_sequential(password):
            return False, "Password cannot contain sequential patterns"

        return True, None

    @classmethod
    def _is_sequential(cls, password: str) -> bool:
        """Check if password contains sequential patterns."""
        # Check for common sequences
        sequences = [
            "0123456789",
            "12345678",
            "23456789",
            "34567890",
            "9876543210",
            "87654321",
            "76543210",
            "98765432",
            "abcdefghij",
            "abcdefghijklmnopqrstuvwxyz",
            "zyxwvutsrqponmlkjihgfedcba",
        ]

        password_lower = password.lower()
        for seq in sequences:
            if seq in password_lower:
                return True

        # Check for repeating characters
        for i in range(len(password) - 3):
            if password[i] == password[i + 1] == password[i + 2] == password[i + 3]:
                return True

        return False


class UserBase(BaseModel):
    """Base user schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="User display name")


class UserCreate(UserBase):
    """Schema for user registration."""

    phone: str = Field(
        ...,
        min_length=8,
        max_length=16,
        description="E.164 format phone number (e.g., +8613812345678)",
        examples=["+8613812345678"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 chars, must contain uppercase, lowercase, and digit)",
    )
    email: str | None = Field(
        None,
        description="Optional email address for future use",
    )
    family_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Optional family name (defaults to 'My Family')",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate E.164 phone format."""
        if not PhoneNumberValidation.is_valid_e164(v):
            raise ValueError(
                "Invalid phone number format. Use E.164 format (e.g., +8613812345678)"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str, info) -> str:  # type: ignore
        """Validate password complexity."""
        # Get phone from field if available
        phone = info.data.get("phone") if info else None
        is_valid, error_msg = PasswordValidation.is_valid_password(v, phone)
        if not is_valid:
            raise ValueError(error_msg or "Password does not meet requirements")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    phone: str = Field(..., description="E.164 format phone number")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    phone: str
    name: str
    email: str | None
    avatar_url: str | None
    status: UserStatus
    role: UserRole
    last_login_at: datetime | None
    family_id: UUID | None
    family_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    phone: str = Field(
        ...,
        description="E.164 format phone number",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate E.164 phone format."""
        if not PhoneNumberValidation.is_valid_e164(v):
            raise ValueError(
                "Invalid phone number format. Use E.164 format (e.g., +8613812345678)"
            )
        return v


class ResetPasswordRequest(BaseModel):
    """Schema for password reset with token."""

    token: str = Field(
        ...,
        description="Password reset token",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 chars, must contain uppercase, lowercase, and digit)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        is_valid, error_msg = PasswordValidation.is_valid_password(v)
        if not is_valid:
            raise ValueError(error_msg or "Password does not meet requirements")
        return v


class MessageResponse(BaseModel):
    """Schema for simple success message responses."""

    message: str


class ChildProfileBase(BaseModel):
    """Base child profile schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Child's name")
    birth_date: datetime | None = Field(None, description="Child's birth date")


class ChildProfileCreate(ChildProfileBase):
    """Schema for creating a child profile."""

    avatar_url: str | None = Field(None, description="Avatar image URL")


class ChildProfileUpdate(BaseModel):
    """Schema for updating a child profile."""

    name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None
    birth_date: datetime | None = None


class ChildProfileResponse(ChildProfileBase):
    """Schema for child profile response."""

    id: UUID
    parent_id: UUID
    avatar_url: str | None
    age: int | None
    points_balance: int
    total_points_earned: int
    current_streak: int
    longest_streak: int
    invite_code: str | None
    invite_code_expires_at: datetime | None
    device_id: str | None
    device_bound: bool
    device_bound_at: datetime | None
    status: ChildProfileStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceBindingRequest(BaseModel):
    """Schema for binding a device to a child profile."""

    invite_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^[A-HJ-NP-Z2-9]{6}$",
        description="6-character invite code",
    )
    device_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique device identifier",
    )


class ChildLoginRequest(BaseModel):
    """Schema for child device login."""

    invite_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^[A-HJ-NP-Z2-9]{6}$",
        description="6-character invite code",
    )
    device_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique device identifier",
    )


class ChildLoginResponse(BaseModel):
    """Schema for child login response."""

    profile_id: UUID
    name: str
    age: int | None
    avatar_url: str | None
    points_balance: int
    access_token: str
    refresh_token: str
    expires_in: int
