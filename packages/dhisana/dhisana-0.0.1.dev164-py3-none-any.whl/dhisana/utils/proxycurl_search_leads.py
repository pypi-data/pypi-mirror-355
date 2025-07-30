import logging
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

from dhisana.utils.generate_structured_output_internal import get_structured_output_internal
from dhisana.utils.proxy_curl_tools import get_proxycurl_access_token
from dhisana.utils.clean_properties import cleanup_properties
from dhisana.utils.assistant_tool_tag import assistant_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyCurlSearchParams(BaseModel):
    """Subset of Proxycurl person search parameters used by this helper."""

    current_role_title: Optional[str] = None
    current_company_industry: Optional[str] = None
    current_company_employee_count_min: Optional[int] = None
    current_company_employee_count_max: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    summary: Optional[str] = None
    current_job_description: Optional[str] = None
    past_job_description: Optional[str] = None


async def _description_to_params(
    description: str, tool_config: Optional[List[Dict[str, Any]]] = None
) -> ProxyCurlSearchParams:
    """Use LLM to convert a plain-English ICP description to Proxycurl parameters."""

    system_message = (
        "You are an expert at translating a user ICP description into Proxycurl "
        "person search API parameters."
    )
    example_params = """{
        'country': 'US',
        'first_name': 'Sarah',
        'last_name': 'Jackson OR Johnson',
        'education_field_of_study': 'computer science',
        'education_degree_name': 'MBA',
        'education_school_name': 'Caltech OR Massachusetts Institute of Technology',
        'education_school_linkedin_profile_url': 'https://www.linkedin.com/school/national-university-of-singapore/',
        'current_role_title': 'founder',
        'past_role_title': 'founder',
        'current_role_before': '2019-12-30',
        'current_role_after': '2019-12-30',
        'current_company_linkedin_profile_url': 'https://www.linkedin.com/company/apple',
        'past_company_linkedin_profile_url': 'https://www.linkedin.com/company/apple',
        'current_job_description': 'education',
        'past_job_description': 'education',
        'current_company_name': 'Stripe OR Apple',
        'past_company_name': 'Stripe OR Apple',
        'linkedin_groups': 'haskell',
        'languages': 'Mandarin OR Chinese',
        'region': 'California',
        'city': 'Seattle OR Los Angeles',
        'headline': 'founder',
        'summary': 'founder',
        'industries': 'automotive',
        'interests': 'technology',
        'skills': 'accounting',
        'current_company_country': 'us',
        'current_company_region': 'United States',
        'current_company_city': 'Seattle OR Los Angeles',
        'current_company_type': 'NON_PROFIT',
        'current_company_follower_count_min': '1000',
        'current_company_follower_count_max': '1000',
        'current_company_industry': 'higher AND education',
        'current_company_employee_count_min': '1000',
        'current_company_employee_count_max': '1000',
        'current_company_description': 'medical device',
        'current_company_founded_after_year': '1999',
        'current_company_founded_before_year': '1999',
        'current_company_funding_amount_min': '1000000',
        'current_company_funding_amount_max': '1000000',
        'current_company_funding_raised_after': '2019-12-30',
        'current_company_funding_raised_before': '2019-12-30',
        'public_identifier_in_list': 'williamhgates,johnrmarty',
        'public_identifier_not_in_list': 'williamhgates,johnrmarty'
    }"""
    prompt = f"""{system_message}

Example ProxyCurlSearchParams:
{example_params}

User description:
"""{description}"""

Generate JSON with possible keys: current_role_title, current_company_industry,
current_company_employee_count_min, current_company_employee_count_max,
country, region, city. Parameters may be boolean expressions such as
"current_company_name: 'Stripe OR Apple'". Infer keywords that may appear in a
person's summary, current job description, or past job description, returning
them as summary, current_job_description, and past_job_description fields. If a
value is not explicitly specified, omit the key without making up new
parameters."""

    response, status = await get_structured_output_internal(
        prompt, ProxyCurlSearchParams, tool_config=tool_config
    )

    if status != "SUCCESS" or not response:
        logger.warning("LLM failed to parse description; using defaults")
        return ProxyCurlSearchParams()

    return response


@assistant_tool
async def proxycurl_search_leads(
    icp_description: str,
    max_entries: int = 5,
    tool_config: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Search for leads on Proxycurl based on a plain-English ICP description."""

    if not icp_description:
        logger.warning("No ICP description provided")
        return []

    params_model = await _description_to_params(icp_description, tool_config=tool_config)

    if max_entries <= 0:
        max_entries = 5
    params = params_model.model_dump(exclude_none=True)
    params["page_size"] = max_entries
    params["enrich_profiles"] = "skip"
    params["use_cache"] = "if-present"

    api_key = get_proxycurl_access_token(tool_config)
    if not api_key:
        logger.error("PROXY_CURL_API_KEY not found")
        return []

    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://nubela.co/proxycurl/api/v2/search/person"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    logger.error("Proxycurl search error %s", resp.status)
                    return []
                data = await resp.json()
    except Exception as exc:
        logger.exception("Exception during Proxycurl search: %s", exc)
        return []

    results = data.get("results") or []
    leads: List[Dict[str, Any]] = []

    for item in results[:max_entries]:
        profile = item.get("profile", {}) if isinstance(item, dict) else {}
        experiences = profile.get("experiences") or []
        org_name = ""
        org_url = ""
        if experiences:
            first_exp = experiences[0]
            org_name = first_exp.get("company", "")
            org_url = first_exp.get("company_linkedin_profile_url", "")

        lead = {
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "full_name": profile.get("full_name", ""),
            "user_linkedin_url": item.get("linkedin_profile_url"),
            "job_title": profile.get("occupation", ""),
            "organization_name": org_name,
            "organization_linkedin_url": org_url,
        }
        cleaned = cleanup_properties(lead)
        if cleaned:
            leads.append(cleaned)

    return leads

