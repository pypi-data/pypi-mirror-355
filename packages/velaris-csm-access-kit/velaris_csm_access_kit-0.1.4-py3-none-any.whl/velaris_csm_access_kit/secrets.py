import json
import logging

logger = logging.getLogger(__name__)

_secrets = {}  # module level variable to store secrets

def get_secret(session, region, secret_id, key=None):
    """
    Retrieve secrets stored under a secret_id in AWS Secrets Manager.
    If key is provided, assume the secret is in JSON format and return the value associated with that key
    Otherwise, return the entire secret as a string (eg as in the case of the public for JWT verification)
    """
    global _secrets
    if secret_id not in _secrets:
        logger.info(f"Retrieving secret {secret_id} from AWS Secrets Manager")
        client = session.client(service_name="secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_id)
        _secrets[secret_id] = response.get("SecretString")
    if key is None:
        return _secrets.get(secret_id)
    else:
        return json.loads(_secrets.get(secret_id)).get(key)
