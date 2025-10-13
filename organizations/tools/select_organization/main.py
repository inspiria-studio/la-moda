from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json


class SelectOrganization(Tool):    
    def execute(self, context: Context) -> TextResponse:
        # Parameters for organization selection
        organization_id = context.parameters.get("organization_id", "")
        
        # Parameters for session creation (from previous authentication)
        cost_center_id = context.parameters.get("cost_center_id", "")
        auth_cookie_name = context.parameters.get("auth_cookie_name", "")
        auth_cookie_value = context.parameters.get("auth_cookie_value", "")
        account_auth_cookie_name = context.parameters.get("account_auth_cookie_name", "")
        account_auth_cookie_value = context.parameters.get("account_auth_cookie_value", "")
        price_table_id = context.parameters.get("price_table_id", "")
        user_id = context.parameters.get("user_id", "")

        base_url = context.credentials.get("BASE_URL", "")
        vtex_app_key = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_app_token = context.credentials.get("VTEX_API_APPTOKEN", "")

        try:
            # Step 1: Get organization details
            organization_data = self.get_organization_by_id(base_url, vtex_app_key, vtex_app_token, organization_id)
            
            if not organization_data.get("orgId"):
                return TextResponse(data={
                    "message": "Organization not found",
                    "success": False
                })
            
            # Step 2: Create session with the organization data
            session_result = self.create_session_token(
                base_url, cost_center_id, auth_cookie_name, auth_cookie_value, 
                account_auth_cookie_name, account_auth_cookie_value, 
                organization_id, price_table_id, user_id
            )
            
            # Combine results
            combined_result = {
                "message": "Organization selected and session created successfully",
                "success": True,
                "organization": organization_data,
                "userId": user_id,
                "costId": cost_center_id,
                "orgId": organization_id,
                "sessionToken": session_result.get("sessionToken"),
                "segmentToken": session_result.get("segmentToken")
            }
            
            return TextResponse(data=combined_result)
            
        except Exception as e:
            return TextResponse(data={
                "message": f"Error selecting organization and creating session: {str(e)}", 
                "success": False
            })

    def get_organization_by_id(self, base_url: str, vtex_app_key: str, vtex_app_token: str, organization_id: str) -> dict:
        """Get organization details by ID"""
        
        url = f"{base_url}/api/io/_v/public/graphql/v1"

        query = """
        query GetOrganizationById($id: ID) {
            getOrganizationById(id: $id) @context(provider: "vtex.b2b-organizations-graphql") {
                id
                name
                status
                collections {
                    id
                    name
                }
                priceTables
                salesChannel
                costCenters
            }
        }
        """
        
        payload = {
            "query": query,
            "variables": {
                "id": organization_id
            }
        }
        
        headers = {
            'VTEX-API-AppKey': vtex_app_key,
            'VTEX-API-AppToken': vtex_app_token,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        api_response = response.json()
        print("get_organization_by_id", api_response)
        organization_data = api_response.get('data', {}).get('getOrganizationById', {})
        
        if organization_data:
            collections = organization_data.get('collections', [])
            collection_id = collections[0].get('id') if collections else None
            
            return {
                "salesChannel": organization_data.get('salesChannel', ''),
                "priceTables": organization_data.get('priceTables', []),
                "collectionId": collection_id,
                "orgId": organization_data.get('id', ''),
                "name": organization_data.get('name', ''),
                "status": organization_data.get('status', ''),
                "costCenters": organization_data.get('costCenters', [])
            }
        else:
            return {
                "salesChannel": '',
                "priceTables": [],
                "collectionId": None,
                "orgId": '',
                "name": '',
                "status": '',
                "costCenters": []
            }

    def create_session_token(self, base_url: str, cost_center_id: str, auth_cookie_name: str, auth_cookie_value: str, account_auth_cookie_name: str, account_auth_cookie_value: str, organization_id: str, price_table_id: str, user_id: str) -> dict:
        """Create a session token with the provided authentication data"""
        url = f"{base_url}/api/sessions"
        
        # Create cookie string in format: name=value;name=value
        auth_cookie_str = f"{auth_cookie_name}={auth_cookie_value}"
        account_auth_cookie_str = f"{account_auth_cookie_name}={account_auth_cookie_value}"
        cookie_header = f"{auth_cookie_str};{account_auth_cookie_str}"
        
        json_data = {
            "public": {
                "authCookie": {
                    "value": auth_cookie_value
                },
                "storefront-permissions": {
                    "organization": {
                        "value": organization_id
                    },
                    "costcenter": {
                        "value": cost_center_id
                    },
                    "priceTables": {
                        "value": price_table_id
                    },
                    "userId": {
                        "value": user_id
                    }
                }
            }
        }
        
        headers = {
            'Accept': 'application/json',
            'Cookie': cookie_header
        }
        
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        
        return response.json()
