import logging
import requests
import jwt
from typing import Dict
from .cache import TTLCache

logger = logging.getLogger(__name__)

def validate_token(token: str, public_key: str, env: str, algorithm="RS256") -> Dict:
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            issuer=f"velaris-{env}-token-generation-service",
            options={
                "verify_aud": False, # seems to be required for some tokens
                "verify_exp": False, # FOR TESTING ONLY, should be True in production!!
            }
        )
        logger.info("Successfully decoded token")
        for key in ["user", "tenant"]:
            if key not in decoded:
                logger.error(f"Token does not contain '{key}' field")
                raise ValueError(f"Invalid token structure: missing '{key}' field")
        return decoded
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise ValueError("Invalid token") from e


TOKEN_SERVICE_PARAMETER = "TOKEN_GENERATION_SERVICE_URL"

class TokenService:
    def __init__(self, service_registry, ttl):
        self._service_registry = service_registry
        self._base_url = self._service_registry.get_service_url(TOKEN_SERVICE_PARAMETER)
        self._base_url = self._base_url.rstrip("/")
        self._user_management_service = UserManagmentService(
            self._service_registry.get_service_url("USER_MANAGEMENT_SERVICE_URL")
        ) # this service is used to get user information by username when only a username is provided
        self._cache = TTLCache(ttl)
    
    def _post(self, path: str, payload: dict) -> str:
        logger.info(f"TokenService: POST to {self._base_url}{path}")
        url = f"{self._base_url}{path}"
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Token service failed: {response.status_code} - {response.text}")
        return response.json()["data"]["token"]
    
    def get_application_token(self, audience: list[str]) -> str:
        key = ('get_application_token', tuple(sorted(audience)))
        if self._cache.get(key) is not None:
            return self._cache.get(key)
        else:
            result = self._post("/internal/applicationToken", {"audience": audience})
            self._cache.set(key, result)
            return result
    
    def get_user_token(self, initiator: str, user_id: int, role: str, tenant: dict) -> str:
        key = ('get_user_token', initiator, user_id, role, tenant['tenantIdentifier'])
        if self._cache.get(key) is not None:
            return self._cache.get(key)
        else:
            payload = {
                "initiator": initiator,
                "user": {"id": user_id, "role": role},
                "tenant": tenant
            }
            result = self._post("/internal/token", payload)
            self._cache.set(key, result)
            return result
    
    def get_user_token_by_username(self, initiator: str, username: str, tenant: dict) -> str:
        key = ('get_user_token_by_username', initiator, username, tenant['tenantIdentifier'])
        if self._cache.get(key) is not None:
            return self._cache.get(key)
        else:
            default_user_token = self.get_user_token(
                initiator='INTERNAL_BFF',
                user_id=1, role='Administrator',
                tenant=tenant
            )
            user = self._user_management_service.get_user_by_username(username, default_user_token)
            logger.info(f"User found: {user}")
            result = self.get_user_token(
                initiator=initiator,
                user_id=user["userId"], role='Administrator',
                tenant=tenant
            )
            self._cache.set(key, result)
            return result
    
class AuthenticatedService(): # No caching: Caching must be done in the caller
    '''Base class for services that require authentication with a token'''
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, token: str) -> dict:
        logger.info(f"AuthenticatedService: GET {self.base_url}{path}")
        response = requests.get(
            f"{self.base_url}{path}",
            headers={"Authorization": token, "Content-Type": "application/json"}
        )
        if response.status_code != 200:
            raise RuntimeError(f"Service call failed: {response.status_code} - {response.text}")
        return response.json()
        
class UserManagmentService(AuthenticatedService): # No caching: Caching must be done in the caller
    # requires a user token
    def get_user_by_username(self, username: str, token: str) -> dict:
        users = self._get(f"/users?username={username}", token)['data']['users']
        logger.debug(f"User list: {users}")
        if len(users) > 1:
            raise RuntimeError(f"Multiple users found for username {username}")
        return users[0]
    
# Only needed if we need to get tenant information by identifier
# We'd need to expose a new method in the TokenService that uses it, eg get_user_token_by_username_and_tenant_identifier!
#
# class TenantInformationService(AuthenticatedService): # No caching: Caching must be done in the caller
#     # requires only an application token, not a user token
#     def get_tenant_by_identifier(self,tenant_identifier: str, app_token: str) -> dict:
#         tenants=self._get("/tenants", app_token)
#         logger.debug(f"Tenant list: {tenants}")
#         for i in tenants['data']:
#             if i["tenantIdentifier"]==tenant_identifier:
#                 return i
#         else:
#             raise RuntimeError(f"Tenant {tenant_identifier} not found in TIS")
