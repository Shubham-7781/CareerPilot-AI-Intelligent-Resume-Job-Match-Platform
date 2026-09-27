from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user
from app.models.user import User
from app.services.job_search import search_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=2, description="Job title or keywords"),
    location: str = Query("", description="City or region"),
    country: str = Query("in", description="Two-letter country code"),
    page: int = Query(1, ge=1, le=20),
    current_user: User = Depends(get_current_user),
):
    try:
        results = await search_jobs(q, location, country, page)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Job search provider error")

    return {"query": q, "location": location, "count": len(results), "results": results}
