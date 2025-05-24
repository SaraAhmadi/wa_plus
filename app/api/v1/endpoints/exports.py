from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi.responses import StreamingResponse
import io

from app.dependencies import get_db, get_current_user
from app.services.data_service import DataService
from app.services.export_service import ExportService
from app.schemas.user import User as UserSchema  # For current_user type hint if needed

# Import any specific Pydantic schemas for request bodies if an export request becomes complex

router = APIRouter()


@router.get("/csv", response_class=StreamingResponse)
async def export_data_as_csv(
        # --- Common Filters (mirroring /timeseries-data or /summary-data) ---
        export_type: str = Query(...,
                                 description="Type of data to export (e.g., 'timeseries', 'summary', 'cropping_patterns')"),
        indicator_codes: Optional[List[str]] = Query(None, description="List of indicator codes"),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        reporting_unit_ids: Optional[List[int]] = Query(None, description="List of reporting unit IDs"),
        infrastructure_ids: Optional[List[int]] = Query(None, description="List of infrastructure IDs"),
        # Cropping pattern specific filters
        time_period_year: Optional[int] = Query(None, description="Year for cropping patterns"),
        time_period_season: Optional[str] = Query(None, description="Season for cropping patterns"),
        pattern_type: Optional[str] = Query(None,
                                            description="Pattern type ('Actual', 'Planned') for cropping patterns"),
        # Summary specific
        aggregation_method: Optional[str] = Query(None, description="Aggregation method for summary data"),
        # --- Dependencies ---
        db: AsyncSession = Depends(get_db),
        current_user: UserSchema = Depends(get_current_user)  # Exports are typically authenticated
):
    """
    Export currently filtered/viewed tabular data as a CSV file.
    Corresponds to SSR 8.5.5 GET /api/v1/export/csv
    The query parameters should closely match the filters available for the
    data view the user wants to export.
    """
    data_service = DataService(db)
    export_service = ExportService(db)

    data_to_export: List[Dict[str, Any]] = []
    filename_base = "waplus_export"

    # --- Logic to fetch data based on export_type ---
    if export_type.lower() == "timeseries":
        if not all([indicator_codes, start_date, end_date]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Missing required parameters for timeseries export (indicator_codes, start_date, end_date)")
        if not reporting_unit_ids and not infrastructure_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Either reporting_unit_ids or infrastructure_ids required for timeseries export.")

        data_to_export = await data_service.get_timeseries_data(
            indicator_definition_codes=indicator_codes,
            start_date=start_date,
            end_date=end_date,
            reporting_unit_ids=reporting_unit_ids,
            infrastructure_ids=infrastructure_ids
            # Add other relevant filters if needed (e.g., temporal_resolution_name)
        )
        filename_base = f"timeseries_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

    elif export_type.lower() == "summary":
        if not all([indicator_codes, start_date, end_date, aggregation_method]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Missing required parameters for summary export (indicator_codes, start_date, end_date, aggregation_method)")

        data_to_export = await data_service.get_summary_data(
            indicator_definition_codes=indicator_codes,
            time_period_start=start_date,
            time_period_end=end_date,
            reporting_unit_ids=reporting_unit_ids,
            infrastructure_ids=infrastructure_ids,
            aggregation_method=aggregation_method
        )
        filename_base = f"summary_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

    elif export_type.lower() == "cropping_patterns":
        if not all([reporting_unit_ids, time_period_year]):  # Assuming single reporting_unit_id for this export type
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Missing required parameters for cropping patterns export (reporting_unit_ids (single), time_period_year)")
        if len(reporting_unit_ids) > 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Cropping pattern export supports only a single reporting_unit_id at a time.")

        data_to_export = await data_service.get_cropping_patterns(
            reporting_unit_id=reporting_unit_ids[0],
            time_period_year=time_period_year,
            time_period_season=time_period_season,
            pattern_type=pattern_type
        )
        filename_base = f"cropping_patterns_unit{reporting_unit_ids[0]}_{time_period_year}"

    # Add more export_type conditions for financial data, infrastructure data etc.

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid export_type: {export_type}")

    if not data_to_export and data_to_export is not None:  # Explicitly check for empty list
        # Return a CSV with just headers or a message, or a 204 No Content
        # For now, let's return an empty CSV for consistency if data_service returns []
        pass  # The generate_csv_from_data handles empty data by returning an empty StringIO

    csv_buffer: io.StringIO = await export_service.generate_csv_from_data(data_to_export)

    # Set up response headers for CSV download
    response_headers = {
        "Content-Disposition": f"attachment; filename={filename_base}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    }

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),  # getvalue() to get string from StringIO
        media_type="text/csv",
        headers=response_headers
    )


@router.post("/visualization", status_code=status.HTTP_202_ACCEPTED)  # Or 200 if returning file directly
async def export_current_visualization(
        # current_user: UserSchema = Depends(get_current_user), # Usually requires auth
        # --- Request Body (as per SSR 8.5.5 POST /api/v1/export/visualization) ---
        visualization_type: str = Body(..., examples=["Chart", "Map"]),
        format: str = Body(..., examples=["PNG", "PDF"]),
        svg_data: Optional[str] = Body(None, description="Client-rendered SVG string for charts"),
        map_view_parameters: Optional[Dict[str, Any]] = Body(None,
                                                             description="Parameters for map view (bbox, layers, zoom)"),
        title: Optional[str] = Body(None),
        metadata_to_include: Optional[List[str]] = Body(None, examples=[["filters_applied", "export_date"]])
):
    """
    Export the current state of a chart or map visualization as an image (PNG) or document (PDF).
    Corresponds to SSR 8.5.5 POST /api/v1/export/visualization

    NOTE: This endpoint is largely a placeholder. True server-side rendering of complex
    client-side visualizations (SVG charts, Mapbox maps) into PNG/PDF is non-trivial.
    It might involve:
    1. Client sending fully rendered image data (e.g., base64 PNG from canvas).
    2. Server using libraries like Playwright/Puppeteer (headless browser) to render and capture.
    3. Server using SVG-to-PNG/PDF libraries (e.g., cairosvg, rsvg-convert for SVG; WeasyPrint for HTML/CSS to PDF).

    For Phase 1, client-side export (FR-044, FR-045) is more likely, and this API might
    not be strictly needed if the client handles the download directly.
    If this API *is* used, it's likely to receive already-rendered data or trigger a server-side job.
    """
    export_service = ExportService(Depends(get_db))  # DB not strictly needed for this placeholder

    if format.lower() not in ["png", "pdf"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Unsupported export format. Use 'PNG' or 'PDF'.")

    if visualization_type.lower() == "chart":
        if not svg_data and format.lower() == "png":  # Basic check
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="SVG data required for chart PNG export via server.")
        # TODO: Implement server-side SVG to PNG/PDF conversion if required
        # e.g., using cairosvg:
        # if format.lower() == "png":
        #     import cairosvg
        #     png_output = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
        #     return Response(content=png_output, media_type="image/png", headers={"Content-Disposition": ...})
        # elif format.lower() == "pdf":
        #     # SVG to PDF is more complex, might need HTML wrapping + WeasyPrint or similar
        #     pass
        pass
    elif visualization_type.lower() == "map":
        if not map_view_parameters:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Map view parameters required for map export.")
        # TODO: Implement server-side map capture (e.g., using a headless browser with Mapbox GL JS)
        pass
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported visualization type.")

    # For now, returning a placeholder response as server-side rendering is complex
    return {
        "message": f"Request to export {visualization_type} as {format} received. Server-side rendering not fully implemented.",
        "details": {
            "title": title,
            "metadata": metadata_to_include,
            "params_received": map_view_parameters or "SVG data (length)" + str(len(svg_data)) if svg_data else "None"
        }
    }
