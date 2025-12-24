# Phase 2 Implementation Guide: Fernet Encryption

**Purpose**: Encrypt sensitive data source credentials before storing in database
**Library**: `cryptography` (Fernet symmetric encryption)
**Complexity**: Simple and reliable

---

## 1. Installation

```bash
# Add to backend/requirements.txt
cryptography>=41.0.0
```

```bash
# Install
pip install cryptography
```

---

## 2. Generate Encryption Key

```bash
# Generate a new Fernet key (do this once)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Output example:
# 8fHQqT9vZ2xK4pN7mL1wR5sY3uE6bA0cD9gF2hJ8kM4=
```

Add to `.env`:
```bash
ENCRYPTION_KEY=8fHQqT9vZ2xK4pN7mL1wR5sY3uE6bA0cD9gF2hJ8kM4=
```

---

## 3. Implementation

### 3.1 Create Encryption Utility

**File**: `backend/app/core/encryption.py`

```python
"""
Encryption utilities for sensitive data.
Uses Fernet (symmetric encryption) for simplicity and reliability.
"""
from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""

    def __init__(self):
        """Initialize with encryption key from settings."""
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY not configured in environment")

        # Fernet expects bytes
        key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt (e.g., password)

        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return plaintext

        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext

        decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing data
            fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(result[field])
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            fields: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result


# Singleton instance
encryption_service = EncryptionService()
```

### 3.2 Update Config

**File**: `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # Phase 2: Encryption
    ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.3 Update DataSource Service

**File**: `backend/app/services/data_source_service.py`

```python
from app.core.encryption import encryption_service
from app.models.source import DataSource
from app.repositories.source_repository import SourceRepository

class DataSourceService:
    """Service for managing data sources."""

    # Fields that contain sensitive data
    SENSITIVE_FIELDS = ["password", "api_key", "secret"]

    async def create_source(self, source_data: dict) -> DataSource:
        """
        Create a new data source with encrypted credentials.

        Args:
            source_data: Data source information

        Returns:
            Created data source
        """
        # Encrypt sensitive fields in connection_config
        if "connection_config" in source_data:
            source_data["connection_config"] = encryption_service.encrypt_dict(
                source_data["connection_config"],
                self.SENSITIVE_FIELDS
            )

        # Save to database
        source = await self.repository.create(source_data)
        return source

    async def get_source_with_decrypted_config(self, source_id: str) -> DataSource:
        """
        Get data source with decrypted connection config.
        Used internally for connection testing.

        Args:
            source_id: Data source ID

        Returns:
            Data source with decrypted credentials
        """
        source = await self.repository.get(source_id)
        if not source:
            return None

        # Decrypt connection_config for internal use
        if source.connection_config:
            source.connection_config = encryption_service.decrypt_dict(
                source.connection_config,
                self.SENSITIVE_FIELDS
            )

        return source
```

### 3.4 Update API Response Schema

**File**: `backend/app/schemas/source.py`

```python
from pydantic import BaseModel, field_serializer

class DataSourceResponse(BaseModel):
    """Data source response schema (masks sensitive fields)."""

    id: str
    name: str
    type: str
    connection_config: dict
    # ... other fields ...

    @field_serializer('connection_config')
    def mask_sensitive_fields(self, config: dict) -> dict:
        """Mask sensitive fields in API response."""
        if not config:
            return config

        masked = config.copy()
        sensitive_fields = ["password", "api_key", "secret"]

        for field in sensitive_fields:
            if field in masked:
                masked[field] = "******"  # Mask the value

        return masked

    class Config:
        from_attributes = True
```

---

## 4. Usage Examples

### 4.1 Create Data Source (Encrypts Automatically)

```python
# API endpoint
@router.post("/sources", response_model=DataSourceResponse)
async def create_data_source(
    source_data: DataSourceCreate,
    service: DataSourceService = Depends(get_data_source_service)
):
    """Create a new data source."""
    source = await service.create_source(source_data.dict())
    return source
```

**Request**:
```json
{
  "name": "Oracle Production",
  "type": "oracle",
  "connection_config": {
    "host": "192.168.144.143",
    "port": 1521,
    "service_name": "pdb1",
    "username": "f10app",
    "password": "oracle"  // Will be encrypted
  }
}
```

**Response** (password is masked):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Oracle Production",
  "type": "oracle",
  "connection_config": {
    "host": "192.168.144.143",
    "port": 1521,
    "service_name": "pdb1",
    "username": "f10app",
    "password": "******"  // Masked in response
  }
}
```

**Database** (password is encrypted):
```sql
SELECT connection_config FROM sources WHERE id = '550e8400...';
-- Result:
-- {
--   "host": "192.168.144.143",
--   "port": 1521,
--   "service_name": "pdb1",
--   "username": "f10app",
--   "password": "gAAAAABl..."  // Encrypted with Fernet
-- }
```

### 4.2 Test Connection (Decrypts Internally)

```python
@router.post("/sources/{source_id}/test")
async def test_connection(
    source_id: str,
    service: DataSourceService = Depends(get_data_source_service),
    connection_service: ConnectionService = Depends(get_connection_service)
):
    """Test connection to data source."""
    # Get source with decrypted credentials (internal use only)
    source = await service.get_source_with_decrypted_config(source_id)

    # Test connection with real credentials
    result = await connection_service.test_connection(
        source.type,
        source.connection_config  # Decrypted
    )

    return result
```

---

## 5. Security Best Practices

### 5.1 Key Management

✅ **DO**:
- Store `ENCRYPTION_KEY` in `.env` file (not in code)
- Add `.env` to `.gitignore`
- Use different keys for dev/staging/production
- Rotate keys periodically (with migration script)

❌ **DON'T**:
- Commit encryption key to Git
- Share encryption key in Slack/email
- Use the same key across environments

### 5.2 Access Control

```python
# Only decrypt when absolutely necessary
# Bad: Decrypt for every API call
async def get_source(source_id: str):
    source = await repo.get(source_id)
    source.connection_config = decrypt(source.connection_config)  # ❌ Don't do this
    return source

# Good: Only decrypt for internal operations
async def test_connection(source_id: str):
    source = await repo.get(source_id)
    # Decrypt only when needed for connection testing
    decrypted_config = decrypt(source.connection_config)  # ✅ OK
    return test_with_config(decrypted_config)
```

### 5.3 Logging

```python
# Never log decrypted credentials
import logging

logger = logging.getLogger(__name__)

# Bad
logger.info(f"Testing connection with config: {decrypted_config}")  # ❌ Leaks password

# Good
logger.info(f"Testing connection to {config['host']}")  # ✅ Safe
```

---

## 6. Testing

### 6.1 Unit Test

**File**: `backend/tests/test_encryption.py`

```python
import pytest
from app.core.encryption import EncryptionService

def test_encrypt_decrypt():
    """Test basic encryption and decryption."""
    service = EncryptionService()

    plaintext = "my-secret-password"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)

    assert encrypted != plaintext  # Should be encrypted
    assert decrypted == plaintext  # Should decrypt correctly

def test_encrypt_dict():
    """Test dictionary field encryption."""
    service = EncryptionService()

    data = {
        "host": "localhost",
        "username": "admin",
        "password": "secret123"
    }

    encrypted_data = service.encrypt_dict(data, ["password"])

    assert encrypted_data["host"] == "localhost"  # Not encrypted
    assert encrypted_data["username"] == "admin"  # Not encrypted
    assert encrypted_data["password"] != "secret123"  # Encrypted

    decrypted_data = service.decrypt_dict(encrypted_data, ["password"])
    assert decrypted_data["password"] == "secret123"  # Decrypted
```

### 6.2 Integration Test

```python
async def test_create_source_encrypts_password(client, db_session):
    """Test that password is encrypted when creating data source."""
    response = await client.post("/api/v1/sources", json={
        "name": "Test Oracle",
        "type": "oracle",
        "connection_config": {
            "host": "localhost",
            "username": "test",
            "password": "plaintext-password"
        }
    })

    assert response.status_code == 201
    source_id = response.json()["id"]

    # Check database - password should be encrypted
    source = await db_session.get(DataSource, source_id)
    stored_password = source.connection_config["password"]

    assert stored_password != "plaintext-password"  # Encrypted
    assert stored_password.startswith("gAAAAA")  # Fernet format

    # Check API response - password should be masked
    assert response.json()["connection_config"]["password"] == "******"
```

---

## 7. Migration Script (If Needed)

If you need to encrypt existing data:

```python
# scripts/encrypt_existing_credentials.py
import asyncio
from app.db import get_db_session
from app.models.source import DataSource
from app.core.encryption import encryption_service

async def encrypt_existing_sources():
    """Encrypt passwords in existing data sources."""
    async with get_db_session() as session:
        sources = await session.execute(select(DataSource))
        sources = sources.scalars().all()

        for source in sources:
            if source.connection_config:
                # Check if already encrypted (Fernet format starts with 'gAAAAA')
                password = source.connection_config.get("password", "")
                if password and not password.startswith("gAAAAA"):
                    # Encrypt plaintext password
                    source.connection_config["password"] = encryption_service.encrypt(password)
                    session.add(source)

        await session.commit()
        print(f"Encrypted {len(sources)} data sources")

if __name__ == "__main__":
    asyncio.run(encrypt_existing_sources())
```

---

## 8. Troubleshooting

### Error: "ENCRYPTION_KEY not configured"
**Solution**: Add `ENCRYPTION_KEY` to `.env` file

### Error: "Invalid token" when decrypting
**Possible causes**:
1. Encryption key changed (data encrypted with old key)
2. Data corrupted in database
3. Trying to decrypt non-encrypted data

**Solution**: Re-encrypt data with current key

---

**Document Version**: v1.0
**Last Updated**: 2025-12-23
**Maintainer**: QC Agent (Claude)
**Phase**: Phase 2 - Data Source Connection + Manual Lineage
