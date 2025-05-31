import json

collection = {
    "info": {
        "_postman_id": "YOUR_COLLECTION_ID",  # Replace with a unique ID
        "name": "WAPlus Dashboard API",
        "description": "This collection contains requests for the WAPlus Dashboard API.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "auth": {
        "type": "bearer",
        "bearer": [
            {"key": "token", "value": "{{access_token}}", "type": "string"}
        ]
    },
    "item": []  # Initialize with an empty list of items
}

# Define the login request
login_request = {
    "name": "Login",
    "request": {
        "method": "POST",
        "header": [],
        "body": {
            "mode": "urlencoded",
            "urlencoded": [
                {"key": "username", "value": "user@example.com", "type": "text"},
                {"key": "password", "value": "string", "type": "text"}
            ]
        },
        "url": {
            "raw": "{{baseUrl}}/api/v1/auth/login",
            "host": ["{{baseUrl}}"],
            "path": ["api", "v1", "auth", "login"]
        },
        "description": "Authenticate to get the access token."
    },
    "event": [
        {
            "listen": "test",
            "script": {
                "exec": [
                    "if (pm.response.code === 200) {",
                    "    pm.collectionVariables.set(\"access_token\", pm.response.json().access_token);",
                    "}"
                ],
                "type": "text/javascript"
            }
        }
    ],
    "response": []
}
collection["item"].append(login_request)

# Define the "Get Current User" request
get_current_user_request = {
    "name": "Get Current User",
    "request": {
        "method": "GET",
        "header": [],
        "url": {
            "raw": "{{baseUrl}}/api/v1/auth/me",
            "host": ["{{baseUrl}}"],
            "path": ["api", "v1", "auth", "me"]
        },
        "description": "Retrieves the currently authenticated user's details."
    },
    "response": []
}
collection["item"].append(get_current_user_request)

# Define the "Admin - Users" folder and its requests
admin_users_folder = {
    "name": "Admin - Users",
    "item": [
        {
            "name": "Create User",
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "email": "newuser@example.com", "password": "newpassword", "username": "newusername",
                        "full_name": "New User Full Name", "is_active": True, "is_superuser": False
                    }, indent=4),
                    "options": {"raw": {"language": "json"}}
                },
                "url": {
                    "raw": "{{baseUrl}}/api/v1/admin/users/", "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "admin", "users", ""]
                },
                "description": "Create new user by an admin. Requires superuser privileges."
            }, "response": []
        },
        {
            "name": "List Users",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/admin/users/?skip=0&limit=10&filter_params=%7B%22username%22%3A%20%22test%22%7D",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "admin", "users", ""],
                    "query": [
                        {"key": "skip", "value": "0"}, {"key": "limit", "value": "10"},
                        {"key": "filter_params", "value": "{\"username\": \"test\"}", "disabled": True}
                    ]
                },
                "description": "Read users with pagination. Requires superuser privileges."
            }, "response": []
        },
        {
            "name": "Get User by ID",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/admin/users/{{user_id}}", "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "admin", "users", "{{user_id}}"],
                    "variable": [{"key": "user_id", "value": "1"}]
                },
                "description": "Get a specific user by ID. Requires superuser privileges."
            }, "response": []
        },
        {
            "name": "Update User",
            "request": {
                "method": "PUT", "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "email": "updateduser@example.com", "password": "updatedpassword",
                        "username": "updatedusername", "full_name": "Updated User Full Name",
                        "is_active": True, "is_superuser": False
                    }, indent=4),
                    "options": {"raw": {"language": "json"}}
                },
                "url": {
                    "raw": "{{baseUrl}}/api/v1/admin/users/{{user_id}}", "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "admin", "users", "{{user_id}}"],
                    "variable": [{"key": "user_id", "value": "1"}]
                },
                "description": "Update a user. Requires superuser privileges."
            }, "response": []
        },
        {
            "name": "Delete User",
            "request": {
                "method": "DELETE", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/admin/users/{{user_id}}", "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "admin", "users", "{{user_id}}"],
                    "variable": [{"key": "user_id", "value": "1"}]
                },
                "description": "Deactivate a user (soft delete). Requires superuser privileges."
            }, "response": []
        }
    ]
}
collection["item"].append(admin_users_folder)

# Define the "Metadata Catalog" folder and its requests
metadata_catalog_folder = {
    "name": "Metadata Catalog",
    "item": [
        {
            "name": "Get Geographic Units",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/geographic-units?skip=0&limit=100",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "geographic-units"],
                    "query": [
                        {"key": "unit_type_id", "value": "", "disabled": True, "description": "(integer, optional)"},
                        {"key": "parent_unit_id", "value": "", "disabled": True, "description": "(integer, optional)"},
                        {"key": "search", "value": "", "disabled": True, "description": "(string, optional)"},
                        {"key": "skip", "value": "0"},
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "Retrieve a list of available geographic/reporting units."
            }, "response": []
        },
        {
            "name": "Get Geographic Unit by ID",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/geographic-units/{{unit_id}}",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "geographic-units", "{{unit_id}}"],
                    "variable": [{"key": "unit_id", "value": "1", "description": "(integer)"}]
                },
                "description": "Retrieve a specific geographic/reporting unit by its ID."
            }, "response": []
        },
        {
            "name": "Get Geographic Unit Types",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/geographic-unit-types",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "geographic-unit-types"]
                },
                "description": "Retrieve a list of available geographic/reporting unit types."
            }, "response": []
        },
        {
            "name": "Get Indicators",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/indicators?skip=0&limit=100",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "indicators"],
                    "query": [
                        {"key": "category_id", "value": "", "disabled": True, "description": "(integer, optional)"},
                        {"key": "data_type", "value": "", "disabled": True, "description": "(string, optional)"},
                        {"key": "skip", "value": "0"},
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "Retrieve a list of available WA+ indicator definitions."
            }, "response": []
        },
        {
            "name": "Get Indicator by Code",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/indicators/{{indicator_code}}",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "indicators", "{{indicator_code}}"],
                    "variable": [{"key": "indicator_code", "value": "WP", "description": "(string)"}]
                },
                "description": "Retrieve a specific indicator definition by its code."
            }, "response": []
        },
        {
            "name": "Get Indicator Categories",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/indicator-categories",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "indicator-categories"]
                },
                "description": "Retrieve available indicator categories."
            }, "response": []
        },
        {
            "name": "Get Units of Measurement",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/units-of-measurement",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "units-of-measurement"]
                },
                "description": "Retrieve available units of measurement."
            }, "response": []
        },
        {
            "name": "Get Temporal Resolutions",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/temporal-resolutions",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "temporal-resolutions"]
                },
                "description": "Retrieve available temporal resolutions. (Currently not fully implemented in service)"
            }, "response": []
        },
        {
            "name": "Get Data Quality Flags",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/data-quality-flags",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "data-quality-flags"]
                },
                "description": "Retrieve available data quality flags. (Currently not fully implemented in service)"
            }, "response": []
        },
        {
            "name": "Get Infrastructure Types",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/infrastructure-types",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "infrastructure-types"]
                },
                "description": "Retrieve available infrastructure types."
            }, "response": []
        },
        {
            "name": "Get Crops",
            "request": {
                "method": "GET", "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/metadata/crops?skip=0&limit=100",
                    "host": ["{{baseUrl}}"], "path": ["api", "v1", "metadata", "crops"],
                    "query": [
                        {"key": "skip", "value": "0"},
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "Retrieve a list of available crop types. (Currently not fully implemented in service)"
            }, "response": []
        }
    ]
}
collection["item"].append(metadata_catalog_folder)

# Define the "Time Series Data" folder and its requests
time_series_data_folder = {
    "name": "Time Series Data",
    "item": [
        {
            "name": "Get Time Series Data",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/timeseries/?indicator_codes=WP%2CETa&start_date=2023-01-01T00%3A00%3A00Z&end_date=2023-12-31T23%3A59%3A59Z&reporting_unit_ids=1%2C2%2C3",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "timeseries", ""],
                    "query": [
                        {
                            "key": "indicator_codes", "value": "WP,ETa",
                            "description": "Comma-separated list of indicator codes."
                        },
                        {
                            "key": "start_date", "value": "2023-01-01T00:00:00Z",
                            "description": "ISO format datetime string"
                        },
                        {
                            "key": "end_date", "value": "2023-12-31T23:59:59Z",
                            "description": "ISO format datetime string"
                        },
                        {
                            "key": "reporting_unit_ids", "value": "1,2,3",
                            "description": "Comma-separated list of reporting unit IDs (optional, but either this or infrastructure_ids is required)",
                            "disabled": False
                        },
                        {
                            "key": "infrastructure_ids", "value": "10,11",
                            "description": "Comma-separated list of infrastructure unit IDs (optional, but either this or reporting_unit_ids is required)",
                            "disabled": True
                        },
                        {
                            "key": "temporal_resolution_name", "value": "Daily",
                            "description": "(string, optional)", "disabled": True
                        },
                        {
                            "key": "aggregate_to", "value": "Monthly",
                            "description": "(string, optional)", "disabled": True
                        }
                    ]
                },
                "description": "Retrieve time-series data for specified indicators and locations/units. Requires authentication. Either reporting_unit_ids or infrastructure_ids must be provided."
            },
            "response": []
        }
    ]
}
collection["item"].append(time_series_data_folder)

# Define the "Summary Data" folder and its requests
summary_data_folder = {
    "name": "Summary Data",
    "item": [
        {
            "name": "Get Summary Statistics",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/api/v1/summary-data/?indicator_codes=WP%2CETa&time_period_start=2023-01-01T00%3A00%3A00Z&time_period_end=2023-12-31T23%3A59%3A59Z&aggregation_method=Average",
                    "host": ["{{baseUrl}}"],
                    "path": ["api", "v1", "summary-data", ""],
                    "query": [
                        {
                            "key": "indicator_codes",
                            "value": "WP,ETa",
                            "description": "Comma-separated list of indicator codes."
                        },
                        {
                            "key": "time_period_start",
                            "value": "2023-01-01T00:00:00Z",
                            "description": "ISO format datetime string for the start of the period."
                        },
                        {
                            "key": "time_period_end",
                            "value": "2023-12-31T23:59:59Z",
                            "description": "ISO format datetime string for the end of the period."
                        },
                        {
                            "key": "reporting_unit_ids",
                            "value": "1,2,3",
                            "description": "Comma-separated list of reporting unit IDs.",
                            "disabled": True
                        },
                        {
                            "key": "infrastructure_ids",
                            "value": "10,11",
                            "description": "Comma-separated list of infrastructure IDs.",
                            "disabled": True
                        },
                        {
                            "key": "aggregation_method",
                            "value": "Average",
                            "description": "Method for aggregation (e.g., 'Average', 'Sum', 'Min', 'Max', 'Count')."
                        }
                    ]
                },
                "description": "Retrieve aggregated/summary data for comparisons or KPIs. Requires authentication."
            },
            "response": []
        }
    ]
}
collection["item"].append(summary_data_folder)


with open("postman_collection.json", "w") as f:
    json.dump(collection, f, indent=4)

print("Postman collection generated successfully with summary_data folder: postman_collection.json")
