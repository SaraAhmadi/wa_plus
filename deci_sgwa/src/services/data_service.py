from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, case, text, literal_column
from sqlalchemy.orm import selectinload, aliased

from src.database.models import (
    ReportingUnit, ReportingUnitType,
    IndicatorDefinition, IndicatorTimeseries, IndicatorCategory, UnitOfMeasurement,
    TemporalResolution, DataQualityFlag,
    Crop, CroppingPattern,
    FinancialAccount, FinancialAccountType, Currency,
    Infrastructure, InfrastructureType, OperationalStatusType,
    RasterMetadata
)
from src.schemas.indicator_timeseries import TimeseriesDataPoint  # For chart-ready data
from src.schemas.map_layer import MapLayerMetadata  # For /map_layers endpoint


# Import other relevant Pydantic schemas for request/response shaping as needed

class DataService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    # --- Reporting Unit and Related Lookups ---
    async def get_reporting_unit_by_id(self, unit_id: int) -> Optional[ReportingUnit]:
        query = select(ReportingUnit).options(selectinload(ReportingUnit.unit_type)).where(ReportingUnit.id == unit_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_reporting_units(
            self,
            unit_type_id: Optional[int] = None,
            parent_unit_id: Optional[int] = None,
            search_term: Optional[str] = None,
            offset: int = 0,
            limit: int = 100
    ) -> List[ReportingUnit]:
        query = select(ReportingUnit).options(selectinload(ReportingUnit.unit_type)).order_by(ReportingUnit.name)
        if unit_type_id:
            query = query.where(ReportingUnit.unit_type_id == unit_type_id)
        if parent_unit_id:
            query = query.where(ReportingUnit.parent_unit_id == parent_unit_id)
        if search_term:
            query = query.where(ReportingUnit.name.ilike(f"%{search_term}%"))
        query = query.offset(offset).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_reporting_unit_types(self) -> List[ReportingUnitType]:
        query = select(ReportingUnitType).order_by(ReportingUnitType.name)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    # --- Indicator Definition and Related Lookups ---
    async def get_indicator_definition_by_id(self, def_id: int) -> Optional[IndicatorDefinition]:
        query = (
            select(IndicatorDefinition)
            .options(
                selectinload(IndicatorDefinition.unit_of_measurement),
                selectinload(IndicatorDefinition.category)
            )
            .where(IndicatorDefinition.id == def_id)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_indicator_definition_by_code(self, code: str) -> Optional[IndicatorDefinition]:
        query = (
            select(IndicatorDefinition)
            .options(
                selectinload(IndicatorDefinition.unit_of_measurement),
                selectinload(IndicatorDefinition.category)
            )
            .where(IndicatorDefinition.code == code)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_indicator_definitions(
            self,
            category_id: Optional[int] = None,
            data_type_filter: Optional[str] = None,  # e.g., "time-series", "spatial_raster", "static_summary"
            offset: int = 0,
            limit: int = 100
    ) -> List[IndicatorDefinition]:
        query = (
            select(IndicatorDefinition)
            .options(
                selectinload(IndicatorDefinition.unit_of_measurement),
                selectinload(IndicatorDefinition.category)
            )
            .order_by(IndicatorDefinition.name_en)
        )
        if category_id:
            query = query.where(IndicatorDefinition.category_id == category_id)
        if data_type_filter:
            if data_type_filter == "spatial_raster":
                query = query.where(IndicatorDefinition.is_spatial_raster == True)
            # Add more conditions for other data_type_filters if needed
            # e.g., if you add a 'data_nature' field to IndicatorDefinition like 'time-series', 'summary'
        query = query.offset(offset).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_indicator_categories(self) -> List[IndicatorCategory]:
        query = select(IndicatorCategory).order_by(IndicatorCategory.name_en)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_units_of_measurement(self) -> List[UnitOfMeasurement]:
        query = select(UnitOfMeasurement).order_by(UnitOfMeasurement.name)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    # --- TimeSeries Data ---
    async def get_timeseries_data(
            self,
            indicator_definition_codes: List[str],
            start_date: datetime,
            end_date: datetime,
            reporting_unit_ids: Optional[List[int]] = None,
            infrastructure_ids: Optional[List[int]] = None,
            temporal_resolution_name: Optional[str] = None,  # e.g., "Daily", "Monthly" for filtering
            aggregate_to: Optional[str] = None  # e.g., "Monthly", "Annual", "Seasonal" for on-the-fly aggregation
    ) -> List[Dict[str, Any]]:  # Return structure flexible for charting
        """
        Fetches time-series data, potentially with on-the-fly aggregation.
        """
        # Get definition IDs from codes first
        def_query = select(IndicatorDefinition.id).where(IndicatorDefinition.code.in_(indicator_definition_codes))
        def_result = await self.db_session.execute(def_query)
        indicator_definition_ids = def_result.scalars().all()
        if not indicator_definition_ids:
            return []

        # Base query components
        fields_to_select = [
            IndicatorTimeseries.timestamp,
            IndicatorTimeseries.value_numeric.label("value"),  # Prefer numeric for aggregation
            IndicatorTimeseries.value_text.label("value_text"),
            IndicatorDefinition.code.label("indicator_code"),
            IndicatorDefinition.name_en.label("indicator_name"),
            UnitOfMeasurement.abbreviation.label("unit"),
            ReportingUnit.name.label("reporting_unit_name"),
            Infrastructure.name.label("infrastructure_name"),
            TemporalResolution.name.label("source_temporal_resolution"),
            DataQualityFlag.name.label("quality_flag")
        ]
        joins = [
            (IndicatorDefinition, IndicatorTimeseries.indicator_definition_id == IndicatorDefinition.id),
            (UnitOfMeasurement, IndicatorDefinition.unit_of_measurement_id == UnitOfMeasurement.id, True),
            # True for isouter
            (ReportingUnit, IndicatorTimeseries.reporting_unit_id == ReportingUnit.id, True),
            (Infrastructure, IndicatorTimeseries.infrastructure_id == Infrastructure.id, True),
            (TemporalResolution, IndicatorTimeseries.temporal_resolution_id == TemporalResolution.id, True),
            (DataQualityFlag, IndicatorTimeseries.quality_flag_id == DataQualityFlag.id, True),
        ]
        conditions = [
            IndicatorTimeseries.indicator_definition_id.in_(indicator_definition_ids),
            IndicatorTimeseries.timestamp.between(start_date, end_date)
        ]

        location_filters = []
        if reporting_unit_ids:
            location_filters.append(IndicatorTimeseries.reporting_unit_id.in_(reporting_unit_ids))
        if infrastructure_ids:
            location_filters.append(IndicatorTimeseries.infrastructure_id.in_(infrastructure_ids))
        if location_filters:
            conditions.append(or_(*location_filters))

        if temporal_resolution_name:  # Filter by source resolution
            # This requires joining TemporalResolution if not already for selection
            conditions.append(TemporalResolution.name == temporal_resolution_name)

        # Handle aggregation
        if aggregate_to:
            trunc_field = None
            if aggregate_to.lower() == "monthly":
                trunc_field = func.date_trunc('month', IndicatorTimeseries.timestamp)
            elif aggregate_to.lower() == "annual":
                trunc_field = func.date_trunc('year', IndicatorTimeseries.timestamp)
            elif aggregate_to.lower() == "seasonal":  # This is more complex, needs defining seasons
                # Example for meteorological seasons (DJF, MAM, JJA, SON)
                # This might require more complex CASE statements or a calendar table
                # For simplicity, not fully implemented here.
                pass

            if trunc_field is not None:
                # Replace timestamp with truncated field, add aggregate function for value
                # Remove value_text, source_temporal_resolution, quality_flag from direct selection
                # as they lose meaning when aggregated.
                fields_to_select = [
                    trunc_field.label("timestamp"),  # Aggregated timestamp (e.g., start of month/year)
                    func.avg(IndicatorTimeseries.value_numeric).label("value"),  # Example: average
                    # Keep grouping fields like indicator_code, reporting_unit_name etc.
                    IndicatorDefinition.code.label("indicator_code"),
                    IndicatorDefinition.name_en.label("indicator_name"),
                    UnitOfMeasurement.abbreviation.label("unit"),
                    ReportingUnit.name.label("reporting_unit_name"),
                    Infrastructure.name.label("infrastructure_name"),
                    literal_column(f"'{aggregate_to}'").label("aggregation_level")  # Add aggregation level info
                ]
                # Group by all non-aggregated selected fields
                group_by_fields = [
                    trunc_field,
                    IndicatorDefinition.code, IndicatorDefinition.name_en, UnitOfMeasurement.abbreviation,
                    ReportingUnit.name, Infrastructure.name
                ]
                query = select(*fields_to_select)
                for join_model, join_condition, *isouter_flag in joins:
                    isouter = isouter_flag[0] if isouter_flag else False
                    query = query.join(join_model, join_condition, isouter=isouter)
                query = query.where(and_(*conditions)).group_by(*group_by_fields).order_by(trunc_field,
                                                                                           IndicatorDefinition.code)
            else:  # No valid aggregation, proceed with raw data query
                query = select(*fields_to_select)
                for join_model, join_condition, *isouter_flag in joins:
                    isouter = isouter_flag[0] if isouter_flag else False
                    query = query.join(join_model, join_condition, isouter=isouter)
                query = query.where(and_(*conditions)).order_by(IndicatorTimeseries.timestamp, IndicatorDefinition.code)
        else:  # No aggregation, raw data query
            query = select(*fields_to_select)
            for join_model, join_condition, *isouter_flag in joins:
                isouter = isouter_flag[0] if isouter_flag else False
                query = query.join(join_model, join_condition, isouter=isouter)
            query = query.where(and_(*conditions)).order_by(IndicatorTimeseries.timestamp, IndicatorDefinition.code)

        result = await self.db_session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    async def get_summary_data(
            self,
            indicator_definition_codes: List[str],
            time_period_start: datetime,
            time_period_end: datetime,
            reporting_unit_ids: Optional[List[int]] = None,
            infrastructure_ids: Optional[List[int]] = None,
            group_by_field: Optional[str] = None,  # e.g., "crop_type", "water_source_type"
            aggregation_method: str = "Average"
    ) -> List[Dict[str, Any]]:
        # Get definition IDs from codes first
        def_query = select(IndicatorDefinition.id).where(IndicatorDefinition.code.in_(indicator_definition_codes))
        def_result = await self.db_session.execute(def_query)
        indicator_definition_ids = def_result.scalars().all()
        if not indicator_definition_ids:
            return []

        agg_func_map = {
            "Average": func.avg, "Sum": func.sum, "Min": func.min, "Max": func.max,
            "Count": func.count, "LatestValue": func.last_value  # last_value needs window function
        }
        selected_agg_func = agg_func_map.get(aggregation_method)
        if not selected_agg_func:
            raise ValueError(f"Unsupported aggregation method: {aggregation_method}")

        # Base selection
        selection = [
            IndicatorDefinition.code.label("indicator_code"),
            IndicatorDefinition.name_en.label("indicator_name"),
            UnitOfMeasurement.abbreviation.label("unit"),
            selected_agg_func(IndicatorTimeseries.value_numeric).label("aggregated_value")
        ]
        group_by_columns = [
            IndicatorDefinition.code, IndicatorDefinition.name_en, UnitOfMeasurement.abbreviation
        ]
        joins = [
            (IndicatorDefinition, IndicatorTimeseries.indicator_definition_id == IndicatorDefinition.id),
            (UnitOfMeasurement, IndicatorDefinition.unit_of_measurement_id == UnitOfMeasurement.id, True),
        ]
        conditions = [
            IndicatorTimeseries.indicator_definition_id.in_(indicator_definition_ids),
            IndicatorTimeseries.timestamp.between(time_period_start, time_period_end)
        ]

        # Handle location (reporting unit or infrastructure)
        if reporting_unit_ids:
            selection.append(ReportingUnit.name.label("location_name"))
            selection.append(ReportingUnit.id.label("location_id"))
            group_by_columns.extend([ReportingUnit.name, ReportingUnit.id])
            joins.append((ReportingUnit, IndicatorTimeseries.reporting_unit_id == ReportingUnit.id))
            conditions.append(IndicatorTimeseries.reporting_unit_id.in_(reporting_unit_ids))
        elif infrastructure_ids:
            selection.append(Infrastructure.name.label("location_name"))
            selection.append(Infrastructure.id.label("location_id"))
            group_by_columns.extend([Infrastructure.name, Infrastructure.id])
            joins.append((Infrastructure, IndicatorTimeseries.infrastructure_id == Infrastructure.id))
            conditions.append(IndicatorTimeseries.infrastructure_id.in_(infrastructure_ids))
        # Else, data is not location specific (e.g. national average)

        # TODO: Handle group_by_field (e.g., "crop_type") - this would require further joins
        # (e.g., to CroppingPattern then to Crop if indicator is crop-related)
        # and adding that field to selection and group_by_columns.

        query = select(*selection)
        for join_model, join_condition, *isouter_flag in joins:
            isouter = isouter_flag[0] if isouter_flag else False
            query = query.join(join_model, join_condition, isouter=isouter)

        query = query.where(and_(*conditions)).group_by(*group_by_columns).order_by(
            *group_by_columns[:1])  # Order by first grouping col

        result = await self.db_session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    # --- Cropping Pattern Data ---
    async def get_cropping_patterns(
            self,
            reporting_unit_id: int,
            time_period_year: int,
            time_period_season: Optional[str] = None,
            pattern_type: Optional[str] = None  # "Actual", "Planned"
    ) -> List[Dict[str, Any]]:  # Return dicts for flexibility
        query = (
            select(
                Crop.name_en.label("crop_name"), Crop.code.label("crop_code"),
                CroppingPattern.area_cultivated_ha, CroppingPattern.area_proposed_ha,
                CroppingPattern.yield_actual_ton_ha, CroppingPattern.yield_proposed_ton_ha,
                CroppingPattern.water_allocation_mcm, CroppingPattern.water_consumed_actual_mcm,
                CroppingPattern.data_type, CroppingPattern.time_period_season
            )
            .join(Crop, CroppingPattern.crop_id == Crop.id)
            .where(
                CroppingPattern.reporting_unit_id == reporting_unit_id,
                CroppingPattern.time_period_year == time_period_year
            )
        )
        if time_period_season:
            query = query.where(CroppingPattern.time_period_season == time_period_season)
        if pattern_type:
            query = query.where(CroppingPattern.data_type == pattern_type)

        result = await self.db_session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    # --- Financial Data ---
    async def get_financial_accounts_summary(
            self,
            start_date: datetime,
            end_date: datetime,
            reporting_unit_id: Optional[int] = None,
            infrastructure_id: Optional[int] = None,
            group_by_account_type: bool = False
    ) -> List[Dict[str, Any]]:
        selection = [
            func.sum(FinancialAccount.amount).label("total_amount"),
            Currency.code.label("currency_code")
        ]
        group_by_cols = [Currency.code]
        conditions = [FinancialAccount.transaction_date.between(start_date, end_date)]
        joins = [
            (FinancialAccountType, FinancialAccount.financial_account_type_id == FinancialAccountType.id),
            (Currency, FinancialAccount.currency_id == Currency.id)
        ]

        # Main category (cost/revenue)
        selection.append(FinancialAccountType.is_cost.label("is_cost"))
        group_by_cols.append(FinancialAccountType.is_cost)

        if group_by_account_type:
            selection.extend([
                FinancialAccountType.name.label("account_type_name"),
                FinancialAccountType.category.label("account_category")
            ])
            group_by_cols.extend([FinancialAccountType.name, FinancialAccountType.category])

        if reporting_unit_id:
            selection.append(ReportingUnit.name.label("reporting_unit_name"))
            group_by_cols.append(ReportingUnit.name)
            joins.append((ReportingUnit, FinancialAccount.reporting_unit_id == ReportingUnit.id, True))
            conditions.append(FinancialAccount.reporting_unit_id == reporting_unit_id)
        if infrastructure_id:
            selection.append(Infrastructure.name.label("infrastructure_name"))
            group_by_cols.append(Infrastructure.name)
            joins.append((Infrastructure, FinancialAccount.infrastructure_id == Infrastructure.id, True))
            conditions.append(FinancialAccount.infrastructure_id == infrastructure_id)

        query = select(*selection)
        for join_model, join_condition, *isouter_flag in joins:
            isouter = isouter_flag[0] if isouter_flag else False
            query = query.join(join_model, join_condition, isouter=isouter)

        query = query.where(and_(*conditions)).group_by(*group_by_cols).order_by(FinancialAccountType.is_cost.desc(),
                                                                                 *group_by_cols[1:])

        result = await self.db_session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    async def get_water_tariffs(
            self,
            reporting_unit_id: Optional[int] = None,
            crop_code: Optional[str] = None,
            water_use_sector: Optional[str] = None,
            # Need a way to model this (e.g., in FinancialAccountType name or a dedicated field)
            year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        # This is highly dependent on how tariffs are stored.
        # Assuming tariffs are specific types of FinancialAccount entries (revenues)
        # or a dedicated "Tariffs" table.
        # For this example, let's assume they are FinancialAccountType revenues.
        query = (
            select(
                FinancialAccountType.name.label("tariff_name"),
                FinancialAccount.amount.label("value"),  # This might be amount per unit area/volume
                Currency.code.label("currency_code"),
                FinancialAccount.description.label("description"),  # e.g. "per hectare", "per m3"
                # ReportingUnit.name.label("reporting_unit_name"),
                # Crop.name_en.label("crop_name")
            )
            .join(FinancialAccountType, FinancialAccount.financial_account_type_id == FinancialAccountType.id)
            .join(Currency, FinancialAccount.currency_id == Currency.id)
            .where(FinancialAccountType.is_cost == False)  # It's a revenue
            # A more specific filter based on FinancialAccountType.name or category for "Tariff"
            .where(FinancialAccountType.name.ilike("%tariff%"))  # Example
        )
        # Add filters for reporting_unit_id, crop_code (via join), sector, year (from transaction_date)
        # This query needs significant refinement based on actual tariff data structure.
        # For brevity, not fully implemented here.
        # result = await self.db_session.execute(query)
        # return [dict(row) for row in result.mappings().all()]
        return [{"message": "Tariff data retrieval needs specific data model for tariffs"}]

    async def get_non_revenue_water_data(
            self,
            reporting_unit_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        # This requires specific indicators for "Water Supplied" and "Water Billed/Consumed Accounted"
        # Let's assume codes: 'WATER_SUPPLIED_VOL', 'WATER_BILLED_VOL'
        supplied_query = (
            select(func.sum(IndicatorTimeseries.value_numeric).label("supplied_volume"))
            .join(IndicatorDefinition)
            .where(IndicatorDefinition.code == 'WATER_SUPPLIED_VOL')  # Example code
            .where(IndicatorTimeseries.reporting_unit_id == reporting_unit_id)
            .where(IndicatorTimeseries.timestamp.between(start_date, end_date))
        )
        billed_query = (
            select(func.sum(IndicatorTimeseries.value_numeric).label("billed_volume"))
            .join(IndicatorDefinition)
            .where(IndicatorDefinition.code == 'WATER_BILLED_VOL')  # Example code
            .where(IndicatorTimeseries.reporting_unit_id == reporting_unit_id)
            .where(IndicatorTimeseries.timestamp.between(start_date, end_date))
        )
        supplied_vol_res = await self.db_session.execute(supplied_query)
        billed_vol_res = await self.db_session.execute(billed_query)
        supplied_volume = supplied_vol_res.scalar_one_or_none() or 0
        billed_volume = billed_vol_res.scalar_one_or_none() or 0

        if supplied_volume > 0:
            nrw_volume = supplied_volume - billed_volume
            nrw_percentage = (nrw_volume / supplied_volume) * 100 if supplied_volume else 0
            return {
                "supplied_volume": supplied_volume,
                "billed_volume": billed_volume,
                "nrw_volume": nrw_volume,
                "nrw_percentage": nrw_percentage,
                "unit": "MCM"  # Assume unit based on indicator definitions
            }
        return None

    # --- Map Layers Metadata ---
    async def get_map_layers_metadata(
            self,
            reporting_unit_id: Optional[int] = None,
            indicator_definition_code: Optional[str] = None,
            layer_type: Optional[str] = None  # e.g., "Raster", "VectorChoropleth"
    ) -> List[MapLayerMetadata]:
        """
        Get metadata about available map layers from RasterMetadata table.
        (Corresponds to API SSR 8.5.2 /map_layers)
        This assumes RasterMetadata primarily feeds this. Vector layers might come
        from ReportingUnit geometries styled by an indicator, or a dedicated VectorLayerMetadata table.
        """
        query = (
            select(
                RasterMetadata.layer_name_geoserver.label("layer_id"),  # Use this as unique layer_id
                IndicatorDefinition.name_en.label("title"),
                RasterMetadata.description.label("abstract"),
                RasterMetadata.geoserver_workspace,
                RasterMetadata.layer_name_geoserver,  # Explicitly select again
                literal_column("'WMS'").label("service_type"),  # Assume WMS for raster, adjust if WMTS/WFS
                # Construct service_endpoint based on config - this part is tricky as GeoServer URL is in config
                # literal_column(f"{settings.GEOSERVER_URL}/wms").label("service_endpoint"), # Requires settings
                IndicatorDefinition.code.label("associated_indicator_code"),
                RasterMetadata.default_style_name,
                # legend_url might be derived or stored
                RasterMetadata.timestamp_valid_start.label("temporal_validity_start"),
                RasterMetadata.timestamp_valid_end.label("temporal_validity_end"),
                RasterMetadata.spatial_resolution_desc
            )
            .join(IndicatorDefinition, RasterMetadata.indicator_definition_id == IndicatorDefinition.id)
        )

        if indicator_definition_code:
            query = query.where(IndicatorDefinition.code == indicator_definition_code)
        # Filtering by reporting_unit_id for raster layers is complex as rasters might span units
        # or not be directly tied to one in RasterMetadata. This needs careful thought on data model.
        # If layer_type is used, you might filter on IndicatorDefinition.is_spatial_raster or a new field.

        result = await self.db_session.execute(query)

        # Construct full service_endpoint using settings.GEOSERVER_URL here
        # This is a simplification; actual OGC endpoint construction is more nuanced
        from src.settings.config import settings  # Import locally for this construction
        base_geoserver_url = str(settings.GEOSERVER_URL).rstrip(
            '/') if settings.GEOSERVER_URL else "http://geoserver:8080/geoserver"

        layers = []
        for row_mapping in result.mappings().all():
            row_dict = dict(row_mapping)
            # Example: Assume WMS for raster layers
            row_dict[
                "service_endpoint"] = f"{base_geoserver_url}/{row_dict['geoserver_workspace']}/wms" if row_dict.get(
                'geoserver_workspace') else f"{base_geoserver_url}/wms"
            row_dict["service_type"] = "WMS"  # Or determine based on layer properties
            # If you store vector layer metadata differently, you'd UNION or combine queries here
            try:
                layers.append(MapLayerMetadata(**row_dict))
            except Exception as e:
                print(f"Error creating MapLayerMetadata from row: {row_dict} - {e}")  # For debugging
                # Skip problematic rows or handle error
        return layers

    # --- Infrastructure ---
    async def get_infrastructure_items(
            self,
            infra_type_id: Optional[int] = None,
            reporting_unit_id: Optional[int] = None,
            operational_status_id: Optional[int] = None,
            offset: int = 0,
            limit: int = 100
    ) -> List[Infrastructure]:
        query = (
            select(Infrastructure)
            .options(
                selectinload(Infrastructure.infrastructure_type),
                selectinload(Infrastructure.operational_status),
                selectinload(Infrastructure.reporting_unit).selectinload(ReportingUnit.unit_type),  # Nested load
                selectinload(Infrastructure.capacity_unit)
            )
            .order_by(Infrastructure.name)
        )
        if infra_type_id:
            query = query.where(Infrastructure.infrastructure_type_id == infra_type_id)
        if reporting_unit_id:
            query = query.where(Infrastructure.reporting_unit_id == reporting_unit_id)
        if operational_status_id:
            query = query.where(Infrastructure.operational_status_id == operational_status_id)

        query = query.offset(offset).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_infrastructure_types(self) -> List[InfrastructureType]:
        query = select(InfrastructureType).order_by(InfrastructureType.name)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_operational_status_types(self) -> List[OperationalStatusType]:
        query = select(OperationalStatusType).order_by(OperationalStatusType.name)
        result = await self.db_session.execute(query)
        return result.scalars().all()