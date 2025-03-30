# Carrier Vetting API Proxy

# 1. Overview
This is a FastAPI-based proxy service that helps vet carriers by checking various safety and authentication factors. It interfaces with the Highway API to get carrier information, and exposes a PASS/FAIL status for a given carrier, based on the conditions chosen in the `config/conditions.json` file.

# 2. Setup

The service requires three environment variables:
- HIGHWAY_API_TOKEN  # The authentication token for Highway API
- PROXY_API_KEY     # The API key that clients will use to authenticate with this proxy
- USE_STAGING       # Boolean to use Highway's staging environment (optional, defaults to false)

## Configuration

The service uses a `config/conditions.json` file to control which conditions trigger a FAIL result. The file contains two sections:

1. `phone_conditions`: Controls which phone number categories trigger a FAIL
2. `carrier_conditions`: Controls which carrier safety checks must pass

Each condition has an `active` flag (0 or 1) that determines if it's enforced. If any active condition fails, the check will return a FAIL result. If all conditions pass, the check will return a PASS result.


# 3. Usage

The API exposes a single endpoint:
GET /carrier/check

### Authentication
All requests must include an API key in the Authorization header:
Authorization: Bearer your_proxy_api_key


### Input 
The API accepts query parameters for carrier identification:
- mc_number: Motor Carrier number
- dot_number: Department of Transportation number
- phone_number: Carrier's phone number (must be in E.164 format)

You must provide exactly one of these identifiers.

### Rate Limiting
The API is rate limited to 100 requests per minute per IP address.


### Response
The API returns a JSON response with the following structure:

```json
{
  "carrier_id": "string",          // Unique identifier for the carrier (e.g. "mc_1234")
  "legal_name": "string",          // Legal business name of the carrier
  "dba_name": "string | null",     // "Doing Business As" name, if any
  "dot_number": "string",          // DOT number
  "mc_number": "string",           // MC number
  "result": "string",              // "PASS" or "FAIL"
  "reason": "string | null",       // Reason for failure, null if passed
  "phone_search_result_category": "string | null", // Phone search category if phone number provided
  "authority_assessment": {
    "rating": "string",            // Authority rating from Highway API
    "carrier_interstate_authority_check": "string", // "Active" or "Inactive"
    "broker_interstate_authority_check": "string",  // "Active" or "Inactive"
    "is_active_insurance": "boolean",              // Whether insurance is active
    "no_out_of_service_order": "boolean",          // Whether there are no out-of-service orders
    "is_satisfactory_safety_rating": "boolean",     // Whether safety rating is satisfactory
    "is_operating_status_active": "boolean",        // Whether operating status is active
    "is_inspection_history_greater_than_zero": "boolean", // Whether carrier has inspection history
    "latest_safety_rating": "string"               // Latest safety rating
  },
  "rules_assessment": {
    "overall_result": "string"     // Highway API's own assessment ("pass" or "fail")
  }
}
```

Note: The response contains two different assessment results:
1. `result`: This is the proxy's own PASS/FAIL determination based on critical safety and authority factors as described in the "How is the pass/fail determined?" section.
2. `rules_assessment.overall_result`: This is Highway API's own rules assessment which is passed through for informational purposes but does not affect our PASS/FAIL determination.


## How is the pass/fail determined?

### A. Phone Number Check
If a phone number is provided:
- Uses Highway API's rapid phone search
- FAIL is returned if the phone matches any active condition in `phone_conditions`
- Common failure cases include:
  - Phone not found
  - Phone flagged for fraud (if enabled)
  - Phone associated with identity alerts (if enabled)
  - Phone belongs to dispatcher service (if enabled)
  - Phone associated with multiple carriers (if enabled)
  - Phone belongs to blocked users/companies
  - Phone used for caller ID spoofing
  - Phone is high risk or unknown
  - Phone belongs to carrier but fails rule assessment
  - Phone belongs to carrier with incomplete rule assessment
  - Phone belongs to carrier not in broker's network

### B. MC/DOT Number Check
If MC or DOT number is provided, the system checks several critical factors:

1. Carrier must be found in Highway's database
2. Authority assessment must be available
3. All enabled carrier conditions in `conditions.json` must pass. Common checks include:
   - Insurance must be active (`is_active_insurance`)
   - No out-of-service orders (`no_out_of_service_order`)
   - Operating status must be active (`is_operating_status_active`)
   - Safety rating must be satisfactory (`is_satisfactory_safety_rating`)
   - Valid authority (`has_valid_authority`)
   - No pending revocation (`no_pending_revocation`)

The check will FAIL if:
- Carrier is not found
- Authority assessment is unavailable
- Any enabled condition in `conditions` fails  


# 4. Example Requests and Responses

Here are two example requests and their responses:

### Example 1: Successful Check (PASS)
```bash
curl -X GET "https://your-railway-app-url/carrier/check?mc_number=1515" \
-H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "carrier_id": "mc_1515",
  "legal_name": "GREYHOUND LINES INC",
  "dba_name": "BOLT BUS",
  "dot_number": "44110",
  "mc_number": "1515",
  "result": "PASS",
  "reason": null,
  "phone_search_result_category": null,
  "authority_assessment": {
    "rating": "Authorized Carrier",
    "carrier_interstate_authority_check": "Active",
    "broker_interstate_authority_check": "Inactive",
    "is_active_insurance": true,
    "no_out_of_service_order": true,
    "is_satisfactory_safety_rating": true,
    "is_operating_status_active": true,
    "is_inspection_history_greater_than_zero": true,
    "latest_safety_rating": "Satisfactory"
  },
  "rules_assessment": {
    "overall_result": "fail"
  }
}
```

### Example 2: Failed Check (FAIL)
```bash
curl -X GET "https://your-railway-app-url/carrier/check?mc_number=10101" \
-H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "carrier_id": "mc_10101",
  "legal_name": "SUPREME MOVING AND STORAGE, INC.",
  "dba_name": null,
  "dot_number": "2971099",
  "mc_number": "10101",
  "result": "FAIL",
  "reason": "Insurance not active",
  "phone_search_result_category": null,
  "authority_assessment": {
    "rating": "Not Authorized",
    "carrier_interstate_authority_check": "Inactive",
    "broker_interstate_authority_check": "Inactive",
    "is_active_insurance": false,
    "no_out_of_service_order": false,
    "is_satisfactory_safety_rating": true,
    "is_operating_status_active": false,
    "is_inspection_history_greater_than_zero": false,
    "latest_safety_rating": "Unrated"
  },
  "rules_assessment": {
    "overall_result": "fail"
  }
}
```

Note: Replace `YOUR_API_KEY` with your actual API key when making requests.

