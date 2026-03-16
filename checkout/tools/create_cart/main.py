from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
import os
import re
import ast
from dotenv import load_dotenv
from urllib.parse import quote


class CreateCart(Tool):
    def _parse_product_items(self, product_items_str):
        """Parse product items from string format to proper dictionary format"""
        try:
            # If it's already a list of dicts, return as is
            if isinstance(product_items_str, list):
                print(f"Product items already parsed: {product_items_str}")
                return product_items_str
            
            # If it's not a string, convert to string
            if not isinstance(product_items_str, str):
                product_items_str = str(product_items_str)
            
            print(f"Parsing product items string: {product_items_str}")
            
            # Clean up the string: remove leading colons, whitespace, etc.
            cleaned_str = product_items_str.strip()
            # Remove leading colon if present (common issue)
            if cleaned_str.startswith(':'):
                cleaned_str = cleaned_str[1:].strip()
            
            # Try to parse as JSON first (most reliable)
            try:
                parsed = json.loads(cleaned_str)
                if isinstance(parsed, list):
                    print(f"Successfully parsed as JSON: {parsed}")
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON parsing failed: {str(e)}, trying ast.literal_eval or manual parsing")
            # Formato literal Python (aspas simples) ex: [{'product_retailer_id': '260650', 'quantity': 2}]
            try:
                parsed = ast.literal_eval(cleaned_str)
                if isinstance(parsed, list):
                    print(f"Successfully parsed as Python literal: {parsed}")
                    return parsed
            except (ValueError, SyntaxError):
                pass
            
            # Remove brackets and split items
            items_str = cleaned_str.strip('[]').strip()
            if not items_str:
                return []
            
            # Try to extract JSON-like content if it's embedded in a string
            # Look for JSON array pattern
            json_match = re.search(r'\[.*\]', items_str)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, list):
                        print(f"Successfully parsed JSON from embedded string: {parsed}")
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Split into individual items and parse each one
            items = []
            for item_str in items_str.split('}, {'):
                # Clean up the item string
                item_str = item_str.strip('{}').strip()
                print(f"Processing item string: {item_str}")
                
                # Try to parse as JSON object first
                try:
                    item_dict = json.loads('{' + item_str + '}')
                    if item_dict:
                        items.append(item_dict)
                        print(f"Added item (JSON): {item_dict}")
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
                
                # Fallback to manual parsing for non-JSON format
                item_dict = {}
                for pair in item_str.split(','):
                    pair = pair.strip()
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip().strip("'\"")
                        value = value.strip().strip("'\"")
                        
                        # Convert numeric values, but keep product_retailer_id as string
                        if key == 'product_retailer_id':
                            # Keep product_retailer_id as string for later processing
                            value = str(value)
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '').replace('-', '').isdigit():
                            value = float(value)
                        
                        item_dict[key] = value
                
                if item_dict:
                    items.append(item_dict)
                    print(f"Added item (manual): {item_dict}")
            
            print(f"Final parsed items: {items}")
            return items
                
        except Exception as e:
            print(f"Error parsing product items: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []

    def execute(self, context: Context) -> TextResponse:
        product_items = context.parameters.get("product_items", [])
        #vtex_session = context.parameters.get("vtex_session", "")
        #vtex_segment = context.parameters.get("vtex_segment", "")
        vtex_session = ""
        vtex_segment = ""

        # Se os tokens não vierem como parâmetros, buscar da Weni
        if not vtex_session or not vtex_segment:
            try:
                weni_token = "f5a884633f31eef1ffb0480731f054267d0fb614"
                urn = context.contact.get("urn")
                if weni_token and urn:
                    tokens = self._get_tokens_from_weni(urn, weni_token)
                    if tokens:
                        vtex_session = vtex_session or tokens.get("session_token", "")
                        vtex_segment = vtex_segment or tokens.get("segment_token", "")
                else:
                    print(f"Condição não atendida: weni_token={bool(weni_token)}, urn={bool(urn)}")
            except Exception as e:
                print(f"Aviso: Não foi possível recuperar tokens da Weni: {str(e)}")
                import traceback
                print(f"Traceback completo: {traceback.format_exc()}")

        base_url = context.credentials.get("BASE_URL", "")
        #store_url = context.credentials.get("STORE_URL", "")
        store_url = "vendamais.lamoda.com.br"
        if not store_url.startswith("https://"):
            store_url = f"https://{store_url}"
        if not base_url.startswith("https://"):
            base_url = f"https://{base_url}"

        # Configurar ambiente e credenciais
        headers = {
            "Content-Type": "application/json"
        }
        session_information = self.get_session_information(base_url, vtex_session)
        orderform_id = self._create_orderform(base_url, headers, session_information["trade_policy"])
        if orderform_id:
            if isinstance(product_items, str):
                product_items = self._parse_product_items(product_items)
            self._add_items(base_url, headers, orderform_id, product_items, session_information["trade_policy"], session_information["vtex_id_client"], vtex_session, vtex_segment)
            checkout_url = f"{store_url}/login?returnUrl=/cart/?orderFormId={orderform_id}/#cart?sc={session_information['trade_policy']}"
            #checkout_url = f"{store_url}/checkout/?orderFormId={orderform_id}/#cart?sc={session_information["trade_policy"]}"
            return TextResponse({"order_form_id": orderform_id, "order_form_updated": True, "checkout_url": checkout_url})
        
        
        if not session_information:
            return TextResponse(data="Erro ao obter informações da sessão")
        
        # Validar se cost_center existe antes de buscar informações
        if not session_information.get("cost_center"):
            return TextResponse(data="Erro: Cost Center não encontrado na sessão. A sessão pode não ter sido criada corretamente com os dados de organização.")
        
        cost_center_information = self.get_cost_center_information(base_url, session_information["cost_center"], session_information["vtex_id_client"])
        
        try:
            # Parse product items if it's a string
            if isinstance(product_items, str):
                product_items = self._parse_product_items(product_items)
            
            # Fluxo mínimo para criação do carrinho
            orderform_id = self._create_orderform(base_url, headers, session_information["trade_policy"])
            
            # Adicionar UTM (não requer parâmetros adicionais)
            self._add_utm_source(base_url, headers, orderform_id, session_information["trade_policy"], session_information["org_id"], session_information["cost_center"])
            
            # Adicionar itens ao carrinho (etapa essencial)
            self._add_items(base_url, headers, orderform_id, product_items, session_information["trade_policy"], session_information["vtex_id_client"], vtex_session, vtex_segment)

            # Adiciona informações do usuário ao carrinho
            self._add_user_information(base_url, headers, orderform_id, session_information["email"], session_information["first_name"], session_information["last_name"], cost_center_information["name"], cost_center_information["state_registration"], cost_center_information["business_document"], cost_center_information["phone_number"])
            
            # Gerar link de checkout para pagamento
            #checkout_url = f"{store_url}/checkout/?orderFormId={orderform_id}/#cart?sc={session_information["trade_policy"]}"
            checkout_url = f"{store_url}login?returnUrl=/cart/?orderFormId={orderform_id}/#cart?sc={session_information["trade_policy"]}"
            
            # Montar resposta com o link de checkout
            payment_details = {
                "status": "success",
                "order_form_id": orderform_id,
                "checkout_url": checkout_url
            }
            
            return TextResponse(data=json.dumps(payment_details))
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            return TextResponse(data=f"Erro durante processamento do carrinho: {str(e)}")
       
    def _create_orderform(self, base_url, headers, trade_policy):
        """Cria um novo OrderForm e retorna seu ID"""
        orderform_url = f"{base_url}/api/checkout/pub/orderForm/?forceNewCart=True&sc={trade_policy}"
        orderform_response = requests.get(orderform_url, headers=headers)
        
        if orderform_response.status_code != 200:
            error_msg = f"Erro ao criar OrderForm: {orderform_response.status_code}"
            try:
                error_detail = orderform_response.json()
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                pass
            raise Exception(error_msg)
        
        orderform_data = orderform_response.json()
        orderform_id = orderform_data.get("orderFormId")
        
        if not orderform_id:
            raise Exception("Erro: OrderFormId não encontrado na resposta")
        
        return orderform_id
    
    def _add_utm_source(self, base_url, headers, orderform_id, trade_policy, org_id, cost_center):
        """Adiciona informações de UTM Source"""
        utm_url = f"{base_url}/api/checkout/pub/orderForm/{orderform_id}/attachments/marketingData?sc={trade_policy}"
        utm_data = {
            "utmSource": "Weni",
            "utmMedium": cost_center,
            "utmCampaign": org_id
        }
        
        utm_response = requests.post(utm_url, headers=headers, json=utm_data)
        
        if utm_response.status_code != 200:
            error_msg = f"Erro ao adicionar UTM: {utm_response.status_code}"
            try:
                error_detail = utm_response.json()
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                pass
            raise Exception(error_msg)
        
        return utm_response.json()
    
    def _add_items(self, base_url, headers, orderform_id, product_items, trade_policy, vtex_id_client, vtex_session, vtex_segment):
        """Adiciona os itens ao carrinho"""
        items_url = f"{base_url}/api/checkout/pub/orderForm/{orderform_id}/items?sc={trade_policy}"
        
        # Converter formato de produto_items para formato VTEX
        order_items = []
        for index, item in enumerate(product_items):
            # Handle the special format where keys are like "product_retailer_id=797"
            product_retailer_id = ""
            quantity = 1
            
            # Extract values from the special key format
            for key in item.keys():
                if key.startswith("product_retailer_id="):
                    product_retailer_id = key.split("=", 1)[1]
                elif key.startswith("quantity="):
                    try:
                        quantity = int(key.split("=", 1)[1])
                    except ValueError:
                        quantity = 1
            
            # If no special format found, try normal dictionary access
            if not product_retailer_id:
                product_retailer_id = str(item.get("product_retailer_id", ""))
                quantity = item.get("quantity", 1)
            
            # Ensure product_retailer_id is always a string before splitting
            product_retailer_id = str(product_retailer_id)
            parts = product_retailer_id.split("#")
            
            # Get retailer_id and seller, with fallback values
            retailer_id = (parts[0] or "").strip() if len(parts) > 0 else ""
            seller = parts[1] if len(parts) > 1 else "1"
            if not retailer_id:
                raise Exception(
                    f"Item na posição {index + 1} sem id válido (product_retailer_id vazio ou inválido). "
                    f"Recebido: {item}. Use o formato product_retailer_id='SKU' (ex: '260650' ou '260650#1')."
                )
            # API VTEX Checkout espera PascalCase (Id, Seller, Quantity, Index) - erro CHK0022
            order_items.append({
                "Id": retailer_id,
                "Seller": seller,
                "Quantity": int(quantity),
                "Index": index
            })
        
        items_data = {
            "orderItems": order_items
        }
        
        print(f"Sending items data: {json.dumps(items_data)}")  # Debug log
        
        headers["Cookie"] = f"vtex_session={vtex_session};vtex_segment={vtex_segment}"
        headers["VtexIdclientAutCookie"] = vtex_id_client

        items_response = requests.post(items_url, headers=headers, json=items_data)
        
        if items_response.status_code != 200:
            error_msg = f"Erro ao adicionar itens: {items_response.status_code}"
            try:
                error_detail = items_response.json()
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                pass
            raise Exception(error_msg)
        
        return items_response.json() 

    def get_session_information(self, base_url, vtex_session):
        url = f"{base_url}/api/sessions?items=*"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"vtex_session={vtex_session}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Erro ao obter informações da sessão: {response.status_code}")
        
        response = response.json()
        print("response", response)
        namespaces = response.get("namespaces", {})
        

        storefront_permissions = namespaces.get("storefront-permissions", {})
        
        cost_center = storefront_permissions.get("costcenter", {}).get("value", "") if storefront_permissions else ""
        org_id = storefront_permissions.get("organization", {}).get("value", "") if storefront_permissions else ""
        
        if not cost_center or not org_id:
            print("ERRO: Cost Center ou Org ID não encontrados na resposta")

        profile = namespaces.get("profile", {})
        
        email = profile.get("email", {}).get("value", "") if profile.get("email") else ""
        first_name = profile.get("firstName", {}).get("value", "") if profile.get("firstName") else ""
        last_name = profile.get("lastName", {}).get("value", "") if profile.get("lastName") else ""
        
        store = namespaces.get("store", {})
        trade_policy = store.get("channel", {}).get("value", "") if store.get("channel") else ""

        #public = namespaces.get("public", {})
        #vtex_id_client = public.get("authCookie", {}).get("value", "") if public.get("authCookie") else ""
        #usando esse outro método porque está retornando literalmente assim na API "value": "{auth_cookie_value}"
        vtex_id_client = ""
        
        # Se authCookie não estiver disponível ou for placeholder, tentar usar cookie específico da conta
        if not vtex_id_client or vtex_id_client == "{auth_cookie_value}":
            cookie_namespace = namespaces.get("cookie", {})
            account_id = namespaces.get("account", {}).get("id", {}).get("value", "")
            
            # Tentar cookie específico da conta por ID
            if account_id:
                cookie_key = f"VtexIdclientAutCookie_{account_id}"
                if cookie_key in cookie_namespace:
                    vtex_id_client = cookie_namespace[cookie_key].get("value", "")
            
            """# Se ainda não tiver, tentar por nome da conta
            if (not vtex_id_client or vtex_id_client == "{auth_cookie_value}") and account_name:
                cookie_key = f"VtexIdclientAutCookie_{account_name}"
                if cookie_key in cookie_namespace:
                    vtex_id_client = cookie_namespace[cookie_key].get("value", "")
            
            # Último recurso: usar VtexIdclientAutCookie genérico
            if not vtex_id_client or vtex_id_client == "{auth_cookie_value}":
                if "VtexIdclientAutCookie" in cookie_namespace:
                    vtex_id_client = cookie_namespace["VtexIdclientAutCookie"].get("value", "") """
        
        print(f"DEBUG: Dados extraídos - cost_center: {cost_center}, org_id: {org_id}, email: {email}, trade_policy: {trade_policy}, vtex_id_client: {bool(vtex_id_client)}")

        return {
            "cost_center": cost_center,
            "org_id": org_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "trade_policy": trade_policy,
            "vtex_id_client": vtex_id_client,
        }
    
    def get_cost_center_information(self, base_url, cost_center, vtex_id_client):
        url = f"{base_url}/_v/private/graphql/v1"
        payload = json.dumps({
        "query": f"query {{ getCostCenterById (id: \"{cost_center}\") {{ id name organization stateRegistration businessDocument phoneNumber }} }}"
        })
        if not vtex_id_client:
            raise Exception("Erro: VtexIdclientAutCookie não encontrado na resposta")
        
        headers = {
            "Cookie": f"VtexIdclientAutCookie={vtex_id_client}",
            "Content-Type": "application/json"
        }

        print(f"DEBUG: Buscando cost center - ID: {cost_center}")
        print(f"DEBUG: URL: {url}")
        print(f"DEBUG: Payload: {payload}")
        
        response = requests.post(url, headers=headers, data=payload)
        
        print(f"DEBUG: Status Code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"Erro ao obter informações do custo: {response.status_code}"
            try:
                error_detail = response.json()
                print(f"DEBUG: Erro detalhado: {error_detail}")
                error_msg += f" - {json.dumps(error_detail)}"
            except:
                print(f"DEBUG: Response text: {response.text}")
            raise Exception(error_msg)
        
        response_data = response.json()
        print(f"DEBUG: Resposta completa da API: {json.dumps(response_data)}")

        cost_center_information = response_data.get("data", {}).get("getCostCenterById")
        
        print(f"DEBUG: cost_center_information: {cost_center_information}")
        
        # Validar se cost_center_information existe e não é None
        if not cost_center_information:
            error_msg = "Erro: Cost Center não encontrado na resposta da API"
            if "errors" in response_data:
                error_msg += f" - Erros: {json.dumps(response_data['errors'])}"
            raise Exception(error_msg)
        
        name = cost_center_information.get("name", "")
        state_registration = cost_center_information.get("stateRegistration", "")
        business_document = cost_center_information.get("businessDocument", "")
        phone_number = cost_center_information.get("phoneNumber", "")

        return {
            "name": name,
            "state_registration": state_registration,
            "business_document": business_document,
            "phone_number": phone_number
        }
    
    def _get_tokens_from_weni(self, urn: str, api_token: str) -> dict:
        """
        Recupera sessionToken e segmentToken do contato da Weni.
        
        Args:
            urn (str): URN do contato (ex: "whatsapp:555133334444")
            api_token (str): Token de autenticação da API Weni
        
        Returns:
            dict: {"session_token": str, "segment_token": str} ou {} se não encontrar
        """
        try:
            base_url = "https://flows.weni.ai/api/v2/contacts.json"
            encoded_urn = quote(urn, safe="")
            url = f"{base_url}?urn={encoded_urn}"
            headers = {
                "Authorization": f"token {api_token}",
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            if not results:
                return {}
            
            contact = results[0]
            fields = contact.get("fields", {})
            
            session_token = fields.get("vtex_session_token") or fields.get("sessionToken")
            segment_token = fields.get("vtex_segment_token") or fields.get("segmentToken")
            
            if session_token and segment_token:
                return {
                    "session_token": session_token,
                    "segment_token": segment_token
                }
            
            return {}
        except Exception as e:
            print(f"Erro ao recuperar tokens da Weni: {str(e)}")
            return {}
    
    def _add_user_information(self, base_url, headers, orderform_id, email, first_name, last_name, corporate_name, corporate_document, state_inscription, corporate_phone):
        """Adiciona informações do usuário ao carrinho"""
        user_url = f"{base_url}/api/checkout/pub/orderform/{orderform_id}/attachments/clientPreferencesData"

        user_data = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "corporateName": corporate_name,
            "tradeName": corporate_name,
            "corporateDocument": corporate_document,
            "stateInscription": state_inscription,
            "corporatePhone": corporate_phone,
            "isCorporate": True
        }

        user_response = requests.post(user_url, headers=headers, json=user_data)
        print(f"Adicionando informações do usuário no carrinho: {user_response.json()}")
        if user_response.status_code != 200:
            raise Exception(f"Erro ao adicionar informações do usuário: {user_response.status_code}")
        
        return user_response.json()
    