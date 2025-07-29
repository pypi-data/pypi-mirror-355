from psycopg_pool import AsyncConnectionPool
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class AsyncMultiDbConnectionPool:
        
    def __init__(self, ssm, credentials_path, min_connections, max_connections):
        self._ssm = ssm
        self._credentials_path = credentials_path
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._pools = {}
        logger.info(f"Initialized AsyncMultiDbConnectionPool with max connections per db: {max_connections}")

    def _get_db_credentials_from_env(self, db_id):
        """
        Get database credentials from environment variables as fallback.
        This allows local development without AWS SSM.
        """
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError(f"No DATABASE_URL environment variable found for local development")
        
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        
        db_creds = {
            'db_host': parsed.hostname,
            'db_name': parsed.path.lstrip('/'),
            'db_user': parsed.username,
            'db_password': parsed.password,
            'db_port': str(parsed.port or 5432)
        }
        
        logger.info(f"Using local database credentials for {db_id}")
        return db_creds

    def _get_db_credentials(self, db_id):
        # If SSM client is None, go directly to environment variables
        if self._ssm is None:
            logger.info(f"No SSM client available, using environment variables for {db_id}")
            return self._get_db_credentials_from_env(db_id)
        
        try:
            # Try AWS SSM first
            response = self._ssm.get_parameters_by_path(Path=f'{self._credentials_path}/{db_id}')
            db_creds = {}
            for i in response['Parameters']:
                key = i['Name'].split('/')[-1]
                db_creds[key] = i['Value']
            if not all(key in db_creds for key in
                       ['db_host', 'db_name', 'db_user', 'db_password', 'db_port']):
                raise ValueError(f"Missing required database credentials for {db_id}. Found: {db_creds.keys()}")
            logger.info(f"Using AWS SSM credentials for {db_id}")
            return db_creds
        except Exception as e:
            logger.warning(f"Failed to get credentials from AWS SSM for {db_id}: {e}")
            logger.info("Falling back to local environment variables")
            return self._get_db_credentials_from_env(db_id)

    async def get_connection_pool(self, db_id, read_only=True):
        """
        Get a database connection from the pool.
        If the pool does not exist, create it.
        """
        if db_id is None:
            raise ValueError("db_id cannot be None")
        key = db_id if not read_only else f"{db_id}_reader"
        if key not in self._pools:
            logger.info(f"Creating new connection pool for {key}")
            creds = self._get_db_credentials(key)
            # Slighly odd, mandatory way of passing connection parameters to psycopg_pool...!
            conninfo = f"dbname={creds['db_name']} "
            conninfo += f"user={creds['db_user']} "
            conninfo += f"password={creds['db_password']} "
            conninfo += f"host={creds['db_host']} "
            conninfo += f"port={creds['db_port']}"
            pool = AsyncConnectionPool(
                conninfo=conninfo,
                open=False,
                min_size=self._min_connections,
                max_size=self._max_connections
            )
            await pool.open()
            self._pools[key] = pool
        return self._pools[key]

    async def close_pools(self):
        for key, pool in self._pools.items():
            try:
                await pool.close()
                logger.info(f"Closed connection pool for {key}")
            except Exception as e:
                logger.error(f"Failed to close connection pool ({key}:{pool}): {e}")
        self._pools.clear()
        logger.info("All connection pools closed")
