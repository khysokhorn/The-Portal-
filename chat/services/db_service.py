import os
import json
from dotenv import load_dotenv

try:
    import asyncpg
except ImportError:
    asyncpg = None

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class DBService:
    db_pool = None

    @classmethod
    async def init_db(cls):
        """Initializes the database connection pool and ensures tables exist."""
        if asyncpg and DATABASE_URL:
            try:
                print("Connecting to Neon Postgres...")
                cls.db_pool = await asyncpg.create_pool(DATABASE_URL)
                async with cls.db_pool.acquire() as conn:
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS chat_logs (
                            id SERIAL PRIMARY KEY,
                            model VARCHAR(255),
                            request_payload JSONB,
                            response_payload JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                print("Neon Postgres connected and table verified.")
            except Exception as e:
                print(f"Failed to connect to Postgres: {e}")

    @classmethod
    async def close_db(cls):
        """Closes the database connection pool."""
        if cls.db_pool:
            await cls.db_pool.close()

    @classmethod
    async def log_chat(cls, model: str, request_data: dict, response_data: dict = None):
        """Logs a chat interaction to the database."""
        if cls.db_pool:
            try:
                async with cls.db_pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO chat_logs (model, request_payload, response_payload) VALUES ($1, $2, $3)",
                        model, 
                        json.dumps(request_data), 
                        json.dumps(response_data) if response_data else None
                    )
            except Exception as e:
                print(f"Failed to log chat: {e}")

async def log_chat_to_db(model: str, request_data: dict, response_data: dict = None):
    """Helper function to log chat, easily used in BackgroundTasks."""
    await DBService.log_chat(model, request_data, response_data)
