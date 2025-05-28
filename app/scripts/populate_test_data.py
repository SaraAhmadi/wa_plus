import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import text as sql_text  # For ST_GeomFromEWKT
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, List, Any, Dict, Type, TypeVar

# Adjust path if necessary to import 'app' modules
import sys
import os

from datetime import datetime, timezone
def get_utc_now(): return datetime.utcnow()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.database.session import AsyncSessionFactory
from app.database.models.base_model import Base
from app.database.models import (
    Permission, Role,
    ReportingUnitType, ReportingUnit,
    UnitOfMeasurement, TemporalResolution, DataQualityFlag,
    IndicatorCategory, IndicatorDefinition, IndicatorTimeseries,
    RasterMetadata,
    Crop, CroppingPattern,
    InfrastructureType, OperationalStatusType, Infrastructure,
    Currency, FinancialAccountType, FinancialAccount
)

# Utility to get current UTC time for explicit created_at/updated_at if needed
# from app.utils.common_helpers import get_utc_now # Assuming you have this

ModelType = TypeVar("ModelType", bound=Base)


# --- Generic Helper Function ---
async def get_or_create(session: AsyncSession, model_cls: Type[ModelType], defaults: Optional[Dict[str, Any]] = None,
                        **kwargs: Any) -> tuple[ModelType, bool]:
    stmt = select(model_cls).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalars().first()

    created = False
    if not instance:
        params = {**kwargs, **(defaults or {})}
        instance = model_cls(**params)
        session.add(instance)
        print(f"Creating {model_cls.__name__}: {kwargs}")
        created = True
    else:
        print(f"{model_cls.__name__} with {kwargs} already exists (ID: {instance.id}).")

    return instance, created


# --- Specific Get or Create Helpers ---
async def get_or_create_permission(session: AsyncSession, name: str, description: Optional[str] = None) -> Permission:
    instance, _ = await get_or_create(session, Permission, name=name, defaults={"description": description})
    return instance


async def get_or_create_role(session: AsyncSession, name: str, description: Optional[str] = None,
                             permissions_to_assign: Optional[List[Permission]] = None) -> Role:
    stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == name)
    result = await session.execute(stmt)
    role_instance = result.scalars().first()

    if not role_instance:
        role_instance = Role(name=name, description=description)
        session.add(role_instance)
        await session.flush()
        print(f"Created Role: {name} with ID {role_instance.id}")
        # Explicitly refresh 'permissions' collection for the new role
        await session.refresh(role_instance, attribute_names=['permissions'])
        print(f"Refreshed 'permissions' collection for new role '{role_instance.name}'.")
    else:
        print(f"Role '{name}' (ID: {role_instance.id}) already exists. Permissions eager-loaded.")

    if permissions_to_assign:
        current_assigned_permission_ids = {p.id for p in role_instance.permissions if p.id is not None}
        needs_flush = False
        for perm_obj in permissions_to_assign:
            if perm_obj.id is None:
                print(f"Warning: Permission '{perm_obj.name}' has no ID. Ensure flush after creation.")
                continue
            if perm_obj.id not in current_assigned_permission_ids:
                role_instance.permissions.append(perm_obj)
                needs_flush = True
                print(f"Queueing perm '{perm_obj.name}' for role '{role_instance.name}'.")
        if needs_flush:
            session.add(role_instance)
            await session.flush()
            print(f"Flushed permission assignments for role '{role_instance.name}'.")
    return role_instance


async def get_or_create_reporting_unit_type(session: AsyncSession, name: str,
                                            description: Optional[str] = None) -> ReportingUnitType:
    instance, _ = await get_or_create(session, ReportingUnitType, name=name, defaults={"description": description})
    return instance


async def get_or_create_reporting_unit(
        session: AsyncSession, name: str, code: str, unit_type_id: int,
        parent_unit_id: Optional[int] = None, description: Optional[str] = None,
        area_sqkm: Optional[float] = None, geom_wkt: Optional[str] = None
) -> ReportingUnit:
    defaults = {"name": name, "unit_type_id": unit_type_id, "parent_unit_id": parent_unit_id,
                "description": description, "area_sqkm": area_sqkm}
    instance, created = await get_or_create(session, ReportingUnit, code=code, defaults=defaults)
    if geom_wkt and (created or not instance.geom):
        try:
            ewkt_with_srid = geom_wkt
            if not geom_wkt.upper().startswith("SRID="): ewkt_with_srid = f"SRID=4326;{geom_wkt}"
            await session.execute(sql_text("UPDATE reporting_units SET geom = ST_GeomFromEWKT(:wkt) WHERE id = :id"),
                                  {"wkt": ewkt_with_srid, "id": instance.id})
            print(f"Set/Updated geom for ReportingUnit {code} using WKT.")
        except Exception as e:
            print(f"Error setting geom for RU {code}: {e}")
    return instance


async def get_or_create_unit_of_measurement(session: AsyncSession, name: str, abbreviation: str,
                                            description: Optional[str] = None) -> UnitOfMeasurement:
    instance, _ = await get_or_create(session, UnitOfMeasurement, abbreviation=abbreviation,
                                      defaults={"name": name, "description": description})
    return instance


async def get_or_create_temporal_resolution(session: AsyncSession, name: str) -> TemporalResolution:
    instance, _ = await get_or_create(session, TemporalResolution, name=name)
    return instance


async def get_or_create_data_quality_flag(session: AsyncSession, name: str,
                                          description: Optional[str] = None) -> DataQualityFlag:
    instance, _ = await get_or_create(session, DataQualityFlag, name=name, defaults={"description": description})
    return instance


async def get_or_create_indicator_category(session: AsyncSession, name_en: str,
                                           name_local: Optional[str] = None) -> IndicatorCategory:
    instance, _ = await get_or_create(session, IndicatorCategory, name_en=name_en, defaults={"name_local": name_local})
    return instance


async def get_or_create_indicator_definition(
        session: AsyncSession, code: str, name_en: str, data_type: str,
        unit_of_measurement_id: Optional[int] = None, category_id: Optional[int] = None,
        name_local: Optional[str] = None, description_en: Optional[str] = None,
        description_local: Optional[str] = None, wa_sheet_reference: Optional[str] = None,
        is_spatial_raster: bool = False) -> IndicatorDefinition:
    defaults = {"name_en": name_en, "name_local": name_local, "description_en": description_en,
                "description_local": description_local, "data_type": data_type,
                "unit_of_measurement_id": unit_of_measurement_id, "category_id": category_id,
                "wa_sheet_reference": wa_sheet_reference, "is_spatial_raster": is_spatial_raster}
    instance, _ = await get_or_create(session, IndicatorDefinition, code=code, defaults=defaults)
    return instance


async def create_indicator_timeseries_entry(
        session: AsyncSession, indicator_definition_id: int, timestamp: datetime, value_numeric: Optional[float] = None,
        reporting_unit_id: Optional[int] = None, infrastructure_id: Optional[int] = None,
        value_text: Optional[str] = None, temporal_resolution_id: Optional[int] = None,
        quality_flag_id: Optional[int] = None, comments: Optional[str] = None
) -> IndicatorTimeseries:
    now_utc = get_utc_now()
    # If session timezone is set to UTC, model defaults for created_at/updated_at should be fine
    # No need to explicitly set them here if `connect_args` in session.py is working.
    instance = IndicatorTimeseries(
        indicator_definition_id=indicator_definition_id, reporting_unit_id=reporting_unit_id,
        infrastructure_id=infrastructure_id, timestamp=timestamp, created_at=now_utc,
        updated_at=now_utc, value_numeric=value_numeric,
        value_text=value_text, temporal_resolution_id=temporal_resolution_id,
        quality_flag_id=quality_flag_id, comments=comments
    )
    session.add(instance)
    print(f"Adding IndicatorTimeseries for ind_def_id {indicator_definition_id} at {timestamp}")
    return instance


async def get_or_create_raster_metadata(session: AsyncSession, layer_name_geoserver: str, geoserver_workspace: str,
                                        indicator_definition_id: int, timestamp_valid_start: datetime,
                                        storage_path_or_postgis_table: str, description: Optional[str] = None,
                                        timestamp_valid_end: Optional[datetime] = None,
                                        spatial_resolution_desc: Optional[str] = None,
                                        default_style_name: Optional[str] = None) -> RasterMetadata:
    defaults = {"geoserver_workspace": geoserver_workspace, "description": description,
                "indicator_definition_id": indicator_definition_id, "timestamp_valid_start": timestamp_valid_start,
                "timestamp_valid_end": timestamp_valid_end, "spatial_resolution_desc": spatial_resolution_desc,
                "storage_path_or_postgis_table": storage_path_or_postgis_table,
                "default_style_name": default_style_name}
    instance, _ = await get_or_create(session, RasterMetadata, layer_name_geoserver=layer_name_geoserver,
                                      defaults=defaults)
    return instance


async def get_or_create_crop(session: AsyncSession, code: str, name_en: str, name_local: Optional[str] = None,
                             category: Optional[str] = None, attributes: Optional[dict] = None) -> Crop:
    defaults = {"name_en": name_en, "name_local": name_local, "category": category, "attributes": attributes or {}}
    instance, _ = await get_or_create(session, Crop, code=code, defaults=defaults)
    return instance


async def create_cropping_pattern_entry(session: AsyncSession, reporting_unit_id: int, crop_id: int,
                                        time_period_year: int, data_type: str, time_period_season: Optional[str] = None,
                                        area_cultivated_ha: Optional[float] = None,
                                        area_proposed_ha: Optional[float] = None,
                                        yield_actual_ton_ha: Optional[float] = None,
                                        yield_proposed_ton_ha: Optional[float] = None,
                                        water_allocation_mcm: Optional[float] = None,
                                        water_consumed_actual_mcm: Optional[float] = None,
                                        comments: Optional[str] = None) -> CroppingPattern:
    instance = CroppingPattern(reporting_unit_id=reporting_unit_id, crop_id=crop_id, time_period_year=time_period_year,
                               time_period_season=time_period_season, data_type=data_type,
                               area_cultivated_ha=area_cultivated_ha, area_proposed_ha=area_proposed_ha,
                               yield_actual_ton_ha=yield_actual_ton_ha, yield_proposed_ton_ha=yield_proposed_ton_ha,
                               water_allocation_mcm=water_allocation_mcm,
                               water_consumed_actual_mcm=water_consumed_actual_mcm, comments=comments)
    session.add(instance)
    print(
        f"Adding CroppingPattern for unit {reporting_unit_id}, crop {crop_id}, year {time_period_year}, type {data_type}")
    return instance


async def get_or_create_infrastructure_type(session: AsyncSession, name: str,
                                            description: Optional[str] = None) -> InfrastructureType:
    instance, _ = await get_or_create(session, InfrastructureType, name=name, defaults={"description": description})
    return instance


async def get_or_create_operational_status_type(session: AsyncSession, name: str,
                                                description: Optional[str] = None) -> OperationalStatusType:
    instance, _ = await get_or_create(session, OperationalStatusType, name=name, defaults={"description": description})
    return instance


async def get_or_create_infrastructure(session: AsyncSession, name: str, infrastructure_type_id: int,
                                       reporting_unit_id: Optional[int] = None,
                                       operational_status_id: Optional[int] = None, capacity: Optional[float] = None,
                                       capacity_unit_id: Optional[int] = None, attributes: Optional[dict] = None,
                                       geom_wkt: Optional[str] = None) -> Infrastructure:
    defaults = {"infrastructure_type_id": infrastructure_type_id, "reporting_unit_id": reporting_unit_id,
                "operational_status_id": operational_status_id, "capacity": capacity,
                "capacity_unit_id": capacity_unit_id, "attributes": attributes or {}}
    instance, created = await get_or_create(session, Infrastructure, name=name, defaults=defaults)
    if geom_wkt and (created or not instance.geom):
        try:
            ewkt_with_srid = geom_wkt
            if not geom_wkt.upper().startswith("SRID="): ewkt_with_srid = f"SRID=4326;{geom_wkt}"
            await session.execute(sql_text("UPDATE infrastructure SET geom = ST_GeomFromEWKT(:wkt) WHERE id = :id"),
                                  {"wkt": ewkt_with_srid, "id": instance.id})
            print(f"Set/Updated geom for Infrastructure {name} using WKT.")
        except Exception as e:
            print(f"Error setting geom for Infra {name}: {e}")
    return instance


async def get_or_create_currency(session: AsyncSession, code: str, name: str) -> Currency:
    instance, _ = await get_or_create(session, Currency, code=code, defaults={"name": name})
    return instance


async def get_or_create_financial_account_type(session: AsyncSession, name: str, is_cost: bool,
                                               category: Optional[str] = None) -> FinancialAccountType:
    defaults = {"is_cost": is_cost, "category": category}
    instance, _ = await get_or_create(session, FinancialAccountType, name=name, defaults=defaults)
    return instance


async def create_financial_account_entry(session: AsyncSession, financial_account_type_id: int, transaction_date: date,
                                         amount: Decimal, currency_id: int, reporting_unit_id: Optional[int] = None,
                                         infrastructure_id: Optional[int] = None, crop_id: Optional[int] = None,
                                         description: Optional[str] = None,
                                         source_document_ref: Optional[str] = None) -> FinancialAccount:
    instance = FinancialAccount(reporting_unit_id=reporting_unit_id, infrastructure_id=infrastructure_id,
                                financial_account_type_id=financial_account_type_id, crop_id=crop_id,
                                transaction_date=transaction_date, amount=amount, currency_id=currency_id,
                                description=description, source_document_ref=source_document_ref)
    session.add(instance)
    print(f"Adding FinancialAccount type_id {financial_account_type_id}, date {transaction_date}, amount {amount}")
    return instance


# --- Main Population Logic ---
async def populate_data():
    print("Starting data population script...")

    async with AsyncSessionFactory() as session:
        try:
            # --- Stage 1: Create independent lookup entities and flush ---
            print("\n--- Populating Permissions ---")
            perm_view_all = await get_or_create_permission(session, name="data:view:all",
                                                           description="Can view all data.")
            perm_edit_basin_A = await get_or_create_permission(session, name="settings:edit:basin_A",
                                                               description="Can edit settings for Basin A.")
            perm_manage_users = await get_or_create_permission(session, name="users:manage",
                                                               description="Can manage users and roles.")
            await session.flush()

            print("\n--- Populating Reporting Unit Types ---")
            type_country = await get_or_create_reporting_unit_type(session, name="Country",
                                                                   description="National boundary.")
            type_basin = await get_or_create_reporting_unit_type(session, name="River Basin",
                                                                 description="Major river basin.")
            type_sub_basin = await get_or_create_reporting_unit_type(session, name="Sub-basin",
                                                                     description="Sub-division of a basin.")
            await session.flush()

            print("\n--- Populating Units of Measurement ---")
            uom_m3s = await get_or_create_unit_of_measurement(session, name="Cubic Meter per Second",
                                                              abbreviation="m3/s", description="Flow rate")
            uom_mm = await get_or_create_unit_of_measurement(session, name="Millimeter", abbreviation="mm",
                                                             description="Depth")
            uom_ha = await get_or_create_unit_of_measurement(session, name="Hectare", abbreviation="ha",
                                                             description="Area")
            uom_ton_ha = await get_or_create_unit_of_measurement(session, name="Ton per Hectare", abbreviation="t/ha",
                                                                 description="Yield density")
            uom_mcm = await get_or_create_unit_of_measurement(session, name="Million Cubic Meters", abbreviation="MCM",
                                                              description="Volume")
            await session.flush()

            print("\n--- Populating Temporal Resolutions ---")
            res_daily = await get_or_create_temporal_resolution(session, name="Daily")
            res_monthly = await get_or_create_temporal_resolution(session, name="Monthly")
            await session.flush()

            print("\n--- Populating Data Quality Flags ---")
            dqf_measured = await get_or_create_data_quality_flag(session, name="Measured",
                                                                 description="Directly measured data.")
            dqf_estimated = await get_or_create_data_quality_flag(session, name="Estimated",
                                                                  description="Estimated or modeled data.")
            await session.flush()

            print("\n--- Populating Indicator Categories ---")
            cat_hydro = await get_or_create_indicator_category(session, name_en="Hydrology", name_local="Hidrologi")
            cat_agri = await get_or_create_indicator_category(session, name_en="Agriculture", name_local="Pertanian")
            await session.flush()

            print("\n--- Populating Crops ---")
            crop_wheat = await get_or_create_crop(session, code="WHT", name_en="Wheat", category="Cereal",
                                                  attributes={"growing_period_days": 120})
            crop_maize = await get_or_create_crop(session, code="MAZ", name_en="Maize", category="Cereal")
            await session.flush()

            print("\n--- Populating Infrastructure Types ---")
            it_dam = await get_or_create_infrastructure_type(session, name="Dam", description="Water storage dam.")
            it_pump = await get_or_create_infrastructure_type(session, name="Pumping Station",
                                                              description="Water pumping facility.")
            await session.flush()

            print("\n--- Populating Operational Status Types ---")
            ost_op = await get_or_create_operational_status_type(session, name="Operational",
                                                                 description="Currently operational.")
            ost_maint = await get_or_create_operational_status_type(session, name="Under Maintenance",
                                                                    description="Temporarily down.")
            await session.flush()

            print("\n--- Populating Currencies ---")
            curr_usd = await get_or_create_currency(session, code="USD", name="US Dollar")
            curr_irr = await get_or_create_currency(session, code="IRR", name="Iranian Rial")
            await session.flush()

            print("\n--- Populating Financial Account Types ---")
            fat_op_cost = await get_or_create_financial_account_type(session, name="Operational Cost", is_cost=True,
                                                                     category="OPEX")
            fat_rev_tariff = await get_or_create_financial_account_type(session, name="Tariff Revenue", is_cost=False,
                                                                        category="Revenue")
            await session.flush()

            # --- Stage 2: Create entities that depend on Stage 1 entities ---
            print("\n--- Populating Roles (with Permissions) ---")
            admin_role = await get_or_create_role(session, name="Administrator",
                                                  description="System wide administrator.",
                                                  permissions_to_assign=[perm_view_all, perm_manage_users,
                                                                         perm_edit_basin_A])
            viewer_role = await get_or_create_role(session, name="DataViewer", description="Can view data.",
                                                   permissions_to_assign=[perm_view_all])
            # No explicit flush needed here as get_or_create_role flushes internally if permissions are added

            print("\n--- Populating Reporting Units (with hierarchy) ---")
            country_x = await get_or_create_reporting_unit(session, name="Country X", code="CX",
                                                           unit_type_id=type_country.id)
            await session.flush()
            blue_basin = await get_or_create_reporting_unit(session, name="Blue River Basin", code="BRB",
                                                            unit_type_id=type_basin.id, parent_unit_id=country_x.id,
                                                            area_sqkm=12000.0,
                                                            geom_wkt="MULTIPOLYGON(((0 0, 0 10, 10 10, 10 0, 0 0)))")
            await session.flush()
            upper_blue_sub = await get_or_create_reporting_unit(session, name="Upper Blue Sub-basin", code="UBSB",
                                                                unit_type_id=type_sub_basin.id,
                                                                parent_unit_id=blue_basin.id)
            await session.flush()

            print("\n--- Populating Indicator Definitions (with lookups) ---")
            def_discharge = await get_or_create_indicator_definition(
                session, code="Q_RIVER", name_en="River Discharge", data_type="Numeric",
                unit_of_measurement_id=uom_m3s.id, category_id=cat_hydro.id,
                description_en="River flow rate."
            )
            def_rainfall = await get_or_create_indicator_definition(
                session, code="P_TOTAL", name_en="Total Precipitation", data_type="Numeric",
                unit_of_measurement_id=uom_mm.id, category_id=cat_hydro.id,
                description_en="Total precipitation depth.", is_spatial_raster=True
            )
            await session.flush()

            print("\n--- Populating Infrastructure (with lookups) ---")
            dam_blue = await get_or_create_infrastructure(
                session, name="Blue Grand Dam", infrastructure_type_id=it_dam.id,
                reporting_unit_id=blue_basin.id, operational_status_id=ost_op.id,
                capacity=1200.0, capacity_unit_id=uom_mcm.id,
                attributes={"construction_year": 1985, "height_m": 75}
            )
            await session.flush()

            # --- Stage 3: Create transactional/fact data ---
            print("\n--- Populating Indicator Timeseries ---")
            # Note: timestamp values are now explicitly UTC aware
            await create_indicator_timeseries_entry(
                session, indicator_definition_id=def_discharge.id, reporting_unit_id=upper_blue_sub.id,
                timestamp=datetime(2023, 1, 1, 10, 0, 0),
                value_numeric=150.5,
                temporal_resolution_id=res_daily.id, quality_flag_id=dqf_measured.id
            )
            await create_indicator_timeseries_entry(
                session, indicator_definition_id=def_rainfall.id, reporting_unit_id=upper_blue_sub.id,
                timestamp=datetime(2023, 1, 1, 0, 0, 0),
                value_numeric=75.2,
                temporal_resolution_id=res_monthly.id, quality_flag_id=dqf_estimated.id
            )

            print("\n--- Populating Raster Metadata ---")
            await get_or_create_raster_metadata(
                session, layer_name_geoserver="brb_rainfall_2023_01", geoserver_workspace="wa_plus_rasters",
                indicator_definition_id=def_rainfall.id,
                timestamp_valid_start=datetime(2023, 1, 1),  # Removed tzinfo
                storage_path_or_postgis_table="/srv/geodata/rasters/brb_rainfall_2023_01.tif",
                spatial_resolution_desc="1km", default_style_name="rainfall_style"
            )

            print("\n--- Populating Cropping Patterns ---")
            await create_cropping_pattern_entry(
                session, reporting_unit_id=upper_blue_sub.id, crop_id=crop_wheat.id,
                time_period_year=2023, time_period_season="Kharif", data_type="Actual",
                area_cultivated_ha=120.0, yield_actual_ton_ha=4.5
            )

            print("\n--- Populating Financial Accounts ---")
            await create_financial_account_entry(
                session, financial_account_type_id=fat_op_cost.id, reporting_unit_id=blue_basin.id,
                infrastructure_id=dam_blue.id, currency_id=curr_usd.id,
                transaction_date=date(2023, 12, 31), amount=Decimal("55000.75"),
                description="Annual O&M for Blue Grand Dam 2023"
            )

            await session.commit()  # Commit all pending operations
            print("Test data population committed successfully.")
        except Exception as e:
            print(f"\nError during data population: {e}")
            # No explicit rollback needed here if an error bubbles up before commit,
            # as the `async with AsyncSessionFactory() as session:`
            # context manager will handle rollback on unhandled exceptions IF the session
            # was part of a transaction block (e.g. session.begin()) or if commit fails.
            # However, for safety, an explicit rollback can be added,
            # but ensure it's only called if a transaction was active.
            # if session.in_transaction(): await session.rollback()
            raise
    print("\nData population script finished.")


if __name__ == "__main__":
    print("Running populate_test_data.py script...")
    asyncio.run(populate_data())
