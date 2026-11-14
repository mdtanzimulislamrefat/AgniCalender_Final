"""Harmonized MODIS + VIIRS burning activity calendar (precomputed).

Serves backend/data/output/harmonized_monthly.json, produced by
``python -m backend.processing.harmonize`` from real NASA FIRMS yearly
country files. If the file has not been computed yet, this endpoint
answers 503 with the command to run instead of inventing numbers.
"""
import json

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import current_user
from backend.paths import OUTPUT_DIR

router = APIRouter(prefix='/v1/harmonized', tags=['harmonized'],
                   dependencies=[Depends(current_user)])

OUTPUT_FILE = OUTPUT_DIR / 'harmonized_monthly.json'


@router.get('/calendar')
def harmonized_calendar():
    """Monthly harmonized fire events: raw vs deduplicated counts, overlap
    share, median FRP, climatology anomalies and critical months.

    The calendar is precomputed, not calculated per request; see
    backend/data/output/HARMONIZATION_METHOD.md for the method.
    """
    if not OUTPUT_FILE.exists():
        raise HTTPException(
            503,
            'Harmonized calendar has not been computed yet. Run: '
            'python -m backend.processing.harmonize --years 2003-2024 '
            '--products modis,viirs-snpp,viirs-jpss1')
    return json.loads(OUTPUT_FILE.read_text())
