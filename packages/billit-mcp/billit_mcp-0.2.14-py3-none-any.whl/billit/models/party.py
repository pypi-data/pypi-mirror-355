from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    """Address model for party addresses."""
    address_type: Optional[str] = Field(None, alias="AddressType")
    name: Optional[str] = Field(None, alias="Name")
    street: Optional[str] = Field(None, alias="Street")
    street_number: Optional[str] = Field(None, alias="StreetNumber")
    box: Optional[str] = Field(None, alias="Box")
    zipcode: Optional[str] = Field(None, alias="Zipcode")
    city: Optional[str] = Field(None, alias="City")
    country_code: Optional[str] = Field(None, alias="CountryCode")

    model_config = ConfigDict(populate_by_name=True)


class Party(BaseModel):
    """Complete party model matching Billit API response structure."""
    party_id: int = Field(alias="PartyID")
    name: str = Field(alias="Name")
    
    # Contact information
    commercial_name: Optional[str] = Field(None, alias="CommercialName")
    contact_first_name: Optional[str] = Field(None, alias="ContactFirstName")
    contact_last_name: Optional[str] = Field(None, alias="ContactLastName")
    email: Optional[str] = Field(None, alias="Email")
    phone: Optional[str] = Field(None, alias="Phone")
    mobile: Optional[str] = Field(None, alias="Mobile")
    fax: Optional[str] = Field(None, alias="Fax")
    
    # Business information
    vat_number: Optional[str] = Field(None, alias="VATNumber")
    iban: Optional[str] = Field(None, alias="IBAN")
    language: Optional[str] = Field(None, alias="Language")
    vat_liable: Optional[bool] = Field(None, alias="VATLiable")
    
    # Primary address (flat fields)
    street: Optional[str] = Field(None, alias="Street")
    street_number: Optional[str] = Field(None, alias="StreetNumber")
    box: Optional[str] = Field(None, alias="Box")
    zipcode: Optional[str] = Field(None, alias="Zipcode")
    city: Optional[str] = Field(None, alias="City")
    country_code: Optional[str] = Field(None, alias="CountryCode")
    
    # Structured addresses array
    addresses: Optional[List[Address]] = Field(None, alias="Addresses")
    
    # Accounting integration
    gl_account_code: Optional[str] = Field(None, alias="GLAccountCode")
    gl_default_expiry_offset: Optional[str] = Field(None, alias="GLDefaultExpiryOffset")
    nr: Optional[str] = Field(None, alias="Nr")
    external_provider_tc: Optional[str] = Field(None, alias="ExternalProviderTC")
    external_provider_id: Optional[str] = Field(None, alias="ExternalProviderID")
    
    # Party type
    party_type: Optional[str] = Field(None, alias="PartyType")

    model_config = ConfigDict(populate_by_name=True)


class PartyCreate(BaseModel):
    name: str


class PartyUpdate(BaseModel):
    """Model for updating party (customer/supplier) information.
    
    All fields are optional for PATCH operations.
    Based on Billit API patchable properties documentation.
    
    Note: Addresses can be updated via flat fields (primary address) or
    structured Addresses array. Flat fields appear to be more reliable
    for updates via PATCH operations.
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
    
    # Primary address fields (recommended for updates)
    country_code: Optional[str] = Field(None, alias="CountryCode")
    city: Optional[str] = Field(None, alias="City")
    street: Optional[str] = Field(None, alias="Street")
    street_number: Optional[str] = Field(None, alias="StreetNumber")
    zipcode: Optional[str] = Field(None, alias="Zipcode")
    box: Optional[str] = Field(None, alias="Box")
    
    # Structured addresses (may not be patchable - needs testing)
    addresses: Optional[List[Address]] = Field(None, alias="Addresses")
    
    # Other fields
    vat_liable: Optional[bool] = Field(None, alias="VATLiable")
    gl_account_code: Optional[str] = Field(None, alias="GLAccountCode")
    gl_default_expiry_offset: Optional[str] = Field(None, alias="GLDefaultExpiryOffset")
    nr: Optional[str] = Field(None, alias="Nr")
    external_provider_tc: Optional[str] = Field(None, alias="ExternalProviderTC")
    external_provider_id: Optional[str] = Field(None, alias="ExternalProviderID")

    model_config = ConfigDict(populate_by_name=True)
