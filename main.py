from fastapi import FastAPI, HTTPException, Depends, Header, Request
from typing import Optional
import os
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import aiohttp
from src.highway import Highway
from src.models import CarrierCheckResponse
import json


load_dotenv()

# Configuration
HIGHWAY_API_TOKEN = os.getenv("HIGHWAY_API_TOKEN")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
USE_STAGING = os.getenv("USE_STAGING", "false").lower() == "true"

# Initialize FastAPI with rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Carrier Vetting API Proxy")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize Highway client
highway_client = Highway(token=HIGHWAY_API_TOKEN, staging=USE_STAGING)

async def verify_api_key(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header. Must use Bearer token"
        )
    
    token = authorization.replace("Bearer ", "")
    if token != PROXY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

def load_conditions():
    """Load conditions from JSON file"""
    with open('config/conditions.json') as f:
        return json.load(f)
    
conditions = load_conditions()

def assess_phone_status(status):
    """Evaluate phone status and return pass/fail with reason"""
    if not status or status == []:
        return "FAIL", "Phone number not found"
    
    if not hasattr(status, 'phone_search_result_category'):
        return "FAIL", "Invalid response from carrier search"

    # Fail if phone number is not known
    if status.phone_search_result_category == "phone_number_not_known":
        return "FAIL", "Phone number not known"

    phone_conditions = {
        cond["flag"]: cond["active"] 
        for cond in conditions["phone_conditions"]
    }

    # Check active conditions
    if status.phone_search_result_category in phone_conditions:
        if phone_conditions[status.phone_search_result_category] == 1:
            return "FAIL", f"Phone category: {status.phone_search_result_category}"
    
    # Pass if no active conditions are triggered
    return "PASS", None

def assess_mc_carrier_status(carrier):
    """Evaluate MC carrier status and return pass/fail with reason"""
    if not carrier or carrier == []:
        return "FAIL", "Carrier not found"
    
    if not carrier.authority_assessment:
        return "FAIL", "No authority assessment available"
    
    carrier_conditions = { 
        cond["flag"]: cond["active"] 
    for cond in conditions["carrier_conditions"]
    }
    
    # Check each active condition
    for flag, active in carrier_conditions.items():
        if active == 1:
            if not getattr(carrier.authority_assessment, flag, True):
                return "FAIL", f"Failed condition: {flag}"
    
    return "PASS", None

def assess_dot_carrier_status(carrier):
    """Evaluate DOT carrier status and return pass/fail with reason"""
    # Using same logic as MC assessment since requirements are identical
    return assess_mc_carrier_status(carrier)

@app.get("/carrier/check", response_model=CarrierCheckResponse)
@limiter.limit("100/minute")
async def check_carrier(
    request: Request,
    mc_number: Optional[str] = None,
    dot_number: Optional[str] = None,
    phone_number: Optional[str] = None,
    token: str = Depends(verify_api_key)
):
    if not any([mc_number, dot_number, phone_number]):
        raise HTTPException(
            status_code=400,
            detail="Must provide either mc_number, dot_number, or phone_number"
        )

    try:
        if phone_number:
            # Format the phone number parameter correctly for Highway API
            status = await highway_client.find_carrier_fast({"phone_e164": phone_number})
            result, reason = assess_phone_status(status)
            return CarrierCheckResponse(
                result=result,
                reason=reason,
                phone_search_result_category=status.phone_search_result_category if status else None
            )

        if mc_number:
            carrier = await highway_client.get_carrier_by_mc(mc_number)
            result, reason = assess_mc_carrier_status(carrier)
            return CarrierCheckResponse(
                carrier_id=f"mc_{mc_number}" if carrier != [] else None,
                legal_name=carrier.legal_name if carrier != [] else None,
                dba_name=carrier.dba_name if carrier != [] else None,
                dot_number=carrier.dot_number if carrier != [] else None,
                mc_number=carrier.mc_number if carrier != [] else None,
                result=result,
                reason=reason,
                authority_assessment=carrier.authority_assessment.model_dump() if carrier != [] and carrier.authority_assessment else None,
                rules_assessment=carrier.rules_assessment.model_dump() if carrier != [] and carrier.rules_assessment else None
            )

        if dot_number:
            carrier = await highway_client.find_carrier_by_dot(dot_number)
            result, reason = assess_dot_carrier_status(carrier)
            return CarrierCheckResponse(
                carrier_id=f"dot_{dot_number}" if carrier != [] else None,
                legal_name=carrier.legal_name if carrier != [] else None,
                dba_name=carrier.dba_name if carrier != [] else None,
                dot_number=carrier.dot_number if carrier != [] else None,
                mc_number=carrier.mc_number if carrier != [] else None,
                result=result,
                reason=reason,
                authority_assessment=carrier.authority_assessment.model_dump() if carrier != [] and carrier.authority_assessment else None,
                rules_assessment=carrier.rules_assessment.model_dump() if carrier != [] and carrier.rules_assessment else None
            )

    except Exception as e:
        error_message = str(e)
        if "401" in error_message:
            raise HTTPException(
                status_code=500,
                detail="Failed to authenticate with Highway API. Please check HIGHWAY_API_TOKEN."
            )
        print(f"Error processing request: {error_message}")
        raise HTTPException(status_code=500, detail=error_message) 