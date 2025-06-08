from typing import List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert  # For upserts

# Import your SQLAlchemy models from app.database.models
# This creates a dependency on the main app's models, which is okay
# if ingestion scripts are run in an environment where `app` is accessible.
# Alternatively, define SQLAlchemy models separately for ingestion if it's fully decoupled.
from app.database.models import (
    IndicatorTimeseries, ReportingUnit, IndicatorDefinition, Crop, CroppingPattern  # etc.
)


# from app.database.session import AsyncSessionFactory # If running standalone and need sessions

class BaseLoader:
    def __init__(self, db_session: AsyncSession):  # Or AsyncSessionFactory if creating sessions here
        self.db_session = db_session

    async def load(self, records: List[Dict[str, Any]], model_cls: Type, upsert: bool = False,
                   conflict_target_columns: Optional[List[str]] = None) -> int:
        """
        Loads a list of records (dictionaries) into the specified SQLAlchemy model.
        Returns the number of records successfully processed/attempted.
        """
        count = 0
        if not records:
            return 0

        # Map dict keys to model columns if needed, or assume they match
        # For simplicity, assume keys in `record` match `model_cls` attributes.

        if upsert and conflict_target_columns:
            # Prepare for bulk upsert
            # This requires the records to be dicts that match model fields
            stmt = pg_insert(model_cls).values(records)

            # Define columns to update on conflict
            update_columns = {
                col.name: getattr(stmt.excluded, col.name)
                for col in model_cls.__table__.columns
                if col.name not in conflict_target_columns and not col.primary_key
            }

            if update_columns:  # Only add do_update if there are columns to update
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_target_columns,  # Columns forming the unique constraint
                    set_=update_columns
                )
            else:  # If no columns to update (e.g. only primary key and conflict target)
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_target_columns)

            try:
                await self.db_session.execute(stmt)
                await self.db_session.commit()
                count = len(records)
                print(f"Successfully upserted {count} records into {model_cls.__tablename__}.")
            except Exception as e:
                await self.db_session.rollback()
                print(f"Error during bulk upsert to {model_cls.__tablename__}: {e}")
                # Fallback to row-by-row or raise error
                # For simplicity, we are not doing row-by-row fallback here
                return 0  # Indicate failure or partial success if some rows caused issues
        else:  # Simple bulk insert (or row-by-row if preferred for error handling)
            try:
                # SQLAlchemy 2.0 style bulk insert
                self.db_session.add_all([model_cls(**record) for record in records])
                await self.db_session.commit()
                count = len(records)
                print(f"Successfully inserted {count} records into {model_cls.__tablename__}.")
            except Exception as e:
                await self.db_session.rollback()
                print(f"Error during bulk insert to {model_cls.__tablename__}: {e}")
                # Consider row-by-row insert with individual error handling as a fallback
                # for record_data in records:
                #     try:
                #         db_obj = model_cls(**record_data)
                #         self.db_session.add(db_obj)
                #         await self.db_session.commit() # Commit each? Or batch commits
                #         count += 1
                #     except Exception as ex_row:
                #         await self.db_session.rollback()
                #         print(f"Error inserting record {record_data}: {ex_row}")
                return 0
        return count

# Example:
# async def load_indicator_data(db: AsyncSession, data_to_load: List[Dict[str, Any]]):
#     loader = BaseLoader(db)
#     # Assuming 'data_to_load' dict keys match IndicatorTimeseries model fields
#     # and foreign keys (like indicator_definition_id) are already resolved to IDs.
#     await loader.load(data_to_load, IndicatorTimeseries, upsert=True,
#     conflict_target_columns=['indicator_definition_id', 'timestamp', 'reporting_unit_id'])
