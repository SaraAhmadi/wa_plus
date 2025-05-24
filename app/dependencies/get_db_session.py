from app.database.session import get_async_db_session

# Re-export for cleaner imports in API routes
# Example usage in an endpoint: async def my_endpoint(db: AsyncSession = Depends(get_db)):
get_db = get_async_db_session
