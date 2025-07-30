import pytest
from intelliopsopenfgasdk_python.intelliops_openfga_sdk import IntelliOpsOpenFgaSDK
from intelliopsopenfgasdk_python.models import CreateFgaModel
import httpx


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self._status_code = status_code
        self.status_code = status_code  # Add this for compatibility with httpx.Response
        self._json_data = json_data or {}
        self.text = str(json_data)

    def raise_for_status(self):
        if not (200 <= self._status_code < 300):
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json_data


class DummyHttpClient:
    def __init__(self):
        self.last_post = None

    def post(self, url, json=None):
        self.last_post = (url, json)
        # Simulate different endpoints
        if url == "confluence/create-groups":
            return DummyResponse(200)
        elif url == "confluence/create-l1-l2-objects":
            return DummyResponse(200)
        elif url == "access/check":
            # Return False for a specific l2_object_id to test negative case
            if json and json.get("l2_object_id") == "t417ce8a_Confluence_e4448be1-8022-43a2-b234-e467842aac60_19048045":
                return DummyResponse(200, {"hasAccess": False})
            return DummyResponse(200, {"hasAccess": True})
        return DummyResponse(404)


def test_init_fga_success(monkeypatch):
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = DummyHttpClient()
    model = CreateFgaModel(
        token="token",
        tenantId="tenant",
        connectorType="Confluence",
        orgId="org",
        fgaStoreId="store"
    )
    sdk.init_fga(model)
    # Should call both endpoints
    assert sdk.http_client.last_post[0] == 'confluence/create-l1-l2-objects'


def test_init_fga_http_error(monkeypatch):
    class ErrorHttpClient(DummyHttpClient):
        def post(self, url, json=None):
            return DummyResponse(400)
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = ErrorHttpClient()
    model = CreateFgaModel(
        token="token",
        tenantId="tenant",
        connectorType="Confluence",
        orgId="org",
        fgaStoreId="store"
    )
    with pytest.raises(RuntimeError):
        sdk.init_fga(model)


def test_check_access_true():
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = DummyHttpClient()
    assert (
        sdk.check_access(
            "t417ce8a_Confluence_e4448be1-8022-43a2-b234-e467842aac60_5b70c8b80fd0ac05d389f5e9",
            "t417ce8a_Confluence_e4448be1-8022-43a2-b234-e467842aac60_190480451",
        )
        is True
    )


def test_check_access_false():
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = DummyHttpClient()
    assert (
        sdk.check_access(
            "t417ce8a_Confluence_e4448be1-8022-43a2-b234-e467842aac60_5b70c8b80fd0ac05d389f5e9",
            "t417ce8a_Confluence_e4448be1-8022-43a2-b234-e467842aac60_19048045",
        )
        is False
    )


def test_init_datasource_success():
    from intelliopsopenfgasdk_python.models import CreateDataSourceModel
    class DummyHttpClientDs(DummyHttpClient):
        def post(self, url, json=None):
            assert url == "auth/sync"
            return DummyResponse(200)
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = DummyHttpClientDs()
    model = CreateDataSourceModel(
        orgId="org",
        connectorType="Confluence",
        fgaStoreId="store",
        tenantId="tenant"
    )
    sdk.init_datasource(model)


def test_init_datasource_http_error():
    from intelliopsopenfgasdk_python.models import CreateDataSourceModel
    class ErrorHttpClient(DummyHttpClient):
        def post(self, url, json=None):
            return DummyResponse(400)
    sdk = IntelliOpsOpenFgaSDK()
    sdk.http_client = ErrorHttpClient()
    model = CreateDataSourceModel(
        orgId="org",
        connectorType="Confluence",
        fgaStoreId="store",
        tenantId="tenant"
    )
    with pytest.raises(RuntimeError):
        sdk.init_datasource(model)
