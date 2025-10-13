from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import re

class ValidateToken(Tool):    
    def execute(self, context: Context) -> TextResponse:
        email = context.parameters.get("email", "")
        auth_token = context.parameters.get("auth_token", "")
        user_token = context.parameters.get("user_token", "")

        base_url = context.credentials.get("BASE_URL", "")
        vtex_appkey = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_apptoken = context.credentials.get("VTEX_API_APPTOKEN", "")

        # Extract account_name from base_url
        account_name = self.extract_account_name(base_url)

        print("email", email)

        # Validate the token provided by the user
        result, status_code = self.validate_user_token(base_url, account_name, auth_token, user_token, email)

        if status_code != 200:
            return TextResponse(data={"message": "Invalid or expired token"})

        if result.get("authCookie"):
            auth = {"message": "User authenticated successfully", "authentication_token": result}

            organizations = self.get_organizations(base_url, vtex_appkey, vtex_apptoken, email)
            print("organizations", organizations)
            return TextResponse({"auth": auth, "organizations": organizations})
        else:
            print("Error to generate authentication token ", result)
            return TextResponse(data={"message": "Invalid or expired token"})
                
    
    def extract_account_name(self, base_url: str) -> str:
        """
        Extract the account_name from the base_url
        Example: https://weni.myvtex.com -> weni
        """
        # Remove protocol (http:// or https://)
        url_without_protocol = re.sub(r'^https?://', '', base_url)
        
        # Get the first part before the first dot
        account_name = url_without_protocol.split('.')[0]
        
        return account_name

    def validate_user_token(self, base_url: str, account_name: str, auth_token: str, user_token: str, email: str) -> dict:
        """
        Validate the token provided by the user
        """
        print("=" * 80)
        print("DEBUG: validate_user_token - INÍCIO")
        print("=" * 80)
        
        url = f"{base_url}/api/vtexid/pub/authentication/accesskey/validate"
        print(f"DEBUG: URL: {url}")
        print(f"DEBUG: Account Name: {account_name}")
        print(f"DEBUG: Email: {email}")
        print(f"DEBUG: Auth Token: {auth_token if auth_token else 'None'}")
        print(f"DEBUG: User Token: {user_token if user_token else 'None'}")
        
        # Using application/x-www-form-urlencoded format
        data = {
            'authenticationToken': auth_token,
            'login': email,
            'accessKey': user_token
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"DEBUG: Headers: {headers}")
        print("DEBUG: Enviando requisição POST...")
        
        response = requests.post(url, headers=headers, data=data)

        status_code = response.status_code
        print(f"DEBUG: Status Code: {status_code}")
        
        try:
            response_json = response.json()
            print(f"DEBUG: Response JSON: {response_json}")
        except Exception as e:
            print(f"DEBUG: Erro ao fazer parse do JSON: {str(e)}")
            print(f"DEBUG: Response Text: {response.text}")
            response_json = {}
        
        print("=" * 80)
        print("DEBUG: validate_user_token - FIM")
        print("=" * 80)
        
        return response_json, status_code
    

    def get_organizations(self, base_url: str, vtex_app_key: str, vtex_app_token: str, email: str) -> TextResponse:
        url = f"{base_url}/_v/private/graphql/v1"

        query = """
        query getOrganizationsByEmail($email: String!) {
            getOrganizationsByEmail(email: $email)
            @context(provider: "vtex.b2b-organizations-graphql@0.x") {
                id
                clId
                costId
                orgId
                roleId
                role {
                    id
                    name
                    slug
                }
                organizationName
                organizationStatus
                costCenterName
            }
        }
        """
        
        payload = {
            "query": query,
            "variables": {
                "email": email
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Vtex-api-appkey': vtex_app_key,
            'Vtex-api-apptoken': vtex_app_token
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            api_response = response.json()
            print("get_organizations", api_response)
            organizations_data = api_response.get('data', {}).get('getOrganizationsByEmail', [])
            
            # Para cada organização, buscar as priceTables
            for org in organizations_data:
                if 'id' in org:
                    org['userId'] = org.pop('id')
                
                # Buscar priceTables para esta organização
                org_id = org.get('orgId')
                if org_id:
                    price_tables = self.get_organization_price_tables(base_url, vtex_app_key, vtex_app_token, org_id)
                    org['priceTables'] = price_tables
                else:
                    org['priceTables'] = []
            
            return TextResponse(data={"orgs": organizations_data})
            
        except requests.exceptions.RequestException as e:
            return TextResponse(data={
                "message": f"Error retrieving organizations: {str(e)}", 
                "orgs": []
            })
    
    def get_organization_price_tables(self, base_url: str, vtex_app_key: str, vtex_app_token: str, organization_id: str) -> list:
        """Busca as priceTables para uma organização específica"""
        url = f"{base_url}/api/io/_v/public/graphql/v1"

        query = """
        query GetOrganizationById($id: ID) {
            getOrganizationById(id: $id) @context(provider: "vtex.b2b-organizations-graphql") {
                priceTables
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
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            api_response = response.json()
            organization_data = api_response.get('data', {}).get('getOrganizationById', {})
            
            return organization_data.get('priceTables', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting price tables for organization {organization_id}: {str(e)}")
            return []
