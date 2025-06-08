import asyncio
import random
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Type, TypeVar
from geoalchemy2 import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, attributes
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError # Moved import to top

import sys
import os

project_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from app.database.session import AsyncSessionFactory
from app.database.models.base_model import Base
# User, Role, Permission removed from imports
from app.database.models import (
    ReportingUnitType, ReportingUnit, UnitOfMeasurement,
    TemporalResolution, DataQualityFlag, IndicatorCategory, IndicatorDefinition,
    IndicatorTimeseries, RasterMetadata, Crop, CroppingPattern, InfrastructureType,
    OperationalStatusType, Infrastructure, Currency, FinancialAccountType, FinancialAccount
)
# Hasher is no longer needed as users are not created here
# from app.security.hashing import Hasher
# settings might still be used for other defaults, if not, it can be removed. Keeping for now.
from app.core.config import settings

# --- Configuration ---
# NUM_USERS removed
NUM_REPORTING_UNITS_PER_TYPE_MAIN = 2
NUM_SUB_UNITS_PER_MAIN = 1
NUM_INDICATOR_DEFINITIONS_TO_CREATE = 5  # How many extra random ones after predefined
NUM_TIMESERIES_PER_LINK = 3
NUM_INFRASTRUCTURES_TO_CREATE = 3
NUM_CROPS_TO_CREATE = 3  # Beyond predefined
NUM_FINANCIAL_ACCOUNTS_TO_CREATE = 5
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

ModelType = TypeVar("ModelType", bound=Base)


# --- Helper Functions ---
async def _get_or_create(session: AsyncSession, model_cls: Type[ModelType], defaults: Optional[Dict[str, Any]] = None,
                         load_relationships: Optional[List[str]] = None, **kwargs: Any) -> tuple[ModelType, bool]:
    # Initial query based on kwargs
    stmt = select(model_cls).filter_by(**kwargs)
    if load_relationships and hasattr(model_cls, '__mapper__'):
        options_to_load = []
        for rel_name in load_relationships:
            if hasattr(model_cls, rel_name): options_to_load.append(selectinload(getattr(model_cls, rel_name)))
        if options_to_load: stmt = stmt.options(*options_to_load)

    result = await session.execute(stmt)
    instance = result.scalars().first()
    created = False

    if instance:
        # print(f"{model_cls.__name__} with {kwargs} already exists (ID: {instance.id}).") # Reduced verbosity
        return instance, False # Return early if found

    # If not found, attempt to create within a savepoint
    params = {**kwargs, **(defaults or {})}
    try:
        async with session.begin_nested() as savepoint:  # Start savepoint
            # print(f"Attempting to create {model_cls.__name__} with params: {params} within a savepoint.") # Reduced verbosity
            instance = model_cls(**params)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            created = True
            # print(f"Successfully created and flushed {model_cls.__name__} (ID: {instance.id}) within savepoint.") # Reduced verbosity
            # Savepoint is committed automatically if this block completes without error

    except IntegrityError as e:
        # Savepoint is automatically rolled back by 'async with' on exception
        # print(f"IntegrityError for {model_cls.__name__} with params {params} during savepoint. Savepoint rolled back. Attempting to fetch conflicting record.") # Reduced verbosity

        fetched_instance = None
        # Try fetching by unique fields that might have caused the conflict.
        # Example: if 'name' is unique
        if 'name' in params and hasattr(model_cls, 'name'):
            stmt_alt_name = select(model_cls).filter_by(name=params['name'])
            result_alt_name = await session.execute(stmt_alt_name)
            fetched_instance = result_alt_name.scalars().first()
        # Example: if 'code' is unique (common for some of these models)
        elif 'code' in params and hasattr(model_cls, 'code'):
            stmt_alt_code = select(model_cls).filter_by(code=params['code'])
            result_alt_code = await session.execute(stmt_alt_code)
            fetched_instance = result_alt_code.scalars().first()

        if not fetched_instance:
            # Try again with original kwargs, in case of a race condition
            stmt_alt_kwargs = select(model_cls).filter_by(**kwargs)
            result_alt_kwargs = await session.execute(stmt_alt_kwargs)
            fetched_instance = result_alt_kwargs.scalars().first()

        if fetched_instance:
            instance = fetched_instance
            created = False # Not created by this call
            # print(f"Found existing {model_cls.__name__} (ID: {instance.id}) after IntegrityError and savepoint rollback.") # Reduced verbosity
        else:
            # print(f"Could not find conflicting {model_cls.__name__} after IntegrityError and savepoint rollback. Re-raising original error.") # Reduced verbosity
            raise e  # Re-raise the original integrity error

    return instance, created


def get_random_element(db_list: List[Any], allow_none: bool = False, none_probability: float = 0.1) -> Any:
    if not db_list: return None
    if allow_none and random.random() < none_probability: return None
    return random.choice(db_list)

# --- User, Role, Permission creation functions removed ---

async def create_reporting_unit_types(session: AsyncSession) -> List[ReportingUnitType]:
    print("Creating reporting unit types...")
    types_data = [
        {"name": "Country", "description": "National level"},
        {"name": "Province", "description": "Provincial administrative unit"},
        {"name": "River Basin", "description": "Major river basin"},
        {"name": "Sub-Basin", "description": "Sub-catchment area within a larger basin"},
        {"name": "Irrigation Scheme", "description": "Area covered by an irrigation system"},
        {"name": "Monitoring Zone", "description": "Zone for specific monitoring activities"}
    ]
    created_types = []
    for data in types_data:
        item, _ = await _get_or_create(session, ReportingUnitType, {"description": data["description"]},
                                       name=data["name"])
        created_types.append(item)
    await session.flush()
    print(f"Created/found {len(created_types)} reporting unit types.")
    return created_types

async def get_or_create_reporting_unit(
        session: AsyncSession,
        name: str,
        code: str,
        unit_type_id: int,
        parent_unit_id: Optional[int] = None,
        description: Optional[str] = None,
        area_sqkm: Optional[float] = None,
        geom_wkt: Optional[str] = None
) -> tuple[ReportingUnit, bool]:
    defaults = {
        "name": name,
        "unit_type_id": unit_type_id,
        "parent_unit_id": parent_unit_id,
        "description": description,
        "area_sqkm": area_sqkm
    }
    # Assuming created_by_user_id and updated_by_user_id are nullable or have DB defaults
    # If they were non-nullable and previously set using a user from create_users:
    # defaults["created_by_user_id"] = 1 # Placeholder for user ID from deci_core
    # defaults["updated_by_user_id"] = 1 # Placeholder for user ID from deci_core

    instance, created = await _get_or_create(
        session, ReportingUnit, code=code, defaults=defaults
    )

    if geom_wkt and (created or not instance.geom):
        try:
            instance.geom = WKTElement(geom_wkt, srid=4326)
            session.add(instance)
            await session.flush([instance])
        except Exception as e:
            print(f"Error setting geom for RU {code}: {e}")
            if session.in_transaction():
                await session.rollback()
            raise
    return instance, created

async def create_reporting_units(session: AsyncSession, unit_types: List[ReportingUnitType]) -> List[ReportingUnit]:
    print("Creating reporting units...")
    units = []
    if not unit_types:
        print("Warning: No reporting unit types provided to create_reporting_units.")
        return units

    type_country = next((ut for ut in unit_types if ut.name == "Country"), unit_types[0])
    type_basin = next((ut for ut in unit_types if ut.name == "River Basin"), unit_types[0])
    type_sub_basin = next((ut for ut in unit_types if ut.name == "Sub-Basin"), unit_types[0])

    aqt_country_unit, _ = await get_or_create_reporting_unit(session, name="Republic of Aquaterra", code="AQT", unit_type_id=type_country.id, area_sqkm=random.uniform(100000, 500000))
    units.append(aqt_country_unit)

    province_type = next((ut for ut in unit_types if ut.name == "Province"), unit_types[0])
    for i in range(NUM_REPORTING_UNITS_PER_TYPE_MAIN):
        prov_name = f"Province {chr(65 + i)}"
        prov_code = f"AQT-P{chr(65 + i)}"
        province, _ = await get_or_create_reporting_unit(session, name=prov_name, code=prov_code, unit_type_id=province_type.id, parent_unit_id=aqt_country_unit.id, area_sqkm=random.uniform(50000, 200000))
        units.append(province)
        for j in range(NUM_SUB_UNITS_PER_MAIN):
            sub_name = f"{prov_name} Sub-{j + 1}"
            sub_code = f"{prov_code}-SB{j + 1}"
            sub_unit, _ = await get_or_create_reporting_unit(session, name=sub_name, code=sub_code, unit_type_id=type_sub_basin.id, parent_unit_id=province.id, area_sqkm=random.uniform(1000, 10000))
            units.append(sub_unit)

    country_x, _ = await get_or_create_reporting_unit(session, name="Country X", code="CX", unit_type_id=type_country.id, area_sqkm=1200000.0)
    units.append(country_x)
    wkt_brb = "MULTIPOLYGON(((30 -10, 40 -20, 35 -25, 30 -10)))"
    blue_river_basin, _ = await get_or_create_reporting_unit(session, name="Blue River Basin", code="BRB", unit_type_id=type_basin.id, parent_unit_id=country_x.id, area_sqkm=50000.0, geom_wkt=wkt_brb)
    units.append(blue_river_basin)
    upper_blue_subbasin, _ = await get_or_create_reporting_unit(session, name="Upper Blue Sub-basin", code="UBSB", unit_type_id=type_sub_basin.id, parent_unit_id=blue_river_basin.id, area_sqkm=15000.0)
    units.append(upper_blue_subbasin)
    await session.flush()
    print(f"Created/found {len(units)} reporting units.")
    return units

async def create_lookups(session: AsyncSession) -> Dict[str, List[Any]]:
    print("Creating lookup tables data...")
    results: Dict[str, List[Any]] = {}
    uom_data = [
        {"name": "Cubic Meter", "abbreviation": "m³"}, {"name": "Cubic Meter per Second", "abbreviation": "m3/s"},
        {"name": "Liter per Second", "abbreviation": "l/s"}, {"name": "Hectare", "abbreviation": "ha"},
        {"name": "Ton per Hectare", "abbreviation": "t/ha"}, {"name": "Millimeter", "abbreviation": "mm"},
        {"name": "Million Cubic Meters", "abbreviation": "MCM"}
    ]
    results["units_of_measurement"] = [(await _get_or_create(session, UnitOfMeasurement, {"name": d["name"]}, abbreviation=d["abbreviation"]))[0] for d in uom_data]
    tr_data = ["Annual", "Monthly", "Daily", "Snapshot"]
    results["temporal_resolutions"] = [(await _get_or_create(session, TemporalResolution, name=n))[0] for n in tr_data]
    dqf_data = ["RAW", "VALIDATED", "ESTIMATED", "Measured"]
    results["data_quality_flags"] = [(await _get_or_create(session, DataQualityFlag, name=n, defaults={"description": f"{n} data"}))[0] for n in dqf_data]
    currency_data = [{"code": "USD", "name": "US Dollar"}, {"code": "EUR", "name": "Euro"}, {"code": "IRR", "name": "Iranian Rial"}]
    results["currencies"] = [(await _get_or_create(session, Currency, {"name": d["name"]}, code=d["code"]))[0] for d in currency_data]
    crop_data = [{"code": "WHT", "name_en": "Wheat"}, {"code": "RCE", "name_en": "Rice"}, {"code": "MAZ", "name_en": "Maize"}]
    results["crops"] = [(await _get_or_create(session, Crop, {"name_en": d["name_en"]}, code=d["code"]))[0] for d in crop_data]
    it_data = ["Dam", "Canal", "Pumping Station"]
    results["infrastructure_types"] = [(await _get_or_create(session, InfrastructureType, name=n, defaults={"description": f"{n} type"}))[0] for n in it_data]
    ost_data = ["Operational", "Maintenance", "Decommissioned"]
    results["operational_status_types"] = [(await _get_or_create(session, OperationalStatusType, name=n, defaults={"description": f"Status: {n}"}))[0] for n in ost_data]
    fat_data = [{"name": "Revenue", "is_cost": False}, {"name": "OPEX", "is_cost": True}, {"name": "CAPEX", "is_cost": True}]
    results["financial_account_types"] = [(await _get_or_create(session, FinancialAccountType, name=d["name"], defaults={"is_cost": d["is_cost"]}))[0] for d in fat_data]
    await session.flush()
    print("Lookup data created/verified.")
    return results

# populate_main_data no longer takes 'users' argument
async def populate_main_data(session: AsyncSession, lookups: Dict[str, List[Any]],
                             reporting_units: List[ReportingUnit]):
    print("Populating main data entities (IndicatorDefs, Infra)...")
    # Assuming created_by_user_id and updated_by_user_id on models like IndicatorCategory,
    # IndicatorDefinition, Infrastructure are nullable or have DB defaults.
    # If they were non-nullable and previously set using a user from create_users:
    # placeholder_user_id = 1 # Placeholder for user ID from deci_core

    ru_blue_river_basin, _ = await _get_or_create(session, ReportingUnit, code="BRB")
    ru_upper_blue_subbasin, _ = await _get_or_create(session, ReportingUnit, code="UBSB")

    indicator_categories = {}
    cat_hydro_defaults = {"name_local": "Hidrologi"}
    # if placeholder_user_id: cat_hydro_defaults["created_by_user_id"] = placeholder_user_id
    cat_hydro, _ = await _get_or_create(session, IndicatorCategory, name_en="Hydrology", defaults=cat_hydro_defaults)
    indicator_categories["Hydrology"] = cat_hydro

    cat_agri_defaults = {"name_local": "Pertanian"}
    # if placeholder_user_id: cat_agri_defaults["created_by_user_id"] = placeholder_user_id
    cat_agri, _ = await _get_or_create(session, IndicatorCategory, name_en="Agriculture", defaults=cat_agri_defaults)
    indicator_categories["Agriculture"] = cat_agri
    await session.flush()

    indicator_definitions = {}
    ind_def_precip_data = {"code": "PRECIP", "name_en": "Precipitation", "data_type": "Numeric", "uom_abbr": "mm", "is_spatial_raster": True, "category_name": "Hydrology"}
    ind_def_qriver_data = {"code": "Q_RIVER", "name_en": "River Discharge", "data_type": "Numeric", "uom_abbr": "m3/s", "category_name": "Hydrology"}

    for i_data in [ind_def_precip_data, ind_def_qriver_data]:
        uom = next((u for u in lookups["units_of_measurement"] if u.abbreviation == i_data["uom_abbr"]), None)
        category = indicator_categories.get(i_data["category_name"])
        if not uom: print(f"Warning: UoM {i_data['uom_abbr']} not found for indicator {i_data['code']}. Skipping."); continue
        if not category: print(f"Warning: Category {i_data['category_name']} not found for indicator {i_data['code']}. Skipping."); continue

        idef_defaults = {"name_en": i_data["name_en"], "data_type": i_data["data_type"],
                         "unit_of_measurement_id": uom.id, "category_id": category.id,
                         "is_spatial_raster": i_data.get("is_spatial_raster", False)}
        # if placeholder_user_id: idef_defaults["created_by_user_id"] = placeholder_user_id
        idef, _ = await _get_or_create(session, IndicatorDefinition, code=i_data["code"], defaults=idef_defaults)
        indicator_definitions[i_data["code"]] = idef
    await session.flush()

    infrastructures = {}
    dam_type_generic = next((it for it in lookups["infrastructure_types"] if it.name == "Dam"), None)
    op_status_generic = next((os_ for os_ in lookups["operational_status_types"] if os_.name == "Operational"), None)

    if dam_type_generic and op_status_generic:
        for i in range(NUM_INFRASTRUCTURES_TO_CREATE):
            random_ru_for_generic_dam = get_random_element(reporting_units)
            infra_defaults = {"infrastructure_type_id": dam_type_generic.id,
                              "reporting_unit_id": random_ru_for_generic_dam.id if random_ru_for_generic_dam else None,
                              "operational_status_id": op_status_generic.id}
            # if placeholder_user_id: infra_defaults["created_by_user_id"] = placeholder_user_id
            infra, _ = await _get_or_create(session, Infrastructure, name=f"{random_ru_for_generic_dam.code if random_ru_for_generic_dam else 'SYS'}-Dam-{i + 1}",
                                            defaults=infra_defaults)

    dam_type_specific = dam_type_generic
    op_status_specific = op_status_generic
    uom_mcm = next((uom for uom in lookups["units_of_measurement"] if uom.abbreviation == "MCM"), None)

    if dam_type_specific and op_status_specific and uom_mcm and ru_blue_river_basin:
        dam_blue_grand_defaults = {
            "infrastructure_type_id": dam_type_specific.id,
            "reporting_unit_id": ru_blue_river_basin.id,
            "operational_status_id": op_status_specific.id,
            "capacity": Decimal("120.5"),
            "capacity_unit_id": uom_mcm.id,
        }
        # if placeholder_user_id: dam_blue_grand_defaults["created_by_user_id"] = placeholder_user_id
        dam_blue_grand, _ = await _get_or_create(session, Infrastructure, name="Blue Grand Dam", defaults=dam_blue_grand_defaults)
        infrastructures["Blue Grand Dam"] = dam_blue_grand
    else:
        print("Warning: Could not create 'Blue Grand Dam' due to missing dependencies (type, status, UoM, or RU).")
    await session.flush()
    print("Main data entities populated.")
    entities_for_transactional = {
        "indicator_definitions_dict": indicator_definitions, "infrastructures_dict": infrastructures,
        "reporting_units_all": reporting_units, "ru_upper_blue_subbasin": ru_upper_blue_subbasin,
        "dam_blue_grand": infrastructures.get("Blue Grand Dam"),
        "crop_wheat": next((c for c in lookups.get("crops", []) if c.code == "WHT"), None),
        "lookups": lookups
    }
    return entities_for_transactional

async def populate_transactional_data(session: AsyncSession, main_entities: Dict[str, Any]):
    print("Populating transactional data...")
    # Assuming created_by_user_id and updated_by_user_id on transactional models
    # (IndicatorTimeseries, RasterMetadata, CroppingPattern, FinancialAccount) are nullable or have DB defaults.
    # If they were non-nullable and previously set:
    # placeholder_user_id = 1 # Placeholder for user ID from deci_core

    indicator_definitions_dict = main_entities.get("indicator_definitions_dict", {})
    ru_upper_blue_subbasin = main_entities.get("ru_upper_blue_subbasin")
    dam_blue_grand = main_entities.get("dam_blue_grand")
    crop_wheat = main_entities.get("crop_wheat")
    internal_lookups = main_entities.get("lookups", {})

    def_q_river = indicator_definitions_dict.get("Q_RIVER")
    def_precip = indicator_definitions_dict.get("PRECIP")
    tr_daily = next((tr for tr in internal_lookups.get("temporal_resolutions", []) if tr.name == "Daily"), None)
    dqf_measured = next((dqf for dqf in internal_lookups.get("data_quality_flags", []) if dqf.name == "Measured"), None)

    ts_defaults = {}
    # if placeholder_user_id: ts_defaults["created_by_user_id"] = placeholder_user_id
    if def_q_river and ru_upper_blue_subbasin and tr_daily and dqf_measured:
        for i in range(3):
            session.add(IndicatorTimeseries(indicator_definition_id=def_q_river.id, reporting_unit_id=ru_upper_blue_subbasin.id,
                                            timestamp=datetime(2023, 1, 15 + i, tzinfo=timezone.utc), value_numeric=random.uniform(50, 150),
                                            temporal_resolution_id=tr_daily.id, quality_flag_id=dqf_measured.id, **ts_defaults))
    if def_precip and ru_upper_blue_subbasin and tr_daily and dqf_measured:
        for i in range(3):
             session.add(IndicatorTimeseries(indicator_definition_id=def_precip.id, reporting_unit_id=ru_upper_blue_subbasin.id,
                                             timestamp=datetime(2023, 1, 15 + i, tzinfo=timezone.utc), value_numeric=random.uniform(1, 20),
                                             temporal_resolution_id=tr_daily.id, quality_flag_id=dqf_measured.id, **ts_defaults))

    raster_defaults = {}
    # if placeholder_user_id: raster_defaults["created_by_user_id"] = placeholder_user_id
    if def_precip:
        session.add(RasterMetadata(layer_name_geoserver="brb_rainfall_2023_01", geoserver_workspace="basins",
                                   indicator_definition_id=def_precip.id, timestamp_valid_start=datetime(2023, 1, 1),
                                   timestamp_valid_end=datetime(2023, 1, 31, 23, 59, 59),
                                   storage_path_or_postgis_table="s3://bucket/brb_rainfall_2023_01.tif", **raster_defaults))

    cp_defaults = {}
    # if placeholder_user_id: cp_defaults["created_by_user_id"] = placeholder_user_id
    if crop_wheat and ru_upper_blue_subbasin:
        session.add(CroppingPattern(reporting_unit_id=ru_upper_blue_subbasin.id, crop_id=crop_wheat.id, time_period_year=2023,
                                    data_type="Planned", area_cultivated_ha=Decimal("1200.75"),
                                    yield_actual_ton_ha=Decimal("4.5"), water_consumed_actual_mcm=Decimal("6000.0"), **cp_defaults))

    fa_defaults = {}
    # if placeholder_user_id: fa_defaults["created_by_user_id"] = placeholder_user_id
    fac_type_opex = next((ft for ft in internal_lookups.get("financial_account_types", []) if ft.name == "OPEX"), None)
    curr_usd = next((c for c in internal_lookups.get("currencies", []) if c.code == "USD"), None)
    if dam_blue_grand and fac_type_opex and curr_usd:
        session.add(FinancialAccount(financial_account_type_id=fac_type_opex.id, currency_id=curr_usd.id,
                                     infrastructure_id=dam_blue_grand.id, transaction_date=date(2023, 3, 15),
                                     amount=Decimal("-25000.00"), description="Annual operational cost for Blue Grand Dam", **fa_defaults))
    await session.flush()
    print("Transactional data (specific and potentially generic) added.")

async def populate_database():
    print("Starting database population process...")
    async with AsyncSessionFactory() as session:
        try:
            print("\n--- STAGE 1: Independent Lookups & Basic Entities ---")
            # Removed calls to create_permissions, create_roles, create_users
            ru_types = await create_reporting_unit_types(session)
            lookups = await create_lookups(session)
            print("\n--- STAGE 2: Entities with Dependencies on Stage 1 ---")
            reporting_units_all = await create_reporting_units(session, ru_types)
            # Users argument removed from populate_main_data call
            main_data_entities = await populate_main_data(session, lookups, reporting_units_all)
            print("\n--- STAGE 3: Transactional Data (includes specific entries) ---")
            # The 'lookups' argument was redundant as it's already in main_data_entities
            await populate_transactional_data(session, main_data_entities)
            await session.commit()
            print("Database population completed successfully!")
        except Exception as e:
            print(f"Error during database population: {e}")
            import traceback
            traceback.print_exc()
            raise
    print("\nScript finished.")

async def main():
    await populate_database()

if __name__ == "__main__":
    print("Running data population script (populate_data_test.py)...")
    asyncio.run(main())
    print("Script finished. (final print)")