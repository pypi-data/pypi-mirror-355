from pydantic import Field
from typing import Optional, Dict, Any

from .base import WeaknessBase


class RelatedWeakness(WeaknessBase):
    """A related weakness reference"""
    nature: str = Field(..., alias="Nature")
    cwe_id: str = Field(..., alias="CWE_ID")
    view_id: Optional[str] = Field(None, alias="View_ID")
    ordinal: Optional[str] = Field(None, alias="Ordinal")


class Weakness(WeaknessBase):
    """A CWE weakness entry"""
    id: int = Field(..., alias="ID")
    name: str = Field(..., alias="Name")
    abstraction: str = Field(..., alias="Abstraction")
    structure: str = Field(..., alias="Structure")
    status: str = Field(..., alias="Status")
    description: str = Field(..., alias="Description")

    # Optional fields - we don't model the full structure to keep it simple
    extended_description: Optional[str] = Field(None, alias="Extended_Description")
    likelihood_of_exploit: Optional[str] = Field(None, alias="Likelihood_Of_Exploit")

    # We'll store the raw data for these complex fields
    related_weaknesses: Optional[Dict[str, Any]] = Field(None, alias="Related_Weaknesses")
    applicable_platforms: Optional[Dict[str, Any]] = Field(None, alias="Applicable_Platforms")
    background_details: Optional[Dict[str, Any]] = Field(None, alias="Background_Details")
    modes_of_introduction: Optional[Dict[str, Any]] = Field(None, alias="Modes_Of_Introduction")
    common_consequences: Optional[Dict[str, Any]] = Field(None, alias="Common_Consequences")
    detection_methods: Optional[Dict[str, Any]] = Field(None, alias="Detection_Methods")
    potential_mitigations: Optional[Dict[str, Any]] = Field(None, alias="Potential_Mitigations")
    demonstrative_examples: Optional[Dict[str, Any]] = Field(None, alias="Demonstrative_Examples")
    observed_examples: Optional[Dict[str, Any]] = Field(None, alias="Observed_Examples")
    references: Optional[Dict[str, Any]] = Field(None, alias="References")
    mapping_notes: Optional[Dict[str, Any]] = Field(None, alias="Mapping_Notes")
    content_history: Optional[Dict[str, Any]] = Field(None, alias="Content_History")
