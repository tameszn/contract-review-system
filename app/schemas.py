from typing import Optional
from pydantic import BaseModel,Field
from datetime import date




class Chunk(BaseModel):
    chunk_id: int
    page: int                      
    text: str
    section: Optional[str] = None 

class ContractParty(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    address: Optional[str] = None


class ContractMetadata(BaseModel):
    title: Optional[str] = None
    contract_type: Optional[str] = None

    effective_date: Optional[date] = Field(
        default=None,
        description="ISO 8601 date in YYYY-MM-DD format."
    )

    expiry_date: Optional[date] = Field(
        default=None,
        description="ISO 8601 date in YYYY-MM-DD format."
    )

    jurisdiction: Optional[str] = None
    parties: Optional[list[ContractParty]] = Field(
    default_factory=list,
    description="List of identified contract parties. Return an empty list if none are found, or null if unavailable."
    )
    contract_value: Optional[str] = None
    payment_terms: Optional[str] = None


class ExtractedClause(BaseModel):
    clause_type: str
    clause_title: Optional[str] = None
    clause_text: str
    page_number: int
    section: Optional[str] = None


class ContractExtraction(BaseModel):
    metadata: ContractMetadata
    clauses: list[ExtractedClause] = Field(default_factory=list)


class LiabilityFinding(BaseModel):
    clause_type: str = Field(
        description="Type of liability provision, such as limitation of liability, indemnity, or exclusion of damages."
    )
    risk_level: str = Field(
        description="Risk level: low, medium, high, or critical."
    )
    finding: str = Field(
        description="A concise explanation of the identified liability concern."
    )
    evidence_quote: str = Field(
        description="An exact quotation copied from the contract."
    )
    page_number: int = Field(
        description="Page number where the quoted evidence appears."
    )
    rationale: str = Field(
        description="Why this provision may create legal or commercial exposure."
    )
    recommendation: str = Field(
        description="A practical suggestion for addressing the identified concern."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the finding accurately reflects the supplied evidence."
    )


class LiabilityAnalysis(BaseModel):
    overall_assessment: str = Field(
        description="A concise overall assessment of the contract's liability provisions."
    )
    findings: list[LiabilityFinding] = Field(default_factory=list)