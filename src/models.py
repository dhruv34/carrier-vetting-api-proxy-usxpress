from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


PhoneSearchResultCategory = Literal[
    "found_phone_flagged_for_fraud",
    "found_phone_of_carrier_with_identity_alert",
    "found_phone_of_dispatcher_service",
    "found_phone_associated_with_one_carrier_and_passing_rule_assessment",
    "found_phone_associated_with_one_carrier_and_failing_rule_assessment",
    "found_phone_associated_with_one_carrier_and_incomplete_rule_assessment",
    "found_phone_associated_with_one_carrier_and_not_in_brokers_network",
    "found_phone_associated_with_multiple_carriers",
    "found_phone_of_blocked_user_or_company",
    "caller_id_spoofing_attempt",
    "known_phone_not_belonging_to_carrier",
    "phone_number_not_known_and_high_risk",
    "phone_number_not_known",
]

class HighwayPhoneStatusRapid(BaseModel):
    phone_search_result_category: Optional[PhoneSearchResultCategory] = None

class HighwayCarrierAuthorityAssessment(BaseModel):
    rating: Optional[str] = None
    carrier_interstate_authority_check: Optional[str] = None
    broker_interstate_authority_check: Optional[str] = None
    is_active_insurance: Optional[bool] = True
    no_out_of_service_order: Optional[bool] = True
    is_satisfactory_safety_rating: Optional[bool] = True
    is_operating_status_active: Optional[bool] = True
    is_inspection_history_greater_than_zero: Optional[bool] = True
    latest_safety_rating: Optional[str] = None

class HighwayCarrierRulesAssessment(BaseModel):
    overall_result: Optional[str] = None

class HighwayCarrier(BaseModel):
    id: Optional[str] = None
    legal_name: Optional[str] = None
    dba_name: Optional[str] = None
    dot_number: Optional[str] = None
    mc_number: Optional[str] = None
    authority_assessment: Optional[HighwayCarrierAuthorityAssessment] = None
    rules_assessment: Optional[HighwayCarrierRulesAssessment] = None

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value: any):
        if not value:
            return None
        return str(value)

    @field_validator("mc_number", "dot_number", mode="before")
    @classmethod
    def validate_numbers(cls, value: any) -> str:
        if not value:
            return value
        return str(value).lstrip("0")

class CarrierCheckResponse(BaseModel):
    carrier_id: Optional[str] = Field(None, description="Carrier identifier")
    legal_name: Optional[str] = Field(None, description="Legal name of the carrier")
    dba_name: Optional[str] = Field(None, description="DBA name of the carrier")
    dot_number: Optional[str] = Field(None, description="DOT number")
    mc_number: Optional[str] = Field(None, description="MC number")
    result: str = Field(..., description="PASS or FAIL")
    reason: Optional[str] = Field(None, description="Reason for failure if applicable")
    phone_search_result_category: Optional[str] = Field(None, description="Phone search result category from Highway")
    authority_assessment: Optional[dict] = Field(None, description="Authority assessment details")
    rules_assessment: Optional[dict] = Field(None, description="Rules assessment details")
