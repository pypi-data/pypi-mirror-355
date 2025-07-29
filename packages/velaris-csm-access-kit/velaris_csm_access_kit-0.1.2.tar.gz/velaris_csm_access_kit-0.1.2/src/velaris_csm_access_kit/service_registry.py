import json
import logging
from .cache import TTLCache

logger = logging.getLogger(__name__)

class ServiceRegistry:
    def __init__(self, aws_session, AWS_REGION, env, ttl):
        self.ssm = aws_session.client("ssm", AWS_REGION)
        self.parameter_name = f"/csm/{env}/external/service-registry"
        self._cache = TTLCache(ttl)

    def _get_service_registry_data(self) -> dict:
        key = ('service_registry', )
        if self._cache.get(key) is None:        
            try:
                response = self.ssm.get_parameter(
                    Name=self.parameter_name,
                    WithDecryption=True
                )
                val = response["Parameter"]["Value"]
                logger.info(f"Loading SSM data for parameter {self.parameter_name}")
                self._cache.set(key, json.loads(val))
            except Exception as e:
                logger.error(f"Failed to fetch service registry from SSM: {e}")
                raise RuntimeError("Could not load service registry")
            
        return self._cache.get(key)
    
    def get_service_url(self, service_name) -> dict:
        registry = self._get_service_registry_data()
        return registry[service_name]
