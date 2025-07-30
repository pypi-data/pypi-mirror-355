# IntelliOpsOpenFgaSDK-Python

An efficient, asynchronous Python SDK for communicating with the IntelliOps FGA API.

## Features
- Async API calls using `aiohttp`
- Fast and efficient client
- Easy integration with asyncio-based applications
- Example methods for permission checking and listing

## Installation

Install from local directory:

```bash
pip install .
```

Or install dependencies for development:

```bash
pip install -r requirements.txt
```

## Usage Examples

### 1. Initialize FGA Data Source

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
sdk.init_datasource(datasource_model)
```

### 2. Initialize FGA

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
sdk.init_fga(fga_model)
```

### 3. Check Access

```python
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK

sdk = IntelliOpsOpenFgaSDK()
user_id = "user-id"
l2_object_id = "object-id"
has_access = sdk.check_access(user_id, l2_object_id)
print("User has access?", has_access)
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
