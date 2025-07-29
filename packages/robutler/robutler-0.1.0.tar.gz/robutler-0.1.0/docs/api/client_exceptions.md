# Exceptions

The API Client provides comprehensive error handling through custom exception classes that give detailed information about API errors and system failures.

## RobutlerApiError

::: robutler.api.client.RobutlerApiError

## Error Handling Patterns

### Basic Error Handling

```python
from robutler.api import RobutlerApi, RobutlerApiError

async with RobutlerApi() as api:
    try:
        user = await api.get_user_info()
    except RobutlerApiError as e:
        print(f"API Error: {e.message}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
        if e.details:
            print(f"Details: {e.details}")
```

### Status Code Handling

```python
try:
    result = await api.create_api_key("MyKey")
except RobutlerApiError as e:
    if e.status_code == 401:
        print("Authentication failed - check your API key")
    elif e.status_code == 402:
        print("Insufficient credits")
    elif e.status_code == 429:
        print("Rate limit exceeded - please wait")
    elif e.status_code == 500:
        print("Server error - please try again later")
    else:
        print(f"Unexpected error: {e.message}")
```

### Payment Token Errors

```python
try:
    result = await api.redeem_payment_token(token, amount=1000)
except RobutlerApiError as e:
    if e.status_code == 402:
        if "insufficient" in e.message.lower():
            print("Token has insufficient balance")
        elif "expired" in e.message.lower():
            print("Token has expired")
        elif "invalid" in e.message.lower():
            print("Token is invalid or already used")
    else:
        print(f"Payment error: {e.message}")
```

### Intent Router Errors

```python
try:
    results = await api.search_intents("help with coding")
except RobutlerApiError as e:
    if e.status_code == 503:
        print("Intent router service unavailable")
    elif e.status_code == 400:
        print("Invalid search parameters")
    else:
        print(f"Search error: {e.message}")
```

## Error Categories

### Authentication Errors (401)
- Invalid API key
- Expired authentication token
- Missing authorization header

### Payment Errors (402)
- Insufficient credits
- Invalid payment token
- Expired payment token
- Token already redeemed

### Rate Limiting (429)
- API rate limit exceeded
- Daily credit limit reached
- Session limit exceeded

### Server Errors (5xx)
- Internal server error (500)
- Service unavailable (503)
- Gateway timeout (504)

## Best Practices

### Retry Logic

```python
import asyncio
from robutler.api import RobutlerApiError

async def retry_api_call(api_func, max_retries=3, delay=1.0):
    """Retry API calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await api_func()
        except RobutlerApiError as e:
            if e.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
```

### Graceful Degradation

```python
async def get_user_info_safe(api):
    """Get user info with graceful fallback."""
    try:
        return await api.get_user_info()
    except RobutlerApiError as e:
        if e.status_code == 401:
            print("Authentication required")
            return None
        elif e.status_code in [500, 503]:
            print("Service temporarily unavailable")
            return {"name": "Unknown", "email": "unknown@example.com"}
        else:
            raise
``` 