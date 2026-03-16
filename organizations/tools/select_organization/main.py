from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
from urllib.parse import quote


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
            #organization_data.get("orgId") = "15730808-3657-4800-82d6-f68cecdc1c87"
            
            """ if not organization_data.get("orgId"):
                return TextResponse(data={
                    "message": "Organization not found",
                    "success": False
                }) """
            
            # Step 2: Create session with the organization data
            session_result = self.create_session_token(
                base_url, cost_center_id, auth_cookie_name, auth_cookie_value, 
                account_auth_cookie_name, account_auth_cookie_value, 
                organization_id, price_table_id, user_id
            )
            print("session_result", session_result)
            
            # Step 3: Save tokens to Weni contact
            session_token = session_result.get("sessionToken")
            segment_token = session_result.get("segmentToken")
            
            print(f"DEBUG: session_token existe: {bool(session_token)}")
            print(f"DEBUG: segment_token existe: {bool(segment_token)}")
            
            if session_token and segment_token:
                try:
                    weni_token = "f5a884633f31eef1ffb0480731f054267d0fb614"
                    urn = context.contact.get("urn")
                    print(f"DEBUG: weni_token existe: {bool(weni_token)}")
                    print(f"DEBUG: urn obtido: {urn}")
                    
                    if weni_token and urn:
                        print("DEBUG: Chamando _save_tokens_to_weni...")
                        result = self._save_tokens_to_weni(context, session_token, segment_token, weni_token)
                        print(f"DEBUG: Resultado do save: {result}")
                    else:
                        print(f"DEBUG: Condição não atendida - weni_token: {bool(weni_token)}, urn: {bool(urn)}")
                except Exception as e:
                    # Não falha a operação se não conseguir salvar os tokens
                    print(f"Aviso: Não foi possível salvar tokens na Weni: {str(e)}")
                    import traceback
                    print(f"DEBUG: Traceback completo: {traceback.format_exc()}")
            else:
                print("DEBUG: Tokens não disponíveis - não tentando salvar na Weni")
            
            # Combine results
            combined_result = {
                "message": "Organization selected and session created successfully",
                "success": True,
                "organization": organization_data,
                "userId": user_id,
                "costId": cost_center_id,
                "orgId": organization_id,
                "sessionToken": session_token,
                "segmentToken": segment_token
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
    
    def _save_tokens_to_weni(self, context: Context, session_token: str, segment_token: str, api_token: str) -> bool:
        """
        Salva sessionToken e segmentToken no contato da Weni.
        
        Args:
            urn (str): URN do contato (ex: "whatsapp:555133334444")
            session_token (str): Token de sessão VTEX
            segment_token (str): Token de segmento VTEX
            api_token (str): Token de autenticação da API Weni
        
        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            print("=" * 80)
            print("DEBUG: _save_tokens_to_weni - INÍCIO")
            print(f"DEBUG: URN: {context.contact.get('urn')}")
            print(f"DEBUG: session_token length: {len(session_token) if session_token else 0}")
            print(f"DEBUG: segment_token length: {len(segment_token) if segment_token else 0}")
            urn = context.contact.get("urn")
            print(f"DEBUG: URN: {urn}")
            base_url = "https://flows.weni.ai/api/v2/contacts.json"
            encoded_urn = quote(urn, safe="")
            url = f"{base_url}?urn={encoded_urn}"
            print(f"DEBUG: URL: {url}")
            
            headers = {
                "Authorization": f"token {api_token}",
                "Content-Type": "application/json",
            }
            
            # Campos a serem salvos
            # Nota: Tokens podem exceder 255 caracteres, mas tentamos salvar mesmo assim
            # A API da Weni pode aceitar valores maiores em alguns casos
            fields = {
                "vtex_session_token": session_token,
                "vtex_segment_token": segment_token
            }
            
            payload = {"fields": fields}
            print(f"DEBUG: Enviando requisição POST para Weni...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"DEBUG: Status Code: {response.status_code}")
            
            response.raise_for_status()
            response_data = response.json()
            print(f"DEBUG: Resposta da Weni: {response_data}")
            print("DEBUG: _save_tokens_to_weni - SUCESSO")
            print("=" * 80)
            return 200 <= response.status_code < 300
        except Exception as e:
            print("=" * 80)
            print(f"DEBUG: _save_tokens_to_weni - ERRO")
            print(f"Erro ao salvar tokens na Weni: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback completo: {traceback.format_exc()}")
            print("=" * 80)
            return False
