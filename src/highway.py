import aiohttp
from src.models import HighwayPhoneStatusRapid, HighwayCarrier

class Highway:
    def __init__(self, token: str, staging: bool = False):
        self.token = token
        base_url = "https://staging.highway.com" if staging else "https://highway.com"
        self._base_url = f"{base_url}/core/connect/external_api/v1/carriers"

    async def find_carrier_fast(self, body: dict) -> HighwayPhoneStatusRapid:
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self._base_url}/phone_search_rapid_check"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                if resp.status == 404:
                    return []
                elif resp.status != 200:
                    raise Exception(await resp.text())
                response = await resp.json()
                return HighwayPhoneStatusRapid.model_validate(response)

    async def get_carrier_by_mc(self, mc_number: str) -> HighwayCarrier:
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_url}/mc/{mc_number}/by_identifier",
                headers=headers,
            ) as resp:
                if resp.status == 404:
                    return []
                elif resp.status < 200 or resp.status >= 300:
                    raise Exception(await resp.text())
                response = await resp.json()
                return HighwayCarrier.model_validate(response)

    async def find_carrier_by_dot(self, dot_number: str) -> HighwayCarrier:
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_url}/DOT/{dot_number}/by_identifier",
                headers=headers,
            ) as resp:
                if resp.status == 404:
                    return []
                elif resp.status < 200 or resp.status >= 300:
                    raise Exception(await resp.text())
                response = await resp.json()
                return HighwayCarrier.model_validate(response)