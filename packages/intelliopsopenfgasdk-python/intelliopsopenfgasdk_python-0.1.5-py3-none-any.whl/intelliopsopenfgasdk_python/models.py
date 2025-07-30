from pydantic import BaseModel, Field
from typing import Optional


class CreateFgaModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    tenantId: Optional[str] = Field(None, description="Tenant ID")
    connectorType: str = Field(..., description="Type of connector")
    orgId: str = Field(..., description="Organization ID")
    fgaStoreId: Optional[str] = Field(None, description="FGA Store ID")


class CreateGroupsModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    orgId: str = Field(..., description="Organization ID")
    connectorType: str = Field(..., description="Type of connector")


class CreateL1L2ObjectsModel(BaseModel):
    token: str = Field(..., description="Authentication token")
    tenantId: Optional[str] = Field(None, description="Tenant ID")
    connectorType: str = Field(..., description="Type of connector")
    orgId: str = Field(..., description="Organization ID")
    fgaStoreId: Optional[str] = Field(None, description="FGA Store ID")


class CreateDataSourceModel(BaseModel):
    orgId: str = Field(..., description="Organization ID")
    connectorType: str = Field(..., description="Type of connector")
    fgaStoreId: Optional[str] = Field(None, description="FGA Store ID")
    tenantId: Optional[str] = Field(None, description="Tenant ID")


class CheckAccessModel(BaseModel):
    tenantId: str = Field(..., description="Tenant ID")
    connectorType: str = Field(..., description="Type of connector")
    orgId: str = Field(..., description="Organization ID")
    datasource_user_id: str = Field(..., description="Datasource User ID")
    data_object_id: str = Field(..., description="Data Object ID")

    @property
    def user_id(self) -> str:
        """Returns the user_id in the format <tenant_id>_<connector_type>_<org_id>_<datasource_user_id>"""
        return f"{self.tenantId}_{self.connectorType}_{self.orgId}_{self.datasource_user_id}"

    @property
    def l2_object_id(self) -> str:
        """Returns the l2_object_id in the format <tenant_id>_<connector_type>_<org_id>_<data_object_id>"""
        return f"{self.tenantId}_{self.connectorType}_{self.orgId}_{self.data_object_id}"
