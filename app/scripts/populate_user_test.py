import asyncio
import random
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, attributes
from sqlalchemy import text as sql_text

import sys
import os

project_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

from app.database.session import AsyncSessionFactory
from app.database.models.base_model import Base
from app.database.models import (
    Permission, Role, User, ReportingUnitType, ReportingUnit, UnitOfMeasurement,
    TemporalResolution, DataQualityFlag, IndicatorCategory, IndicatorDefinition,
    IndicatorTimeseries, RasterMetadata, Crop, CroppingPattern, InfrastructureType,
    OperationalStatusType, Infrastructure, Currency, FinancialAccountType, FinancialAccount
)
from app.security.hashing import Hasher
from app.core.config import settings

# --- Configuration ---
NUM_USERS = 5
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


# --- Helper Functions (assuming _get_or_create, get_random_element are as in V7) ---
async def _get_or_create(session: AsyncSession, model_cls: Type[ModelType], defaults: Optional[Dict[str, Any]] = None,
                         load_relationships: Optional[List[str]] = None, **kwargs: Any) -> tuple[ModelType, bool]:
    stmt = select(model_cls).filter_by(**kwargs)
    if load_relationships and hasattr(model_cls, '__mapper__'):
        options_to_load = []
        for rel_name in load_relationships:
            if hasattr(model_cls, rel_name): options_to_load.append(selectinload(getattr(model_cls, rel_name)))
        if options_to_load: stmt = stmt.options(*options_to_load)
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


def get_random_element(db_list: List[Any], allow_none: bool = False, none_probability: float = 0.1) -> Any:
    if not db_list: return None
    if allow_none and random.random() < none_probability: return None
    return random.choice(db_list)


# --- Data Creation Functions (create_permissions, create_roles, create_users from V7 are good) ---
async def create_permissions(session: AsyncSession) -> List[Permission]:
    print("Creating permissions...")
    permissions_data = [
        {"name": "view_all_dashboards", "description": "Can view all dashboards"},
        {"name": "manage_users", "description": "Can create, edit, delete users"},
        {"name": "manage_roles", "description": "Can create, edit, delete roles"},
        {"name": "enter_basin_data", "description": "Can enter data for any basin"},
        {"name": "approve_basin_data", "description": "Can approve data for any basin"},
        {"name": "view_financial_reports", "description": "Can view financial reports"},
        {"name": "manage_infrastructure_data", "description": "Can manage infrastructure records"},
    ]
    permissions = []
    for p_data in permissions_data:
        perm, _ = await _get_or_create(session, Permission, {"description": p_data["description"]}, name=p_data["name"])
        permissions.append(perm)
    await session.flush()
    print(f"Created/found {len(permissions)} permissions.")
    return permissions


async def create_roles(session: AsyncSession, all_permissions: List[Permission]) -> List[Role]:
    print("Creating roles...")
    roles_data_from_script = [
        {"name": "Administrator", "description": "System Administrator", "permissions_to_link": all_permissions},
        {"name": "DataManager", "description": "Manages data", "permissions_to_link": [p for p in all_permissions if
                                                                                       "view" in p.name or "data" in p.name or "enter" in p.name or "approve" in p.name]},
        {"name": "ReportingAnalyst", "description": "Views data and reports",
         "permissions_to_link": [p for p in all_permissions if "view" in p.name]},
    ]
    created_roles_list = []
    for r_data in roles_data_from_script:
        role_instance, created = await _get_or_create(session, Role, defaults={"description": r_data["description"]},
                                                      load_relationships=["permissions"], name=r_data["name"])
        if created:
            await session.flush()
            print(f"Role '{role_instance.name}' created with ID {role_instance.id}.")
            attributes.set_committed_value(role_instance, 'permissions', [])
            print(f"Set committed (empty) 'permissions' state for new role '{role_instance.name}'.")
        else:
            if role_instance: print(
                f"Role '{role_instance.name}' (ID: {role_instance.id}) exists. Permissions eager-loaded.")
        if r_data.get("permissions_to_link") and role_instance:
            current_assigned_permission_ids = {p.id for p in role_instance.permissions if p.id is not None}
            needs_flush = False
            for perm_obj in r_data["permissions_to_link"]:
                if perm_obj.id is None: print(f"Warning: Perm '{perm_obj.name}' has no ID."); continue
                if perm_obj.id not in current_assigned_permission_ids:
                    role_instance.permissions.append(perm_obj);
                    needs_flush = True
                    print(f"Queueing perm '{perm_obj.name}' for role '{role_instance.name}'.")
            if needs_flush: session.add(role_instance); await session.flush(); print(
                f"Flushed perm assignments for role '{role_instance.name}'.")
        if role_instance: created_roles_list.append(role_instance)
    print(f"Processed {len(created_roles_list)} roles.")
    return created_roles_list


async def create_users(session: AsyncSession, all_roles: List[Role]) -> List[User]:
    print("Creating users...")
    created_users_list = []
    admin_role = next((r for r in all_roles if r.name == "Administrator"), None)
    if not admin_role and all_roles: admin_role = all_roles[0]
    if not admin_role: print("Warning: No Administrator role for admin user.")
    default_password = settings.DEFAULT_SUPERUSER_PASSWORD if hasattr(settings,
                                                                      'DEFAULT_SUPERUSER_PASSWORD') and settings.DEFAULT_SUPERUSER_PASSWORD else "supersecretpassword123!"
    admin_defaults = {"full_name": "Admin User", "is_superuser": True, "is_active": True,
                      "hashed_password": Hasher.get_password_hash(default_password)}
    admin_user, admin_created = await _get_or_create(session, User, defaults=admin_defaults,
                                                     load_relationships=["roles"], email="admin@example.com")
    if admin_created:
        await session.flush();
        print(f"User '{admin_user.email}' created with ID {admin_user.id}.")
        attributes.set_committed_value(admin_user, 'roles', [])
        print(f"Set committed (empty) 'roles' state for new user '{admin_user.email}'.")
    else:
        if admin_user: print(f"User '{admin_user.email}' (ID: {admin_user.id}) exists. Roles eager-loaded.")
    if admin_user and admin_role:
        current_admin_role_ids = {r.id for r in admin_user.roles if r.id is not None}
        if admin_role.id not in current_admin_role_ids:
            admin_user.roles.append(admin_role);
            session.add(admin_user);
            print(f"Queueing admin role for {admin_user.email}")
    if admin_user: created_users_list.append(admin_user)
    for i in range(1, NUM_USERS + 1):
        user_email = f"user{i}@example.com"
        user_defaults = {"full_name": f"Test User {i}", "is_superuser": False,
                         "is_active": random.choice([True, True, False]),
                         "hashed_password": Hasher.get_password_hash("password123")}
        user, user_created = await _get_or_create(session, User, defaults=user_defaults, load_relationships=["roles"],
                                                  email=user_email)
        if user_created:
            await session.flush();
            print(f"User '{user.email}' created with ID {user.id}.")
            attributes.set_committed_value(user, 'roles', [])
            print(f"Set committed (empty) 'roles' state for new user '{user.email}'.")
        else:
            if user: print(f"User '{user.email}' (ID: {user.id}) exists. Roles eager-loaded.")
        if user and all_roles:
            assigned_role = get_random_element(all_roles)
            if assigned_role:
                current_user_role_ids = {r.id for r in user.roles if r.id is not None}
                if assigned_role.id not in current_user_role_ids:
                    user.roles.append(assigned_role);
                    session.add(user);
                    print(f"Queueing role '{assigned_role.name}' for user '{user.email}'")
        if user: created_users_list.append(user)
    if any(session.is_modified(obj) for obj in created_users_list if
           obj in session and hasattr(obj, 'roles') and attributes.get_history(obj, 'roles').has_changes()):
        await session.flush();
        print(f"Flushed user creations and role assignments.")
    print(f"Processed {len(created_users_list)} users.")
    return created_users_list


# THIS IS THE FUNCTION THAT WAS MISSING / MISNAMED in populate_database
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
    await session.flush()  # Flush after creating all types
    print(f"Created/found {len(created_types)} reporting unit types.")
    return created_types


# Other create_lookups, create_reporting_units, populate_main_data, populate_transactional_data
# are assumed to be the same as in the V7 complete script provided before, or need similar review
# for consistency with _get_or_create and flushing.

# For brevity, I'll paste the main structure assuming those functions exist from V7.
# You'll need to copy them from the V7 version I provided previously if they are not in your current file.

# --- Placeholder for other create functions from V7 (copy them here) ---
async def get_or_create_reporting_unit(session: AsyncSession, name: str, code: str, unit_type_id: int,
                                       parent_unit_id: Optional[int] = None, description: Optional[str] = None,
                                       area_sqkm: Optional[float] = None,
                                       geom_wkt: Optional[str] = None) -> ReportingUnit:
    defaults = {"name": name, "unit_type_id": unit_type_id, "parent_unit_id": parent_unit_id,
                "description": description, "area_sqkm": area_sqkm}
    instance, created = await _get_or_create(session, ReportingUnit, code=code, defaults=defaults)
    if geom_wkt and (created or not instance.geom):
        try:
            ewkt_with_srid = geom_wkt
            if not geom_wkt.upper().startswith("SRID="): ewkt_with_srid = f"SRID=4326;{geom_wkt}"
            await session.execute(sql_text("UPDATE reporting_units SET geom = ST_GeomFromEWKT(:wkt) WHERE id = :id"),
                                  {"wkt": ewkt_with_srid, "id": instance.id})
        except Exception as e:
            print(f"Error setting geom for RU {code}: {e}")
    return instance


async def create_reporting_units(session: AsyncSession, unit_types: List[ReportingUnitType]) -> List[ReportingUnit]:
    print("Creating reporting units...")
    units = []
    if not unit_types: return units
    country_type = next((ut for ut in unit_types if ut.name == "Country"), unit_types[0])
    country_unit, _ = await _get_or_create(session, ReportingUnit, code="AQT",
                                           defaults={"name": "Republic of Aquaterra", "unit_type_id": country_type.id,
                                                     "area_sqkm": random.uniform(100000, 500000)})
    await session.flush();
    units.append(country_unit)
    province_type = next((ut for ut in unit_types if ut.name == "Province"), unit_types[0])
    for i in range(NUM_REPORTING_UNITS_PER_TYPE_MAIN):
        prov_name = f"Province {chr(65 + i)}";
        prov_code = f"AQT-P{chr(65 + i)}"
        province, _ = await _get_or_create(session, ReportingUnit, code=prov_code,
                                           defaults={"name": prov_name, "unit_type_id": province_type.id,
                                                     "parent_unit_id": country_unit.id,
                                                     "area_sqkm": random.uniform(50000, 200000)})
        await session.flush();
        units.append(province)
        sub_basin_type = next((ut for ut in unit_types if ut.name == "Sub-Basin"), unit_types[0])
        for j in range(NUM_SUB_UNITS_PER_MAIN):
            sub_name = f"{prov_name} Sub-{j + 1}";
            sub_code = f"{prov_code}-SB{j + 1}"
            sub_unit, _ = await _get_or_create(session, ReportingUnit, code=sub_code,
                                               defaults={"name": sub_name, "unit_type_id": sub_basin_type.id,
                                                         "parent_unit_id": province.id,
                                                         "area_sqkm": random.uniform(1000, 10000)})
            units.append(sub_unit)
    await session.flush()
    print(f"Created/found {len(units)} reporting units.")
    return units


async def create_lookups(session: AsyncSession) -> Dict[str, List[Any]]:
    print("Creating lookup tables data...")
    results: Dict[str, List[Any]] = {}
    uom_data = [{"name": "Cubic Meter", "abbreviation": "m³"}, {"name": "Liter per Second", "abbreviation": "l/s"},
                {"name": "Hectare", "abbreviation": "ha"}, {"name": "Ton per Hectare", "abbreviation": "ton/ha"},
                {"name": "Millimeter", "abbreviation": "mm"}]
    results["units_of_measurement"] = [
        await _get_or_create(session, UnitOfMeasurement, {"name": d["name"]}, abbreviation=d["abbreviation"])[0] for d
        in uom_data]
    tr_data = ["Annual", "Monthly", "Daily", "Snapshot"]
    results["temporal_resolutions"] = [await _get_or_create(session, TemporalResolution, name=n)[0] for n in tr_data]
    dqf_data = ["RAW", "VALIDATED", "ESTIMATED"]
    results["data_quality_flags"] = [
        await _get_or_create(session, DataQualityFlag, name=n, defaults={"description": f"{n} data"})[0] for n in
        dqf_data]
    currency_data = [{"code": "USD", "name": "US Dollar"}, {"code": "EUR", "name": "Euro"}]
    results["currencies"] = [await _get_or_create(session, Currency, {"name": d["name"]}, code=d["code"])[0] for d in
                             currency_data]
    crop_data = [{"code": "WHT", "name_en": "Wheat"}, {"code": "RCE", "name_en": "Rice"}]
    results["crops"] = [await _get_or_create(session, Crop, {"name_en": d["name_en"]}, code=d["code"])[0] for d in
                        crop_data]
    it_data = ["Dam", "Canal", "Pumping Station"]
    results["infrastructure_types"] = [
        await _get_or_create(session, InfrastructureType, name=n, defaults={"description": f"{n} type"})[0] for n in
        it_data]
    ost_data = ["Operational", "Maintenance", "Decommissioned"]
    results["operational_status_types"] = [
        await _get_or_create(session, OperationalStatusType, name=n, defaults={"description": f"Status: {n}"})[0] for n
        in ost_data]
    fat_data = [{"name": "Revenue", "is_cost": False}, {"name": "OPEX", "is_cost": True},
                {"name": "CAPEX", "is_cost": True}]
    results["financial_account_types"] = [
        await _get_or_create(session, FinancialAccountType, name=d["name"], defaults={"is_cost": d["is_cost"]})[0] for d
        in fat_data]
    await session.flush()
    print("Lookup data created/verified.")
    return results


async def populate_main_data(session: AsyncSession, lookups: Dict[str, List[Any]], users: List[User],
                             reporting_units: List[ReportingUnit]):
    print("Populating main data entities (IndicatorDefs, Infra)...")
    indicator_categories = []
    cat_hydro, _ = await _get_or_create(session, IndicatorCategory, name_en="Hydrology",
                                        defaults={"name_local": "Hidrologi"})
    indicator_categories.append(cat_hydro)
    await session.flush()

    indicator_definitions = []
    ind_def_base = [{"code": "PRECIP", "name_en": "Precipitation", "data_type": "Numeric", "uom_abbr": "mm",
                     "is_spatial_raster": True},
                    {"code": "Q_RIVER", "name_en": "River Discharge", "data_type": "Numeric", "uom_abbr": "m3/s"}]
    for i_data in ind_def_base:
        uom = next(u for u in lookups["units_of_measurement"] if u.abbreviation == i_data["uom_abbr"])
        idef, _ = await _get_or_create(session, IndicatorDefinition, code=i_data["code"],
                                       defaults={"name_en": i_data["name_en"], "data_type": i_data["data_type"],
                                                 "unit_of_measurement_id": uom.id, "category_id": cat_hydro.id,
                                                 "is_spatial_raster": i_data.get("is_spatial_raster", False)})
        indicator_definitions.append(idef)
    await session.flush()

    infrastructures = []
    dam_type = next(it for it in lookups["infrastructure_types"] if it.name == "Dam")
    op_status = next(os_ for os_ in lookups["operational_status_types"] if os_.name == "Operational")
    for i in range(NUM_INFRASTRUCTURES_TO_CREATE):
        ru = get_random_element(reporting_units)
        infra, _ = await _get_or_create(session, Infrastructure, name=f"{ru.code if ru else 'SYS'}-Dam-{i + 1}",
                                        defaults={"infrastructure_type_id": dam_type.id,
                                                  "reporting_unit_id": ru.id if ru else None,
                                                  "operational_status_id": op_status.id})
        infrastructures.append(infra)
    await session.flush()
    print("Main data entities populated.")
    return {"indicator_definitions": indicator_definitions, "infrastructures": infrastructures}


async def populate_transactional_data(session: AsyncSession, main_entities: Dict[str, List[Any]],
                                      lookups: Dict[str, List[Any]]):
    print("Populating transactional data...")
    # Simplified versions - assuming models and create_..._entry functions exist from V5
    # IndicatorTimeseries
    if main_entities.get("indicator_definitions") and main_entities.get("reporting_units"):
        for _ in range(5):  # Create 5 timeseries entries
            ind_def = get_random_element(main_entities["indicator_definitions"])
            ru = get_random_element(main_entities["reporting_units"])
            tr = get_random_element(lookups["temporal_resolutions"])
            dqf = get_random_element(lookups["data_quality_flags"])
            if ind_def and ru and tr and dqf:
                ts_entry_data = {
                    "indicator_definition_id": ind_def.id, "reporting_unit_id": ru.id,
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                    "value_numeric": random.uniform(1, 100),
                    "temporal_resolution_id": tr.id, "quality_flag_id": dqf.id
                }
                session.add(IndicatorTimeseries(**ts_entry_data))

    # CroppingPattern
    if main_entities.get("reporting_units") and lookups.get("crops"):
        for _ in range(3):
            ru = get_random_element(main_entities["reporting_units"])
            crop = get_random_element(lookups["crops"])
            if ru and crop:
                cp_entry_data = {
                    "reporting_unit_id": ru.id, "crop_id": crop.id,
                    "time_period_year": 2023, "data_type": "Actual",
                    "area_cultivated_ha": random.uniform(10, 100)
                }
                session.add(CroppingPattern(**cp_entry_data))

    # FinancialAccount
    if lookups.get("financial_account_types") and lookups.get("currencies") and main_entities.get("reporting_units"):
        for _ in range(3):
            fat = get_random_element(lookups["financial_account_types"])
            curr = get_random_element(lookups["currencies"])
            ru = get_random_element(main_entities["reporting_units"])
            if fat and curr and ru:
                fa_entry_data = {
                    "financial_account_type_id": fat.id, "currency_id": curr.id,
                    "reporting_unit_id": ru.id,
                    "transaction_date": date(2023, random.randint(1, 12), random.randint(1, 28)),
                    "amount": Decimal(str(random.uniform(1000, 100000))).quantize(Decimal("0.01"))
                }
                session.add(FinancialAccount(**fa_entry_data))

    # RasterMetadata
    if main_entities.get("indicator_definitions"):
        raster_ind = next((id_ for id_ in main_entities["indicator_definitions"] if id_.is_spatial_raster), None)
        if raster_ind:
            rm_entry_data = {
                "layer_name_geoserver": f"{raster_ind.code}_test_raster", "geoserver_workspace": "test_ws",
                "indicator_definition_id": raster_ind.id,
                "timestamp_valid_start": datetime.now(timezone.utc) - timedelta(days=30),
                "storage_path_or_postgis_table": "/test/path.tif"
            }
            session.add(RasterMetadata(**rm_entry_data))

    await session.flush()
    print("Transactional data added (not yet committed).")


# --- Main Orchestrator ---
async def populate_database():
    print("Starting database population process...")
    async with AsyncSessionFactory() as session:
        try:
            print("\n--- STAGE 1: Independent Lookups & Basic Entities ---")
            permissions = await create_permissions(session)
            roles = await create_roles(session, permissions)
            users = await create_users(session, roles)

            ru_types = await create_reporting_unit_types(session)  # This was the missing call
            lookups = await create_lookups(session)

            print("\n--- STAGE 2: Entities with Dependencies on Stage 1 ---")
            # main_entities will contain reporting_units, indicator_definitions, infrastructures
            main_entities = await populate_main_entities(session, lookups, users, ru_types)

            print("\n--- STAGE 3: Transactional Data ---")
            await populate_transactional_data(session, main_entities, lookups)

            await session.commit()
            print("Database population completed successfully!")

        except Exception as e:
            print(f"Error during database population: {e}")
            import traceback
            traceback.print_exc()
            # if session.in_transaction(): await session.rollback() # Context manager handles this
            raise
    print("\nScript finished.")


async def main():
    await populate_database()


if __name__ == "__main__":
    print("Running data population script (populate_user_test.py)...")
    asyncio.run(main())
    print("Script finished. (final print)")