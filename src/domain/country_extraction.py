from pydantic import BaseModel, Field, field_validator
from src.utils.countries_constants import VALID_COUNTRY_NAMES, normalize_country_name

class CountryExtraction(BaseModel):
    country_name: str = Field(
        description=(
            "Full official country name in English, "
            "e.g., 'Afghan' → 'Afghanistan', 'White House' → 'United States', "
            "aliases are normalized to official names"
        )
    )
    sentiment: float = Field(
        ge=-1.0,
        le=1.0,
        description="Sentiment score from -1.0 (very negative) to 1.0 (very positive). 0 is neutral.",
    )

    @field_validator("country_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("The field cannot be empty.")
        return normalize_country_name(v)

    @field_validator("country_name")
    @classmethod
    def check_country_name(cls, v: str) -> str:
        if v not in VALID_COUNTRY_NAMES:
            raise ValueError("The country name must match the official list of countries.")
        return v