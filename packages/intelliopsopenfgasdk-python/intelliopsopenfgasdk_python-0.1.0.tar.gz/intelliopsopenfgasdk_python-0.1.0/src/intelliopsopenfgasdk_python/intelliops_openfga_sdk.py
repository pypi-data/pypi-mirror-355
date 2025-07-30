from .models import CreateFgaModel, CreateGroupsModel, CreateL1L2ObjectsModel
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

    def init_fga(self, create_fga_model: CreateFgaModel) -> None:
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
        create_groups_endpoint = f"confluence/create-groups"
        create_l1_l2_objects_endpoint = f"confluence/create-l1-l2-objects"

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
            # Handle HTTP errors (non-2xx status codes)
            raise RuntimeError(
                f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            # Handle network errors
            raise RuntimeError(f"Request error occurred: {exc}") from exc

    def check_access(self, user_id: str, l2_object_id: str) -> bool:
        """
        Checks access for the user.
        Returns:
            bool: True if the user has access, False otherwise.
        Raises:
            httpx.HTTPStatusError: If the response status is not 2xx.
            httpx.RequestError: For network-related errors.
        """
        check_access_endpoint = f"access/check"
        try:
            response = self.http_client.post(
                check_access_endpoint,
                json={"user_id": user_id, "l2_object_id": l2_object_id},
            )
            response.raise_for_status()
            hasAccess = response.json().get("hasAccess", False)
            return hasAccess
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Request error occurred: {exc}") from exc
