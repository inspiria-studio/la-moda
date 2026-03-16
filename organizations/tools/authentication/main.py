from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import re

class Authentication(Tool):    
    def execute(self, context: Context) -> TextResponse:
        email = context.parameters.get("email", "")

        base_url = context.credentials.get("BASE_URL", "")
        locale = context.credentials.get("LOCALE", "pt-BR")

       
        try:
            # Extract account_name from base_url
            account_name = self.extract_account_name(base_url)
            
            # First step: get authentication token
            auth_token = self.get_authentication_token(base_url, account_name, locale)
            
            """ # Second step: send access key using the token
            result = self.send_access_key(base_url, auth_token, email) """
            
            return TextResponse(data={"email": email, "auth_token": auth_token})
            
        except Exception as e:
            # Print error to console for debugging
            print(f"Authentication error: {str(e)}")
            
            # Return invalid email message
            return TextResponse(data={"message": "Invalid email"})
    
    def extract_account_name(self, base_url: str) -> str:
        """
        Extract the account_name from the base_url
        Example: https://weni.myvtex.com -> weni
        """
        print("=" * 80)
        print("DEBUG: extract_account_name - INÍCIO")
        print("=" * 80)
        print(f"DEBUG: Base URL: {base_url}")
        
        # Remove protocol (http:// or https://)
        url_without_protocol = re.sub(r'^https?://', '', base_url)
        print(f"DEBUG: URL sem protocolo: {url_without_protocol}")
        
        # Get the first part before the first dot
        account_name = url_without_protocol.split('.')[0]
        print(f"DEBUG: Account Name extraído: {account_name}")
        
        print("=" * 80)
        print("DEBUG: extract_account_name - FIM")
        print("=" * 80)
        
        return account_name

    def get_authentication_token(self, base_url: str, account_name: str, locale: str) -> str:
        """
        First step: get the authentication token
        """
        print("=" * 80)
        print("DEBUG: get_authentication_token - INÍCIO")
        print("=" * 80)
        print(f"DEBUG: Base URL: {base_url}")
        print(f"DEBUG: Account Name: {account_name}")
        print(f"DEBUG: Locale: {locale}")
        
        url = f"{base_url}/api/vtexid/pub/authentication/start?scope={account_name}&locale={locale}"
        print(f"DEBUG: URL completa: {url}")
        
        print("DEBUG: Enviando requisição GET...")
        response = requests.get(url)
        
        status_code = response.status_code
        print(f"DEBUG: Status Code: {status_code}")
        
        try:
            response.raise_for_status()
            auth_data = response.json()
            print(f"DEBUG: Response JSON: {auth_data}")
        except Exception as e:
            print(f"DEBUG: Erro na requisição: {str(e)}")
            print(f"DEBUG: Response Text: {response.text}")
            raise
        
        # Extract the authenticationToken from response
        authentication_token = auth_data.get("authenticationToken")
        print(f"DEBUG: Authentication Token extraído: {authentication_token if authentication_token else 'None'}")
        
        if not authentication_token:
            print("DEBUG: ERRO - Authentication token não encontrado na resposta!")
            raise Exception("Authentication token not found in response")
            
        print("=" * 80)
        print("DEBUG: get_authentication_token - FIM")
        print("=" * 80)
            
        return authentication_token

    def send_access_key(self, base_url: str, auth_token: str, email: str) -> dict:
        """
        Second step: send access key using the authentication token
        """
        print("=" * 80)
        print("DEBUG: send_access_key - INÍCIO")
        print("=" * 80)
        print(f"DEBUG: Base URL: {base_url}")
        print(f"DEBUG: Auth Token: {auth_token if auth_token else 'None'}")
        print(f"DEBUG: Email: {email}")
        
        url = f"{base_url}/api/vtexid/pub/authentication/accesskey/send"
        print(f"DEBUG: URL: {url}")
        
        # Using multipart/form-data format as shown in the cURL example
        files = {
            'authenticationToken': (None, auth_token),
            'email': (None, email)
        }
        
        headers = {
            'Accept': 'application/json'
        }
        
        print(f"DEBUG: Files: {files}")
        print(f"DEBUG: Headers: {headers}")
        print("DEBUG: Enviando requisição POST...")
        
        response = requests.post(url, headers=headers, files=files)
        
        status_code = response.status_code
        print(f"DEBUG: Status Code: {status_code}")
        
        try:
            response.raise_for_status()
            response_json = response.json()
            print(f"DEBUG: Response JSON: {response_json}")
        except Exception as e:
            print(f"DEBUG: Erro na requisição: {str(e)}")
            print(f"DEBUG: Response Text: {response.text}")
            raise
        
        print("=" * 80)
        print("DEBUG: send_access_key - FIM")
        print("=" * 80)
        
        return response_json