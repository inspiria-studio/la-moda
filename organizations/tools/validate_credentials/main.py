from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import re
import json

class ValidateCredentials(Tool):    
    def execute(self, context: Context) -> TextResponse:
        # Tentar obter email e password dos parâmetros (pode vir do flow ou diretamente)
        email = context.parameters.get("email", "")
        password = context.parameters.get("password", "")
        auth_token = context.parameters.get("auth_token", "")

        """ # Se não tiver email ou password, tentar extrair do payload do flow
        if not email or not password:
            flow_data = self.extract_flow_credentials(context)
            if flow_data:
                email = flow_data.get("email", email)
                password = flow_data.get("password", password)

        # Se ainda não tiver email ou password, disparar o flow
        if not email or not password:
            return self.send_whatsapp_flow(context) """

        # Se não tiver auth_token, retornar erro
        if not auth_token:
            return TextResponse(data={
                "message": "Auth token é necessário. Use a tool send_token primeiro.",
                "flow_sent": False
            })

        base_url = context.credentials.get("BASE_URL", "https://lamodab2b.myvtex.com")
        vtex_appkey = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_apptoken = context.credentials.get("VTEX_API_APPTOKEN", "")

        # Extract account_name from base_url
        account_name = self.extract_account_name(base_url)

        print("email", email)

        # Validate the token provided by the user
        result, status_code = self.validate_user_token(base_url, account_name, auth_token, email, password)

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
    
    def extract_flow_credentials(self, context: Context) -> dict:
        """
        Extrai email e senha do payload do flow response.
        O formato esperado é baseado no JSON do flow fornecido:
        - screen_0_Email_0: email (do payload final do flow)
        - screen_1_senha_0: senha (do payload final do flow)
        
        """
        credentials = {}
        
        # Tentar obter do payload direto (pode vir como string JSON ou dict)
        flow_payload = context.parameters.get("flow_payload", {})
        if isinstance(flow_payload, str):
            try:
                flow_payload = json.loads(flow_payload)
            except:
                flow_payload = {}
        
        # Extrair email - tentar múltiplas variações
        email = ""
        # Primeiro tentar do flow_payload
        email = flow_payload.get("screen_0_Email_0", "")

        password = ""
        # Primeiro tentar do flow_payload
        password = flow_payload.get("screen_1_senha_0", "")

        
        if email and password:
            credentials["email"] = email
            credentials["password"] = password
            print(f"extract_flow_credentials: credenciais extraídas do flow - email={email[:5]}...")
        
        return credentials

    def send_whatsapp_flow(self, context: Context) -> TextResponse:
        """
        Dispara um WhatsApp Flow via Facebook Graph API para coletar credenciais do usuário.

        Requisitos (context.credentials):
          - META_NUMBER_ID: ID do número do WhatsApp Business
          - META_TOKEN: Token Bearer do Graph API
          - FLOW_ID: ID do flow publicado no WhatsApp
        """
        try:
            urn = context.contact.get("urn")
            urn = "whatsapp:5585999854658"
            if not urn:
                return TextResponse(data={
                    "success": False,
                    "message": "URN do contato não encontrado. Não é possível enviar o flow.",
                    "flow_sent": False
                })

            numberidMeta = context.credentials.get("META_NUMBER_ID", "512711513158012")
            meta_token = context.credentials.get("META_TOKEN", "")
            flow_id = context.credentials.get("FLOW_ID", "1381454720032966")
            flow_id = "1381454720032966"

            if not numberidMeta or not meta_token:
                return TextResponse(data={
                    "success": False,
                    "message": "Credenciais do Facebook Graph API não configuradas (META_NUMBER_ID, META_TOKEN).",
                    "flow_sent": False
                })

            if not flow_id:
                return TextResponse(data={
                    "success": False,
                    "message": "FLOW_ID não configurado nas credenciais.",
                    "flow_sent": False
                })

            # Garantir que a URN está no formato correto (whatsapp:numero)
            if not urn.startswith("whatsapp:"):
                urn = f"whatsapp:{urn}"

            graph_url = f"https://graph.facebook.com/v19.0/{numberidMeta}/messages"
            headers = {
                "Authorization": f"Bearer {meta_token}",
                "Content-Type": "application/json"
            }

            body = {
                "messaging_product": "whatsapp",
                "to": urn,
                "type": "interactive",
                "interactive": {
                    "type": "flow",
                    "header": {
                        "type": "text",
                        "text": "Autenticação"
                    },
                    "body": {
                        "text": "Por favor, faça a autenticação para continuar."
                    },
                    "footer": {
                        "text": "Importante: tempo de espera para resposta é de ⏱️ 15 minutos."
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "mode": "published",
                            "flow_message_version": "3",
                            "flow_id": flow_id,
                            "flow_cta": "Iniciar",
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": "screen_kxqrnr"
                            }
                        }
                    }
                }
            }

            resp = requests.post(graph_url, headers=headers, json=body, timeout=30)
            print(f"send_whatsapp_flow: resposta do Facebook Graph API - status={resp.status_code}")
            print(f"send_whatsapp_flow: resposta do Facebook Graph API - {resp.text}")

            if 200 <= resp.status_code < 300:
                return TextResponse(data={
                    "success": True,
                    "message": "Flow enviado com sucesso. Aguarde o preenchimento das credenciais.",
                    "flow_sent": True
                })
            else:
                # Tentar extrair mensagem de erro mais detalhada
                error_message = resp.text
                try:
                    error_json = resp.json()
                    if "error" in error_json:
                        error_details = error_json["error"]
                        error_message = error_details.get("message", error_message)
                        if "error_data" in error_details:
                            error_data = error_details["error_data"]
                            if "details" in error_data:
                                error_message = f"{error_message} - {error_data['details']}"
                except:
                    pass
                
                return TextResponse(data={
                    "success": False,
                    "message": f"Erro ao enviar flow: {error_message}",
                    "flow_sent": False,
                    "status_code": resp.status_code
                })

        except Exception as e:
            print(f"send_whatsapp_flow: erro ao enviar o fluxo - {e}")
            return TextResponse(data={
                "success": False,
                "message": f"Erro ao enviar flow: {str(e)}",
                "flow_sent": False
            })
    
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

    def validate_user_token(self, base_url: str, account_name: str, auth_token: str, email: str, password: str) -> dict:
        """
        Validate the token provided by the user
        """
        print("=" * 80)
        print("DEBUG: validate_user_token - INÍCIO")
        print("=" * 80)
        
        url = f"{base_url}/api/vtexid/pub/authentication/classic/validate"
        print(f"DEBUG: URL: {url}")
        print(f"DEBUG: Account Name: {account_name}")
        print(f"DEBUG: Email: {email}")
        print(f"DEBUG: Auth Token: {auth_token if auth_token else 'None'}")
        print(f"DEBUG: Password: {password if password else 'None'}")
        
        # Using application/x-www-form-urlencoded format
        data = {
            'email': email,
            'password': password,
            'authenticationToken': auth_token
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
