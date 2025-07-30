from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Party(BaseModel):
    party_id: int = Field(alias="PartyID")
    name: str = Field(alias="Name")

    model_config = ConfigDict(populate_by_name=True)


class PartyCreate(BaseModel):
    name: str


class PartyUpdate(BaseModel):
    """Model for updating party (customer/supplier) information.
    
    All fields are optional for PATCH operations.
    Based on Billit API patchable properties documentation.
    """
    name: Optional[str] = Field(None, alias="Name")
    commercial_name: Optional[str] = Field(None, alias="CommercialName")
    contact_first_name: Optional[str] = Field(None, alias="ContactFirstName")
    contact_last_name: Optional[str] = Field(None, alias="ContactLastName")
    email: Optional[str] = Field(None, alias="Email")
    phone: Optional[str] = Field(None, alias="Phone")
    mobile: Optional[str] = Field(None, alias="Mobile")
    fax: Optional[str] = Field(None, alias="Fax")
    vat_number: Optional[str] = Field(None, alias="VATNumber")
    iban: Optional[str] = Field(None, alias="IBAN")
    language: Optional[str] = Field(None, alias="Language")
    country_code: Optional[str] = Field(None, alias="CountryCode")
    city: Optional[str] = Field(None, alias="City")
    street: Optional[str] = Field(None, alias="Street")
    street_number: Optional[str] = Field(None, alias="StreetNumber")
    zipcode: Optional[str] = Field(None, alias="Zipcode")
    box: Optional[str] = Field(None, alias="Box")
    vat_liable: Optional[bool] = Field(None, alias="VATLiable")
    gl_account_code: Optional[str] = Field(None, alias="GLAccountCode")
    gl_default_expiry_offset: Optional[str] = Field(None, alias="GLDefaultExpiryOffset")
    nr: Optional[str] = Field(None, alias="Nr")
    external_provider_tc: Optional[str] = Field(None, alias="ExternalProviderTC")
    external_provider_id: Optional[str] = Field(None, alias="ExternalProviderID")

    model_config = ConfigDict(populate_by_name=True)
