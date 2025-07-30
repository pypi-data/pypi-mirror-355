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

## Usage Examples

### 1. Initialize the SDK (Recommended)

```python
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK
from intelliopsopenfgasdk_python.models import CreateFgaModel

sdk = IntelliOpsOpenFgaSDK()
fga_model = CreateFgaModel(
    token="your-token",
    tenantId="your-tenant-id",
    connectorType="Confluence",
    orgId="your-org-id",
    fgaStoreId="your-fga-store-id"
)
sdk.initialize(fga_model)  # This will call both datasource and FGA initialization
```

### 2. Initialize FGA Data Source (Manual)

```python
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK
from intelliopsopenfgasdk_python.models import CreateDataSourceModel

sdk = IntelliOpsOpenFgaSDK()
datasource_model = CreateDataSourceModel(
    orgId="your-org-id",
    connectorType="Confluence",
    fgaStoreId="your-fga-store-id",
    tenantId="your-tenant-id"
)
sdk._IntelliOpsOpenFgaSDK__init_datasource(datasource_model)
```

### 3. Initialize FGA (Manual)

```python
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK
from intelliopsopenfgasdk_python.models import CreateFgaModel

sdk = IntelliOpsOpenFgaSDK()
fga_model = CreateFgaModel(
    token="your-token",
    tenantId="your-tenant-id",
    connectorType="Confluence",
    orgId="your-org-id",
    fgaStoreId="your-fga-store-id"
)
sdk._IntelliOpsOpenFgaSDK__init_fga(fga_model)
```

### 4. Check Access (Sync)

```python
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK

sdk = IntelliOpsOpenFgaSDK()
user_id = "user-id"
l2_object_id = "object-id"
has_access = sdk.check_access(user_id, l2_object_id)
print("User has access?", has_access)
```

### 5. Check Access (Async)

```python
import asyncio
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK

sdk = IntelliOpsOpenFgaSDK()
async def main():
    user_id = "user-id"
    l2_object_id = "object-id"
    has_access = await sdk.async_check_access(user_id, l2_object_id)
    print("User has access?", has_access)

asyncio.run(main())
```

### 6. Async Initialization (Advanced)

```python
import asyncio
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK
from intelliopsopenfgasdk_python.models import CreateFgaModel, CreateDataSourceModel

sdk = IntelliOpsOpenFgaSDK()
async def main():
    datasource_model = CreateDataSourceModel(
        orgId="your-org-id",
        connectorType="Confluence",
        fgaStoreId="your-fga-store-id",
        tenantId="your-tenant-id"
    )
    await sdk.__async_init_datasource(datasource_model)
    fga_model = CreateFgaModel(
        token="your-token",
        tenantId="your-tenant-id",
        connectorType="Confluence",
        orgId="your-org-id",
        fgaStoreId="your-fga-store-id"
    )
    await sdk.__async_init_fga(fga_model)

asyncio.run(main())
```

## Testing

Run tests using pytest:

```powershell
pytest
```

## Build & Publish

See [build.md](build.md) for detailed build and publishing instructions.

## License

[MIT](LICENSE)
