from pydantic import BaseModel, Field
from typing import Optional


class CreateFgaModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    tenant_uid: Optional[str] = Field(None, description="Tenant ID")
    connector_type: str = Field(..., description="Type of connector")
    org_id: str = Field(..., description="Organization ID")
    fga_store_id: Optional[str] = Field(None, description="FGA Store ID")


class CreateGroupsModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    org_id: str = Field(..., description="Organization ID")
    connector_type: str = Field(..., description="Type of connector")


class CreateL1L2ObjectsModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    tenant_uid: Optional[str] = Field(None, description="Tenant ID")
    connector_type: str = Field(..., description="Type of connector")
    org_id: str = Field(..., description="Organization ID")
    fga_store_id: Optional[str] = Field(None, description="FGA Store ID")


class CreateDataSourceModel(BaseModel):
    org_id: str = Field(..., description="Organization ID")
    connector_type: str = Field(..., description="Type of connector")
    fga_store_id: Optional[str] = Field(None, description="FGA Store ID")
    tenant_uid: Optional[str] = Field(None, description="Tenant ID")


class CheckAccessModel(BaseModel):
    tenant_uid: str = Field(..., description="Tenant ID")
    connector_type: str = Field(..., description="Type of connector")
    org_id: str = Field(..., description="Organization ID")
    datasource_user_id: str = Field(..., description="Datasource User ID")
    data_object_id: str = Field(..., description="Data Object ID")

    @property
    def user_id(self) -> str:
        """Returns the user_id in the format <tenant_id>_<connector_type>_<org_id>_<datasource_user_id>"""
        return f"{self.tenant_uid}_{self.connector_type}_{self.org_id}_{self.datasource_user_id}"

    @property
    def l2_object_id(self) -> str:
        """Returns the l2_object_id in the format <tenant_id>_<connector_type>_<org_id>_<data_object_id>"""
        return f"{self.tenant_uid}_{self.connector_type}_{self.org_id}_{self.data_object_id}"
