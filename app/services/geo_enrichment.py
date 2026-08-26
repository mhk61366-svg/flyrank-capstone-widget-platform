import httpx

def try_ip_api(ip_address: str) -> dict | None:
    try:
        resp = httpx.get(f"http://ip-api.com/json/{ip_address}", timeout=2.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return {"country": data.get("country"), "city": data.get("city")}
    except httpx.HTTPError:
        pass
    return None

def try_ipapi_co(ip_address: str) -> dict | None:
    try:
        resp = httpx.get(f"https://ipapi.co/{ip_address}/json/", timeout=2.0)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("error"):
            return {"country": data.get("country_name"), "city": data.get("city")}
    except httpx.HTTPError:
        pass
    return None

def enrich(ip_address: str) -> dict:
    if not ip_address or ip_address in ("127.0.0.1", "testclient"):
        return {"country": None, "city": None}
    result = try_ip_api(ip_address)
    if result:
        return result
    result = try_ipapi_co(ip_address)
    if result:
        return result
    return {"country": None, "city": None}