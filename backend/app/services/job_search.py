import httpx
from app.core.config import settings

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


async def search_jobs(query: str, location: str = "", country: str = "in", page: int = 1, results_per_page: int = 10) -> list[dict]:
    """Search jobs via the Adzuna API (legitimate, ToS-compliant job search API)
    instead of scraping LinkedIn with Selenium."""
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        raise RuntimeError("Adzuna credentials not configured (ADZUNA_APP_ID / ADZUNA_APP_KEY)")

    url = f"{ADZUNA_BASE_URL}/{country}/search/{page}"
    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": query,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("results", []):
        jobs.append({
            "title": item.get("title"),
            "company": (item.get("company") or {}).get("display_name"),
            "location": (item.get("location") or {}).get("display_name"),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "description": item.get("description"),
            "url": item.get("redirect_url"),
            "created": item.get("created"),
        })
    return jobs
