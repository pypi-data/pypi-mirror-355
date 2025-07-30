from pydantic import BaseModel


class CompanyRegister(BaseModel):
    """Model for registering a company."""

    name: str
