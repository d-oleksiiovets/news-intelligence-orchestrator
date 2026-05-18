from pydantic import BaseModel, Field, field_validator
from typing import List

from src.domain.country_extraction import CountryExtraction

class NewsAnalysis(BaseModel):
    entities: List[CountryExtraction] = Field(
        description=(
            "List of countries involved in the news. If the news is general, use 'Global'. "
            "Common aliases are normalized to official country names."
        )
    )

    @field_validator("entities")
    @classmethod
    def check_duplicates(cls, v: List[CountryExtraction]) -> List[CountryExtraction]:
        seen_names: set[str] = set()
        for c in v:
            if c.country_name in seen_names:
                raise ValueError(f"Duplicate country name: {c.country_name}")
            seen_names.add(c.country_name)
        return v