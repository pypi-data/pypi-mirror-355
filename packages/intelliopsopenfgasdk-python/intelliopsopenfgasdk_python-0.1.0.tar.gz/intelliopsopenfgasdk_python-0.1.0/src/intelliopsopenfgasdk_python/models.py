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