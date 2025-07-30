from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """Represents a product or service defined in Billit."""

    product_id: int = Field(alias="ProductID")
    description: str = Field(alias="Description")

    model_config = ConfigDict(populate_by_name=True)


class ProductUpsert(BaseModel):
    """Model used for creating or updating a product."""

    product_id: Optional[int] = Field(default=None, alias="ProductID")
    description: str = Field(alias="Description")

    model_config = ConfigDict(populate_by_name=True)
