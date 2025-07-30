from .models import (
    CreateFgaModel,
    CreateGroupsModel,
    CreateL1L2ObjectsModel,
    CreateDataSourceModel,
    CheckAccessModel,
)
from .http_client import HttpClient
import httpx


class IntelliOpsOpenFgaSDK:
    def __init__(self, base_url="http://localhost:3002", headers=None, timeout=10.0):
        """
        Initializes the IntelliOpsOpenFgaSDK with a reusable HttpClient instance.
        Args:
            base_url (str, optional): The base URL for the HttpClient.
            headers (dict, optional): Default headers for the HttpClient.
            timeout (float, optional): Timeout for requests in seconds.
        """
        self.http_client = HttpClient(
            base_url=base_url, headers=headers, timeout=timeout
        )

    def initialize(self, create_fga_model: CreateFgaModel) -> None:
        """
        Initializes the SDK by setting up the HttpClient.
        This method can be extended to perform any additional initialization logic if needed.
        Returns:
            None
        """
        create_datasource_model = CreateDataSourceModel(
            orgId=create_fga_model.orgId,
            connectorType=create_fga_model.connectorType,
            fgaStoreId=create_fga_model.fgaStoreId,
            tenantId=create_fga_model.tenantId,
        )
        self.__init_datasource(create_datasource_model)

        self.__init_fga(create_fga_model)

    def _handle_http_error(self, exc):
        status_code = getattr(exc.response, "status_code", None)
        text = getattr(exc.response, "text", str(exc))
        raise RuntimeError(f"HTTP error occurred: {status_code} - {text}") from exc

    def _handle_request_error(self, exc):
        raise RuntimeError(f"Request error occurred: {exc}") from exc

    def __init_datasource(self, create_datasource_model: CreateDataSourceModel) -> None:
        """
        Initializes the datasource for FGA.
        Args:
            create_fga_model (CreateDataSourceModel): The model containing the necessary parameters.
        Returns:
            None
        Raises:
            httpx.HTTPStatusError: If the response status is not 2xx.
            httpx.RequestError: For network-related errors.
        """
        init_datasource_endpoint = "auth/sync"
        try:
            response = self.http_client.post(
                init_datasource_endpoint, json=create_datasource_model
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)

    async def __async_init_datasource(
        self, create_datasource_model: CreateDataSourceModel
    ) -> None:
        """
        Asynchronously initializes the datasource for FGA.
        Args:
            create_datasource_model (CreateDataSourceModel): The model containing the necessary parameters.
        Returns:
            None
        Raises:
            RuntimeError: If an HTTP or network error occurs.
        """
        init_datasource_endpoint = "auth/sync"
        try:
            response = await self.http_client.async_post(
                init_datasource_endpoint, json=create_datasource_model
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)

    def __init_fga(self, create_fga_model: CreateFgaModel) -> None:
        """
        Creates a new FGA model.
        Args:
            model_name (str): The name of the model to create.
            model_definition (dict): The definition of the model.
        Returns:
            dict: The response from the FGA service.
        Raises:
            httpx.HTTPStatusError: If the response status is not 2xx.
            httpx.RequestError: For network-related errors.
        """
        create_groups_endpoint = "confluence/create-groups"
        create_l1_l2_objects_endpoint = "confluence/create-l1-l2-objects"

        try:
            # Create groups
            create_groups_model: CreateGroupsModel = CreateGroupsModel(
                token=create_fga_model.token,
                orgId=create_fga_model.orgId,
                connectorType=create_fga_model.connectorType,
            )
            create_groups_model_response = self.http_client.post(
                create_groups_endpoint, json=create_groups_model
            )
            create_groups_model_response.raise_for_status()

            # Create L1 and L2 objects
            create_l1_l2_objects_model: CreateL1L2ObjectsModel = CreateL1L2ObjectsModel(
                token=create_fga_model.token,
                tenantId=create_fga_model.tenantId,
                connectorType=create_fga_model.connectorType,
                orgId=create_fga_model.orgId,
                fgaStoreId=create_fga_model.fgaStoreId,
            )
            create_l1_l2_objects_model_response = self.http_client.post(
                create_l1_l2_objects_endpoint, json=create_l1_l2_objects_model
            )
            create_l1_l2_objects_model_response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)

    async def __async_init_fga(self, create_fga_model: CreateFgaModel) -> None:
        """
        Asynchronously creates a new FGA model.
        Args:
            create_fga_model (CreateFgaModel): The model containing the necessary parameters.
        Returns:
            None
        Raises:
            RuntimeError: If an HTTP or network error occurs.
        """
        create_groups_endpoint = "confluence/create-groups"
        create_l1_l2_objects_endpoint = "confluence/create-l1-l2-objects"
        try:
            create_groups_model = CreateGroupsModel(
                token=create_fga_model.token,
                orgId=create_fga_model.orgId,
                connectorType=create_fga_model.connectorType,
            )
            create_groups_model_response = await self.http_client.async_post(
                create_groups_endpoint, json=create_groups_model
            )
            create_groups_model_response.raise_for_status()
            create_l1_l2_objects_model = CreateL1L2ObjectsModel(
                token=create_fga_model.token,
                tenantId=create_fga_model.tenantId,
                connectorType=create_fga_model.connectorType,
                orgId=create_fga_model.orgId,
                fgaStoreId=create_fga_model.fgaStoreId,
            )
            create_l1_l2_objects_model_response = await self.http_client.async_post(
                create_l1_l2_objects_endpoint, json=create_l1_l2_objects_model
            )
            create_l1_l2_objects_model_response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)

    def check_access(self, check_access_model: CheckAccessModel) -> bool:
        """
        Checks access for the user.
        Returns:
            bool: True if the user has access, False otherwise.
        Raises:
            httpx.HTTPStatusError: If the response status is not 2xx.
            httpx.RequestError: For network-related errors.
        """
        check_access_endpoint = "access/check"
        try:
            response = self.http_client.post(
                check_access_endpoint,
                json={
                    "user_id": check_access_model.user_id,
                    "l2_object_id": check_access_model.l2_object_id,
                },
            )
            response.raise_for_status()
            hasAccess = response.json().get("hasAccess", False)
            return hasAccess
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)

    async def async_check_access(self, check_access_model: CheckAccessModel) -> bool:
        """
        Asynchronously checks access for the user.
        Args:
            user_id (str): The user identifier.
            l2_object_id (str): The L2 object identifier.
        Returns:
            bool: True if the user has access, False otherwise.
        Raises:
            RuntimeError: If an HTTP or network error occurs.
        """
        check_access_endpoint = "access/check"
        try:
            response = await self.http_client.async_post(
                check_access_endpoint,
                json={
                    "user_id": check_access_model.user_id,
                    "l2_object_id": check_access_model.l2_object_id,
                },
            )
            response.raise_for_status()
            return response.json().get("hasAccess", False)
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc)
        except httpx.RequestError as exc:
            self._handle_request_error(exc)
