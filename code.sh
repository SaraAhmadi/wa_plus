# Create top-level directories
mkdir alembic
mkdir app
mkdir data_ingestion
mkdir services_external
mkdir tests
mkdir scripts

# --- app ---
cd app
touch __init__.py
touch main.py

mkdir core
cd core
touch __init__.py
touch config.py
cd .. # back to app

mkdir api
cd api
mkdir v1
cd v1
touch __init__.py
touch api_router_v1.py
mkdir endpoints
cd endpoints
touch __init__.py
touch auth.py
touch data_exploration.py
touch map_layers.py
touch exports.py
mkdir admin
cd admin
touch __init__.py # Important for admin to be a package
touch users.py
cd .. # back to endpoints
cd .. # back to v1
cd .. # back to api
cd .. # back to app

mkdir database
cd database
touch __init__.py
touch session.py
mkdir models
cd models
touch __init__.py
touch base_model.py
touch user.py
touch role.py
touch basin.py
touch indicator_timeseries.py
touch raster_metadata.py
cd .. # back to database
cd .. # back to app

mkdir schemas
cd schemas
touch __init__.py
touch user.py
touch token.py
touch basin.py
touch indicator_timeseries.py
touch map_layer.py
cd .. # back to app

mkdir services
cd services
touch __init__.py
touch auth_service.py
touch data_service.py
touch user_service.py
touch export_service.py
cd .. # back to app

mkdir dependencies
cd dependencies
touch __init__.py
touch get_current_user.py
touch get_db_session.py
touch rbac.py
cd .. # back to app

mkdir security
cd security
touch __init__.py
touch hashing.py
touch token_utils.py
cd .. # back to app

mkdir utils
cd utils
touch __init__.py
touch common_helpers.py
cd .. # back to app
cd .. # back to waplus_dashboard_backend

# --- data_ingestion ---
cd data_ingestion
touch __init__.py
touch pipeline.py
mkdir parsers
cd parsers
touch __init__.py # Make parsers a package
cd .. # back to data_ingestion
touch transformers.py
touch loaders.py
cd .. # back to waplus_dashboard_backend

# --- services_external ---
cd services_external
touch __init__.py
touch redis_client.py
cd .. # back to waplus_dashboard_backend

# --- tests ---
cd tests
touch __init__.py
touch conftest.py
mkdir unit
mkdir integration
cd .. # back to waplus_dashboard_backend

# --- scripts ---
# scripts directory already created
# cd scripts
# touch some_script.py # example if you had one
# cd ..

# Create top-level files
touch .env
touch .env.example
touch .gitignore
touch Dockerfile
touch docker-compose.yml
touch pyproject.toml # Or requirements.txt, I'll go with pyproject.toml for modern Python
touch README.md

echo "Folder and file structure created."