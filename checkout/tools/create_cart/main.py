from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
import os
from dotenv import load_dotenv


class CreateCart(Tool):
    def _parse_product_items(self, product_items_str):
        """Parse product items from string format to proper dictionary format"""
        try:
            # If it's already a list of dicts, return as is
            if isinstance(product_items_str, list):
                print(f"Product items already parsed: {product_items_str}")
                return product_items_str
            
            print(f"Parsing product items string: {product_items_str}")
            
            # Remove brackets and split items
            items_str = product_items_str.strip('[]').strip()
            if not items_str:
                return []
            
            # Split into individual items and parse each one
            items = []
            for item_str in items_str.split('}, {'):
                # Clean up the item string
                item_str = item_str.strip('{}').strip()
                print(f"Processing item string: {item_str}")
                
                # Split into key-value pairs
                item_dict = {}
                for pair in item_str.split(','):
                    pair = pair.strip()
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert numeric values, but keep product_retailer_id as string
                        if key == 'product_retailer_id':
                            # Keep product_retailer_id as string for later processing
                            value = str(value)
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '').isdigit():
                            value = float(value)
                        
                        item_dict[key] = value
                
                if item_dict:
                    items.append(item_dict)
                    print(f"Added item: {item_dict}")
            
            print(f"Final parsed items: {items}")
            return items
                
        except Exception as e:
            print(f"Error parsing product items: {str(e)}")
            return []

    def execute(self, context: Context) -> TextResponse:
        product_items = context.parameters.get("product_items", [])
        orderform_id = context.parameters.get("orderform_id", "")
        vtex_session = context.parameters.get("vtex_session", "")
        vtex_segment = context.parameters.get("vtex_segment", "")

        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        if not store_url.startswith("https://"):
            store_url = f"https://{store_url}"
        if not base_url.startswith("https://"):
            base_url = f"https://{base_url}"

        # Configurar ambiente e credenciais
        headers = {
            "Content-Type": "application/json"
        }
        session_information = self.get_session_information(base_url, vtex_session)
        if orderform_id:
            if isinstance(product_items, str):
                product_items = self._parse_product_items(product_items)
            self._add_items(base_url, headers, orderform_id, product_items, session_information["trade_policy"], session_information["org_id"], session_information["vtex_id_client"], vtex_session, vtex_segment)
            return TextResponse({"order_form_id": orderform_id, "order_form_updated": True, "checkout_url": f"{store_url}/checkout/?orderFormId={orderform_id}/#cart?sc={session_information["trade_policy"]}"})
        
        
        if not session_information:
            return TextResponse(data="Erro ao obter informações da sessão")
        print("base_url", base_url)
        print("session_information", session_information)
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
            checkout_url = f"{store_url}/checkout/?orderFormId={orderform_id}/#cart?sc={session_information["trade_policy"]}"
            
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
            retailer_id = parts[0] if len(parts) > 0 else ""
            seller = parts[1] if len(parts) > 1 else "1"
            
            order_items.append({
                "id": retailer_id,
                "seller": seller,
                "quantity": quantity,
                "index": index
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
        print("response", response)
        if response.status_code != 200:
            raise Exception(f"Erro ao obter informações da sessão: {response.status_code}")
        
        response = response.json()
        namespaces = response.get("namespaces", {})

        storefront_permissions = namespaces.get("storefront-permissions", {})
        cost_center = storefront_permissions.get("costcenter", {}).get("value", "")
        org_id = storefront_permissions.get("organization", {}).get("value", "")
        if not cost_center or not org_id:
            print("Erro: Cost Center ou Org ID não encontrados na resposta")

        profile = namespaces.get("profile", {})
        email = profile.get("email", {}).get("value", "")
        first_name = profile.get("firstName", {}).get("value", "")
        last_name = profile.get("lastName", {}).get("value", "")
        
        store = namespaces.get("store", {})
        trade_policy = store.get("channel", {}).get("value", "")

        public = namespaces.get("public", {})
        vtex_id_client = public.get("authCookie", {}).get("value", "")

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

        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code != 200:
            raise Exception(f"Erro ao obter informações do custo: {response.status_code}")
        
        response = response.json()

        cost_center_information = response.get("data", {}).get("getCostCenterById", {})
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

        if user_response.status_code != 200:
            raise Exception(f"Erro ao adicionar informações do usuário: {user_response.status_code}")
        
        return user_response.json()
    