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
        print(f"{model_cls.__name__} with {kwargs} already exists (ID: {instance.id}).")
        return instance, False # Return early if found

    # If not found, attempt to create within a savepoint
    params = {**kwargs, **(defaults or {})}
    try:
        async with session.begin_nested() as savepoint:  # Start savepoint
            print(f"Attempting to create {model_cls.__name__} with params: {params} within a savepoint.")
            instance = model_cls(**params)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            created = True
            print(f"Successfully created and flushed {model_cls.__name__} (ID: {instance.id}) within savepoint.")
            # Savepoint is committed automatically if this block completes without error

    except IntegrityError as e:
        # Savepoint is automatically rolled back by 'async with' on exception
        print(f"IntegrityError for {model_cls.__name__} with params {params} during savepoint. Savepoint rolled back. Attempting to fetch conflicting record.")

        fetched_instance = None
        # Try fetching by unique fields that might have caused the conflict.
        if 'name' in params and hasattr(model_cls, 'name'):
            stmt_alt_name = select(model_cls).filter_by(name=params['name'])
            result_alt_name = await session.execute(stmt_alt_name)
            fetched_instance = result_alt_name.scalars().first()

        if not fetched_instance:
            # Try again with original kwargs, in case of a race condition
            stmt_alt_kwargs = select(model_cls).filter_by(**kwargs)
            result_alt_kwargs = await session.execute(stmt_alt_kwargs)
            fetched_instance = result_alt_kwargs.scalars().first()

        if fetched_instance:
            instance = fetched_instance
            created = False # Not created by this call
            print(f"Found existing {model_cls.__name__} (ID: {instance.id}) after IntegrityError and savepoint rollback.")
        else:
            print(f"Could not find conflicting {model_cls.__name__} after IntegrityError and savepoint rollback. Re-raising original error.")
            raise e  # Re-raise the original integrity error

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
        # "manage_users" is generic, "users:manage" is more specific. Will use specific one for now.
        # {"name": "manage_users", "description": "Can create, edit, delete users"},
        {"name": "manage_roles", "description": "Can create, edit, delete roles"},
        {"name": "enter_basin_data", "description": "Can enter data for any basin"},
        {"name": "approve_basin_data", "description": "Can approve data for any basin"},
        {"name": "view_financial_reports", "description": "Can view financial reports"},
        {"name": "manage_infrastructure_data", "description": "Can manage infrastructure records"},
        # Added from populate_test_data.py
        {"name": "data:view:all", "description": "Can view all data."},
        {"name": "settings:edit:basin_A", "description": "Can edit settings for Basin A."},
        {"name": "users:manage", "description": "Can manage users and roles."} # Specific version for user management
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

    # Helper to find permissions by name for role definitions
    def get_perms_by_names(names: List[str]) -> List[Permission]:
        return [p for p in all_permissions if p.name in names]

    roles_data_from_script = [
        {
            "name": "Administrator",
            "description": "System Administrator",
            # Assign all known specific permissions. The original "all_permissions" was too broad if new permissions are added.
            "permissions_to_link": get_perms_by_names([
                "data:view:all", "users:manage", "settings:edit:basin_A",
                "view_all_dashboards", "manage_roles", "enter_basin_data",
                "approve_basin_data", "view_financial_reports", "manage_infrastructure_data"
            ])
        },
        {
            "name": "DataManager",
            "description": "Manages data",
            "permissions_to_link": get_perms_by_names([
                "data:view:all", "view_all_dashboards", "enter_basin_data", "approve_basin_data",
                "manage_infrastructure_data" # DataManagers might manage infrastructure
            ])
        },
        {
            "name": "ReportingAnalyst",
            "description": "Views data and reports",
            "permissions_to_link": get_perms_by_names(["data:view:all", "view_all_dashboards", "view_financial_reports"])
        },
        { # Added from populate_test_data.py
            "name": "DataViewer",
            "description": "Can view data.",
            "permissions_to_link": get_perms_by_names(["data:view:all", "view_all_dashboards"])
        }
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
    instance, created = await _get_or_create(
        session, ReportingUnit, code=code, defaults=defaults
    )

    if geom_wkt and (created or not instance.geom):
        try:
            # Use WKTElement instead of raw SQL
            instance.geom = WKTElement(geom_wkt, srid=4326)
            session.add(instance)
            await session.flush([instance])  # Flush only this instance
        except Exception as e:
            print(f"Error setting geom for RU {code}: {e}")
            # Explicit rollback for this operation
            if session.in_transaction():
                await session.rollback()
            # Re-raise to handle at higher level
            raise

    return instance, created


async def create_reporting_units(session: AsyncSession, unit_types: List[ReportingUnitType]) -> List[ReportingUnit]:
    print("Creating reporting units...")
    units = []
    if not unit_types:
        print("Warning: No reporting unit types provided to create_reporting_units.")
        return units

    # Fetch specific unit types, falling back to the first available if not found
    type_country = next((ut for ut in unit_types if ut.name == "Country"), unit_types[0])
    type_basin = next((ut for ut in unit_types if ut.name == "River Basin"), unit_types[0])
    type_sub_basin = next((ut for ut in unit_types if ut.name == "Sub-Basin"), unit_types[0])

    # Create "Republic of Aquaterra" and its sub-units (existing logic)
    aqt_country_unit, _ = await _get_or_create(session, ReportingUnit, code="AQT",
                                               defaults={"name": "Republic of Aquaterra", "unit_type_id": type_country.id,
                                                         "area_sqkm": random.uniform(100000, 500000)})
    await session.flush()
    units.append(aqt_country_unit)

    province_type = next((ut for ut in unit_types if ut.name == "Province"), unit_types[0])
    for i in range(NUM_REPORTING_UNITS_PER_TYPE_MAIN):
        prov_name = f"Province {chr(65 + i)}"
        prov_code = f"AQT-P{chr(65 + i)}"
        province, _ = await _get_or_create(session, ReportingUnit, code=prov_code,
                                           defaults={"name": prov_name, "unit_type_id": province_type.id,
                                                     "parent_unit_id": aqt_country_unit.id,
                                                     "area_sqkm": random.uniform(50000, 200000)})
        await session.flush()
        units.append(province)

        # Using type_sub_basin for these generic sub-units for consistency
        for j in range(NUM_SUB_UNITS_PER_MAIN):
            sub_name = f"{prov_name} Sub-{j + 1}"
            sub_code = f"{prov_code}-SB{j + 1}"
            sub_unit, _ = await _get_or_create(session, ReportingUnit, code=sub_code,
                                               defaults={"name": sub_name, "unit_type_id": type_sub_basin.id,
                                                         "parent_unit_id": province.id,
                                                         "area_sqkm": random.uniform(1000, 10000)})
            units.append(sub_unit)

    # Create specific units from populate_test_data.py
    # 1. Country X
    country_x, _ = await get_or_create_reporting_unit(
        session, name="Country X", code="CX", unit_type_id=type_country.id, area_sqkm=1200000.0
    )
    units.append(country_x)

    # 2. Blue River Basin
    wkt_brb = "MULTIPOLYGON(((30 -10, 40 -20, 35 -25, 30 -10)))"
    blue_river_basin, _ = await get_or_create_reporting_unit(
        session, name="Blue River Basin", code="BRB", unit_type_id=type_basin.id,
        parent_unit_id=country_x.id, area_sqkm=50000.0, geom_wkt=wkt_brb
    )
    units.append(blue_river_basin)

    # 3. Upper Blue Sub-basin
    upper_blue_subbasin, _ = await get_or_create_reporting_unit(
        session, name="Upper Blue Sub-basin", code="UBSB", unit_type_id=type_sub_basin.id,
        parent_unit_id=blue_river_basin.id, area_sqkm=15000.0
    )
    units.append(upper_blue_subbasin)

    await session.flush()
    print(f"Created/found {len(units)} reporting units.")
    return units


async def create_lookups(session: AsyncSession) -> Dict[str, List[Any]]:
    print("Creating lookup tables data...")
    results: Dict[str, List[Any]] = {}
    uom_data = [
        {"name": "Cubic Meter", "abbreviation": "m³"},
        {"name": "Cubic Meter per Second", "abbreviation": "m3/s"}, # Added
        {"name": "Liter per Second", "abbreviation": "l/s"},
        {"name": "Hectare", "abbreviation": "ha"},
        {"name": "Ton per Hectare", "abbreviation": "t/ha"}, # Standardized abbreviation
        {"name": "Millimeter", "abbreviation": "mm"},
        {"name": "Million Cubic Meters", "abbreviation": "MCM"}  # Added
    ]
    results["units_of_measurement"] = [
        (await _get_or_create(session, UnitOfMeasurement, {"name": d["name"]}, abbreviation=d["abbreviation"]))[0] for d
        in uom_data]

    tr_data = ["Annual", "Monthly", "Daily", "Snapshot"] # Already comprehensive
    results["temporal_resolutions"] = [(await _get_or_create(session, TemporalResolution, name=n))[0] for n in tr_data]
    dqf_data = ["RAW", "VALIDATED", "ESTIMATED", "Measured"] # Added "Measured"
    results["data_quality_flags"] = [
        (await _get_or_create(session, DataQualityFlag, name=n, defaults={"description": f"{n} data"}))[0] for n in
        dqf_data]
    currency_data = [
        {"code": "USD", "name": "US Dollar"},
        {"code": "EUR", "name": "Euro"},
        {"code": "IRR", "name": "Iranian Rial"} # Added
    ]
    results["currencies"] = [(await _get_or_create(session, Currency, {"name": d["name"]}, code=d["code"]))[0] for d in
                             currency_data]
    crop_data = [
        {"code": "WHT", "name_en": "Wheat"},
        {"code": "RCE", "name_en": "Rice"},
        {"code": "MAZ", "name_en": "Maize"} # Added
    ]

    tr_data = ["Annual", "Monthly", "Daily", "Snapshot"]
    results["temporal_resolutions"] = [(await _get_or_create(session, TemporalResolution, name=n))[0] for n in tr_data]
    dqf_data = ["RAW", "VALIDATED", "ESTIMATED"]
    results["data_quality_flags"] = [
        (await _get_or_create(session, DataQualityFlag, name=n, defaults={"description": f"{n} data"}))[0] for n in
        dqf_data]
    currency_data = [{"code": "USD", "name": "US Dollar"}, {"code": "EUR", "name": "Euro"}]
    results["currencies"] = [(await _get_or_create(session, Currency, {"name": d["name"]}, code=d["code"]))[0] for d in
                             currency_data]
    crop_data = [{"code": "WHT", "name_en": "Wheat"}, {"code": "RCE", "name_en": "Rice"}]

    results["crops"] = [(await _get_or_create(session, Crop, {"name_en": d["name_en"]}, code=d["code"]))[0] for d in
                        crop_data]
    it_data = ["Dam", "Canal", "Pumping Station"] # Already comprehensive
    results["infrastructure_types"] = [
        (await _get_or_create(session, InfrastructureType, name=n, defaults={"description": f"{n} type"}))[0] for n in
        it_data]
    ost_data = ["Operational", "Maintenance", "Decommissioned"]
    results["operational_status_types"] = [
        (await _get_or_create(session, OperationalStatusType, name=n, defaults={"description": f"Status: {n}"}))[0] for n
        in ost_data]
    fat_data = [{"name": "Revenue", "is_cost": False}, {"name": "OPEX", "is_cost": True},
                {"name": "CAPEX", "is_cost": True}]
    results["financial_account_types"] = [
        (await _get_or_create(session, FinancialAccountType, name=d["name"], defaults={"is_cost": d["is_cost"]}))[0] for d
        in fat_data]
    await session.flush()
    print("Lookup data created/verified.")
    return results


async def populate_main_data(session: AsyncSession, lookups: Dict[str, List[Any]], users: List[User],
                             reporting_units: List[ReportingUnit]):
    print("Populating main data entities (IndicatorDefs, Infra)...")

    # --- Ensure specific Reporting Units are available for linking ---
    # These were created in create_reporting_units, now fetch them for use here.
    ru_blue_river_basin, _ = await _get_or_create(session, ReportingUnit, code="BRB")
    ru_upper_blue_subbasin, _ = await _get_or_create(session, ReportingUnit, code="UBSB")

    # --- Indicator Categories ---
    indicator_categories = {} # Use a dict for easier lookup
    cat_hydro, _ = await _get_or_create(session, IndicatorCategory, name_en="Hydrology",
                                        defaults={"name_local": "Hidrologi"})
    indicator_categories["Hydrology"] = cat_hydro
    cat_agri, _ = await _get_or_create(session, IndicatorCategory, name_en="Agriculture",
                                       defaults={"name_local": "Pertanian"})
    indicator_categories["Agriculture"] = cat_agri
    await session.flush()

    # --- Indicator Definitions ---
    indicator_definitions = {} # Use a dict for easier lookup by code

    # Existing generic definitions
    ind_def_precip_data = {"code": "PRECIP", "name_en": "Precipitation", "data_type": "Numeric", "uom_abbr": "mm", "is_spatial_raster": True, "category_name": "Hydrology"}
    ind_def_qriver_data = {"code": "Q_RIVER", "name_en": "River Discharge", "data_type": "Numeric", "uom_abbr": "m3/s", "category_name": "Hydrology"}

    # (P_TOTAL from description seems to be same as PRECIP)

    for i_data in [ind_def_precip_data, ind_def_qriver_data]:
        uom = next((u for u in lookups["units_of_measurement"] if u.abbreviation == i_data["uom_abbr"]), None)
        category = indicator_categories.get(i_data["category_name"])
        if not uom: print(f"Warning: UoM {i_data['uom_abbr']} not found for indicator {i_data['code']}. Skipping."); continue
        if not category: print(f"Warning: Category {i_data['category_name']} not found for indicator {i_data['code']}. Skipping."); continue

        idef, _ = await _get_or_create(session, IndicatorDefinition, code=i_data["code"],
                                       defaults={"name_en": i_data["name_en"], "data_type": i_data["data_type"],
                                                 "unit_of_measurement_id": uom.id, "category_id": category.id,
                                                 "is_spatial_raster": i_data.get("is_spatial_raster", False)})
        indicator_definitions[i_data["code"]] = idef
    await session.flush()

    # --- Infrastructures ---
    infrastructures = {} # Use a dict for easier lookup

    # Create generic infrastructures
    dam_type_generic = next((it for it in lookups["infrastructure_types"] if it.name == "Dam"), None)
    op_status_generic = next((os_ for os_ in lookups["operational_status_types"] if os_.name == "Operational"), None)

    if dam_type_generic and op_status_generic:
        for i in range(NUM_INFRASTRUCTURES_TO_CREATE):
            # Link generic dams to random RUs from the broader list for variety
            random_ru_for_generic_dam = get_random_element(reporting_units)
            infra, _ = await _get_or_create(session, Infrastructure, name=f"{random_ru_for_generic_dam.code if random_ru_for_generic_dam else 'SYS'}-Dam-{i + 1}",
                                            defaults={"infrastructure_type_id": dam_type_generic.id,
                                                      "reporting_unit_id": random_ru_for_generic_dam.id if random_ru_for_generic_dam else None,
                                                      "operational_status_id": op_status_generic.id})
            # infrastructures.append(infra) # Not storing generic ones in the dict by name for now

    # Create specific "Blue Grand Dam"
    dam_type_specific = next((it for it in lookups["infrastructure_types"] if it.name == "Dam"), None)
    op_status_specific = next((os_ for os_ in lookups["operational_status_types"] if os_.name == "Operational"), None)
    uom_mcm = next((uom for uom in lookups["units_of_measurement"] if uom.abbreviation == "MCM"), None)

    if dam_type_specific and op_status_specific and uom_mcm and ru_blue_river_basin:
        dam_blue_grand, _ = await _get_or_create(
            session, Infrastructure,
            name="Blue Grand Dam",
            defaults={
                "infrastructure_type_id": dam_type_specific.id,
                "reporting_unit_id": ru_blue_river_basin.id,
                "operational_status_id": op_status_specific.id,
                "capacity_value": Decimal("120.5"),
                "capacity_unit_id": uom_mcm.id,
                "construction_year": 2005
            }
        )
        infrastructures["Blue Grand Dam"] = dam_blue_grand
    else:
        print("Warning: Could not create 'Blue Grand Dam' due to missing dependencies (type, status, UoM, or RU).")

    await session.flush()
    print("Main data entities populated.")

    # Prepare entities to be passed to transactional data population
    entities_for_transactional = {
        "indicator_definitions_dict": indicator_definitions, # Pass the dict
        "infrastructures_dict": infrastructures, # Pass the dict
        "reporting_units_all": reporting_units, # Pass the full list for random selection
        "ru_upper_blue_subbasin": ru_upper_blue_subbasin,
        "dam_blue_grand": infrastructures.get("Blue Grand Dam"),
        "crop_wheat": next((c for c in lookups.get("crops", []) if c.code == "WHT"), None),
        # Pass all lookups as well
        "lookups": lookups
    }
    return entities_for_transactional


async def populate_transactional_data(session: AsyncSession, main_entities: Dict[str, Any],
                                      lookups: Dict[str, List[Any]]): # lookups is already in main_entities
    print("Populating transactional data...")

    # Retrieve necessary entities from main_entities
    indicator_definitions_dict = main_entities.get("indicator_definitions_dict", {})
    ru_upper_blue_subbasin = main_entities.get("ru_upper_blue_subbasin")
    dam_blue_grand = main_entities.get("dam_blue_grand")
    crop_wheat = main_entities.get("crop_wheat")
    # lookups are now nested in main_entities
    internal_lookups = main_entities.get("lookups", {})


    # 1. Specific IndicatorTimeseries
    def_q_river = indicator_definitions_dict.get("Q_RIVER")
    def_precip = indicator_definitions_dict.get("PRECIP")
    tr_daily = next((tr for tr in internal_lookups.get("temporal_resolutions", []) if tr.name == "Daily"), None)
    dqf_measured = next((dqf for dqf in internal_lookups.get("data_quality_flags", []) if dqf.name == "Measured"), None)

    if def_q_river and ru_upper_blue_subbasin and tr_daily and dqf_measured:
        for i in range(3): # Create a few data points
            session.add(IndicatorTimeseries(
                indicator_definition_id=def_q_river.id,
                reporting_unit_id=ru_upper_blue_subbasin.id,
                timestamp=datetime(2023, 1, 15 + i, tzinfo=timezone.utc),
                value_numeric=random.uniform(50, 150),
                temporal_resolution_id=tr_daily.id,
                quality_flag_id=dqf_measured.id
            ))
    if def_precip and ru_upper_blue_subbasin and tr_daily and dqf_measured:
        for i in range(3):
             session.add(IndicatorTimeseries(
                indicator_definition_id=def_precip.id,
                reporting_unit_id=ru_upper_blue_subbasin.id,
                timestamp=datetime(2023, 1, 15 + i, tzinfo=timezone.utc),
                value_numeric=random.uniform(1, 20),
                temporal_resolution_id=tr_daily.id,
                quality_flag_id=dqf_measured.id
            ))

    # 2. Specific RasterMetadata
    if def_precip:
        session.add(RasterMetadata(
            layer_name_geoserver="brb_rainfall_2023_01", # Specific name
            geoserver_workspace="basins", # Example workspace
            indicator_definition_id=def_precip.id,
            timestamp_valid_start=datetime(2023, 1, 1, tzinfo=timezone.utc),
            timestamp_valid_end=datetime(2023, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
            storage_path_or_postgis_table="s3://bucket/brb_rainfall_2023_01.tif" # Example path
        ))

    # 3. Specific CroppingPattern
    if crop_wheat and ru_upper_blue_subbasin:
        session.add(CroppingPattern(
            reporting_unit_id=ru_upper_blue_subbasin.id,
            crop_id=crop_wheat.id,
            time_period_year=2023,
            data_type="Planned", # Example data type
            area_cultivated_ha=Decimal("1200.75"),
            yield_value=Decimal("4.5"),
            consumption_value_m3=Decimal("6000.0")
        ))

    # 4. Specific FinancialAccount for Blue Grand Dam
    fac_type_opex = next((ft for ft in internal_lookups.get("financial_account_types", []) if ft.name == "OPEX"), None)
    curr_usd = next((c for c in internal_lookups.get("currencies", []) if c.code == "USD"), None)
    if dam_blue_grand and fac_type_opex and curr_usd:
        session.add(FinancialAccount(
            financial_account_type_id=fac_type_opex.id,
            currency_id=curr_usd.id,
            infrastructure_id=dam_blue_grand.id, # Link to specific dam
            transaction_date=date(2023, 3, 15),
            amount=Decimal("-25000.00"), # Cost is negative
            description="Annual operational cost for Blue Grand Dam"
        ))

    # --- Existing Generic Transactional Data ---
    # Keep some generic data creation if desired, adapting to use main_entities.get("reporting_units_all") etc.
    # For now, focusing on adding specific data. The original generic loops are commented out or removed below for clarity.

    # Original generic IndicatorTimeseries loop (example of adaptation)
    # if main_entities.get("indicator_definitions_dict") and main_entities.get("reporting_units_all"):
    #     all_indicator_defs = list(main_entities["indicator_definitions_dict"].values())
    #     for _ in range(5):
    #         ind_def = get_random_element(all_indicator_defs)
    #         ru = get_random_element(main_entities["reporting_units_all"])
    #         # ... rest of the logic ...
    #         if ind_def and ru and tr and dqf:
    #             # ... session.add ...

    await session.flush()
    print("Transactional data (specific and potentially generic) added.")


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
            # reporting_units_all now contains both generic and specific RUs
            reporting_units_all = await create_reporting_units(session, ru_types)
            lookups = await create_lookups(session)

            print("\n--- STAGE 2: Entities with Dependencies on Stage 1 (includes specific ones) ---")
            # main_entities will now include specific items like dam_blue_grand, ru_upper_blue_subbasin etc.
            # It also receives all reporting_units created to choose from for generic items.
            main_data_entities = await populate_main_data(session, lookups, users, reporting_units_all)

            print("\n--- STAGE 3: Transactional Data (includes specific entries) ---")
            # Pass main_data_entities which now contains the specific items and lookups
            await populate_transactional_data(session, main_data_entities, lookups) # lookups is also in main_data_entities

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
    print("Running data population script (populate_data_test.py)...")
    asyncio.run(main())
    print("Script finished. (final print)")