"""Initialize databases and user for local development."""

import asyncio

import asyncpg


async def main() -> None:
    conn = await asyncpg.connect(
        "postgresql://postgres@localhost:5432/postgres"
    )

    for db_name in ["activia_trace", "activia_trace_test"]:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database: {db_name}")
        else:
            print(f"Database already exists: {db_name}")

    user_exists = await conn.fetchval(
        "SELECT 1 FROM pg_roles WHERE rolname = 'app_user'"
    )
    if not user_exists:
        await conn.execute("CREATE USER app_user WITH PASSWORD 'dev_password'")
        print("Created user: app_user")
    else:
        print("User already exists: app_user")

    for db_name in ["activia_trace", "activia_trace_test"]:
        await conn.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO app_user')
        print(f"Granted privileges on {db_name} to app_user")

    await conn.close()
    print("Done!")


asyncio.run(main())
