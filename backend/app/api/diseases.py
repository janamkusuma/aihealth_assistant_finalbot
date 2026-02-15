# backend/app/api/diseases.py

from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.api.disease_data import DISEASES

router = APIRouter(prefix="/diseases", tags=["Diseases"])


@router.get("/list")
def list_diseases(q: str = "", category: str = "All", user=Depends(get_current_user)):
    q = (q or "").lower().strip()
    category = (category or "All").strip()

    out = []
    for d in DISEASES:
        if category != "All" and d["category"] != category:
            continue
        if q and q not in d["name"].lower():
            continue
        out.append(
            {
                "id": d["id"],
                "name": d["name"],
                "category": d["category"],
                "image": d.get("image", ""),
            }
        )
    return out


@router.get("/{disease_id}")
def disease_detail(disease_id: int, user=Depends(get_current_user)):
    for d in DISEASES:
        if d["id"] == disease_id:
            return d
    raise HTTPException(status_code=404, detail="Disease not found")
