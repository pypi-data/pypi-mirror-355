import json

import msal
import requests
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from ...utils.config import Config
from ...utils.logger import get_logger

logger = get_logger(__name__)


def get_access_token():
    """
    Obtains an access token using the client credentials flow.

    Returns:
        str: The access token.

    Raises:
        ValueError: If required environment variables are missing or token acquisition fails.
    """
    tenant_id = Config().get("MS_TENANT_ID")
    client_id = Config().get("MS_CLIENT_ID")
    client_secret = Config().get("MS_CLIENT_SECRET")
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ["User.Read", "Analytics.Read", "Chat.Read", "Calendars.Read"]
    cache = msal.SerializableTokenCache()
    # if os.path.exists(CACHE_FILE):
    #    with open(CACHE_FILE, "r") as f:
    #        cache.deserialize(f.read())
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=authority,
        token_cache=cache
    )
    """Get an access token, trying silent acquisition first."""
    try:
        # Fallback to device code flow if silent fails
        logger.info("Starting device code flow")
        flow = app.initiate_device_flow(scopes=scopes)
        print(f"Please visit {flow['verification_uri']} and enter code: {flow['user_code']}")
        result = app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            logger.info("Token acquired via device code flow")
            # _save_cache()  # Save the cache after successful authentication
            return result
        else:
            logger.error(f"Token acquisition failed: {result.get('error_description')}")
            return None

    except Exception as e:
        logger.error(f"Error acquiring token: {str(e)}", exc_info=True)
        raise SystemExit


# Define a structured input model for the make_entra_request call.
class EntraInput(BaseModel):
    method: str = Field(..., description="HTTP(S) method (e.g., GET, POST)")
    path: str = Field(..., description="Path of the Entra API endpoint (e.g., 'me')")
    query_params: dict = Field(default_factory=dict, description="Optional URL parameters")
    body: dict = Field(default_factory=dict, description="Optional JSON body for the request")


def make_entra_request(input_str: EntraInput) -> dict:
    """
    Makes a request to a Microsoft Entra endpoint using the Microsoft Graph API.
    Args:
        input_str (str): A JSON string containing the request details, e.g., {"method": "GET", "path": "me"}
    Returns:
        dict: Response data or error details if the request fails.
    """
    logger.info(f"\n\n CALLING WITH INPUT: {input_str}\n\n")
    try:
        input_data = json.loads(input_str)
        method = input_data["method"]
        path = input_data["path"]
        query_params = input_data.get("query_params", {})
        body = input_data.get("body", {})
        # Add other optional fields as needed (e.g., query_params, body)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON input. Expected a string like {\"method\": \"GET\", \"path\": \"me\"}"}
    except KeyError as e:
        return {"error": f"Missing required field: {e}"}

    # Define supported HTTP methods
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    if method.upper() not in allowed_methods:
        return {"error": "Unsupported HTTP method"}

    # Obtain access token
    try:
        access_token = get_access_token()
    except ValueError as e:
        return {"error": str(e)}

    # Construct the URL
    url = f"https://graph.microsoft.com/v1.0/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the request
    response = None
    try:
        response = requests.request(method.upper(), url, headers=headers, params=query_params, json=body)
        response.raise_for_status()

        if response.status_code == 204:
            return {"message": "Operation successful, no content returned"}
        else:
            return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": str(e), "status_code": response.status_code, "response": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# Wrap the function as a LangChain Tool.
entra_tool = Tool(
    name="entra_tool",
    func=make_entra_request,
    description=make_entra_request.__doc__
)


if __name__ == "__main__":
    # Example usage
    input_str = '{"method": "GET", "path": "me"}'
    response = make_entra_request(input_str)
    print(f"Response: {response}")
    print("Done.")
