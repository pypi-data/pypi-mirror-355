# IntelliOpsOpenFgaSDK-Python

An efficient, asynchronous Python SDK for communicating with the IntelliOps FGA API.

## Features
- Async API calls using `aiohttp`
- Fast and efficient client
- Easy integration with asyncio-based applications
- Example methods for permission checking and listing

## Installation

Install via pip (after publishing):

```bash
pip install intelliopsopenfgasdk-python
```

Or install dependencies for development:

```bash
pip install -r requirements.txt
```

## Usage

```python
import asyncio
from src.intelliopsopenfgasdk_python.client import Client

async def main():
    async with Client(base_url="https://api.intelliops.com", api_key="your-key") as client:
        allowed = await client.check_permission("alice", "read", "document:123")
        print("Allowed:", allowed)
        permissions = await client.list_permissions("alice")
        print("Permissions:", permissions)

asyncio.run(main())
```

## Testing

Run tests using pytest:

```powershell
pytest
```

## License

[MIT](LICENSE)
