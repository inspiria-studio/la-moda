from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
import sys
import ast

class SearchProduct(Tool):    
    def intelligentSearch(self, product_name, url, store_url, vtex_segment):
        """
        Searches for products by name and collects detailed information, determining seller ID if necessary.

        Args:
            product_name (str): Name of the product to search for
            url (str): Base URL for the search

        Returns:
            dict: Dictionary with product names as keys and their details including all variations
        """
        products_structured = {}

        search_url = f"{url}/api/io/_v/api/intelligent-search/product_search/?query={product_name}&simulationBehavior=regionalize1p"
        print(f"search_url: {search_url}")

        headers = {
            "Cookie": f"vtex_segment={vtex_segment}"
        }

        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            products = response.json().get("products", [])

            for product in products:
                if not product.get("items"):
                    print(f"Skipping product {product.get('productId')} due to missing items.")
                    continue
                
                product_name_vtex = product.get("productName", "")
                
                # Capturar todas as variações (items) do produto
                variations = []
                for item in product.get("items", []):
                    sku_id = item.get("itemId")
                    sku_name = item.get("nameComplete")
                    variation_item = item.get("variations", [])
                    # Tentar múltiplas formas de obter o preço
                    price = None
                    
                    # Método 1: sellers[0].commertialOffer.Price
                    sellers = item.get("sellers", [])
                    if sellers and len(sellers) > 0:
                        commercial_offer = sellers[0].get("commertialOffer", {})
                        price = commercial_offer.get("Price")
                    
                    # Método 2: campo price direto no item
                    if price is None:
                        price = item.get("price")
                    
                    # Método 3: sellers[0].Price (estrutura antiga)
                    if price is None and sellers and len(sellers) > 0:
                        price = sellers[0].get("Price")
                    
                    # Debug removido - preço sendo capturado corretamente
                    
                    if sku_id:
                        variation = {
                            "sku_id": sku_id,
                            "sku_name": sku_name,
                            "variations": variation_item,
                            "price": price
                        }
                        variations.append(variation)

                if variations:
                    limited_variations = variations[:3]
                    description = product.get("description", "")
                    if len(description) > 200:
                        description = description[:200] + "..."
                    
                    spec_groups = product.get("specificationGroups", [])
                    simplified_specs = []
                    for group in spec_groups[:2]:
                        if group.get("specifications"):
                            limited_specs = group["specifications"][:2]
                            simplified_group = {
                                "name": group.get("name", ""),
                                "specifications": []
                            }
                            for spec in limited_specs:
                                simplified_group["specifications"].append({
                                    "name": spec.get("name", ""),
                                    "values": spec.get("values", [])[:2]
                                })
                            simplified_specs.append(simplified_group)
                    
                    product_structured = {
                        "variations": limited_variations,
                        "description": description,
                        "brand": product.get("brand", ""),
                        "specification_groups": simplified_specs,
                        "productLink": f"{store_url}{product.get('link', '')}",
                        "price": price
                    }
                    
                    products_structured[product_name_vtex] = product_structured

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {product_name}: {e}")
        except json.JSONDecodeError as e:
             print(f"Error decoding JSON response for {product_name}: {e}")

        return products_structured
    

    def filterProductsWithStock(self, products_structured, products_with_stock):
        """
        Filtra os produtos estruturados para manter apenas aqueles que têm estoque e inclui o preço.
        
        Args:
            products_structured (dict): Estrutura de produtos com variações
            products_with_stock (list): Lista de produtos que passaram na simulação do carrinho (com preço)
        
        Returns:
            dict: Estrutura de produtos filtrada apenas com produtos que têm estoque e preço
        """
        if not products_with_stock:
            return {}
        
        # Criar map dos sku_ids para preço
        sku_price_map = {product.get("sku_id"): product.get("price") for product in products_with_stock}
        sku_ids_with_stock = set(sku_price_map.keys())
        
        # Filtrar a estrutura de produtos
        filtered_products = {}
        for product_name_vtex, product_data in products_structured.items():
            # Filtrar apenas as variações que têm estoque
            filtered_variations = []
            for variation in product_data["variations"]:
                if variation.get("sku_id") in sku_ids_with_stock:
                    variation = variation.copy()
                    variation["price"] = sku_price_map.get(variation["sku_id"])
                    filtered_variations.append(variation)
            # Só incluir o produto se ele tiver pelo menos uma variação com estoque
            if filtered_variations:
                filtered_product_data = product_data.copy()
                filtered_product_data["variations"] = filtered_variations
                filtered_products[product_name_vtex] = filtered_product_data
        return filtered_products
    

    def selectProducts(self, cart_simulation, products_details):
        """
        Selects products based on availability and delivery channel, and attaches price info.
        
        Args:
            cart_simulation (dict): Cart simulation result
            products_details (list): List of product details
            
        Returns:
            list: List containing details of selected products only, with price
        """
        selected_products_details = []
        available_original_ids = set()
        item_index_to_original_id = {}
        sku_price_map = {}
        for i, item in enumerate(cart_simulation.get("items", [])):
            if item.get("availability", "").lower() == "available":
                original_id = item.get("id")
                if original_id:
                    available_original_ids.add(original_id)
                    item_index_to_original_id[i] = original_id
                    # Pega o preço do item (preferencialmente sellingPrice, senão price)
                    price = item.get("sellingPrice")
                    if price is None:
                        price = item.get("price")
                    if price is not None:
                        sku_price_map[original_id] = price / 100 if price > 100 else price  # VTEX pode retornar em centavos

        selected_original_ids = set()
        for product_detail in products_details:
            sku_id = product_detail.get("sku_id")
            if sku_id in available_original_ids:
                # Adiciona o preço ao detalhe do produto
                product_detail = product_detail.copy()
                if sku_id in sku_price_map:
                    product_detail["price"] = sku_price_map[sku_id]
                selected_products_details.append(product_detail)
            elif not sku_id in selected_original_ids:
                pass
        return selected_products_details
    

    def cartSimulation(self, base_url, product_name, products_details, seller, quantity, postal_code):
        """
        Performs cart simulation to check availability and delivery channel.
        
        Args:
            base_url (str): Base URL of the API
            product_name (str): Product name
            products_details (list): List of product details
            seller (str): Seller ID
            postal_code (str): Delivery postal code
            
        Returns:
            list: List of details of selected products
        """
        if not products_details:
            return []
            
        items = []
        for product in products_details:
            sku_id = product.get("sku_id")
            items.append({"id": sku_id, "quantity": quantity, "seller": seller})
        url = f"{base_url}/api/checkout/pub/orderForms/simulation"
        payload = {
            "items": items,
            "postalCode": postal_code
        }
        print(f"payload: {payload}")
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {product_name}: {e}")
            return []
        else:
            if response.json()["items"]:
                selected_products = self.selectProducts(
                    cart_simulation=response.json(), 
                    products_details=products_details
                )
                return selected_products
            else:
                return []
            
    
    def getPreferredSellerId(self, postal_code, url, country="BRA"):
        
        search_url = f"{url}/api/checkout/pub/regions?country={country}&postalCode={postal_code}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            response = response.json()
            print(f"Sellers found: {response}, for {postal_code}")

            seller = response[0]["sellers"][0]["id"]
        except Exception as e:
            print(f"Error fetching data for {postal_code}: {e}")
            return None
        return seller
    
    def send_capi(self, auth_token: str, channel_uuid: str, contact_urn: str, event_type: str):
        url = f"https://flows.weni.ai/conversion/"

        if not auth_token:
            print("Auth token not configured")
        
        if not channel_uuid:
            print("Channel UUID not configured")
        
        if not contact_urn:
            print("Contact URN not configured")
        
        if not event_type:
            print("Event type not configured")
        
        if event_type not in ["lead", "purchase"]:
            print("Invalid event type")

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel_uuid": channel_uuid,
            "contact_urn": contact_urn,
            "event_type": event_type, # lead or purchase
        }

        print("CAPI_EVENT: ", payload)

        response = requests.post(url, headers=headers, json=payload)
        status_code = response.status_code
        if status_code == 200:
            return True
        else:
            print(f"Failed to send CAPI event: {response.json()}")
            return False

    
    def execute(self, context: Context) -> TextResponse:
        product_names_param = context.parameters.get("product_names", "")
        vtex_segment = context.parameters.get("vtex_segment", "")

        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")

        if not base_url:
            return TextResponse(data={"error": "BASE_URL not configured"})
        
        auth_token = context.project.get("auth_token", "")
        channel_uuid = context.contact.get("channel_uuid", "")
        contact_urn = context.contact.get("urn", "")

        product_names = []
        if isinstance(product_names_param, list):
            product_names = product_names_param
        elif isinstance(product_names_param, str):
            param_str = product_names_param.strip()
            if not param_str:
                print("Product names param is an empty or whitespace string.")
            else:
                try:
                    parsed_value = ast.literal_eval(param_str)
                    if isinstance(parsed_value, list):
                        product_names = parsed_value
                    else:
                        product_names = [param_str]
                except (ValueError, SyntaxError):

                    if param_str.startswith('[') and param_str.endswith(']'):
                        content = param_str[1:-1].strip()
                        if not content:
                            product_names = []
                        else:
                            product_names = [item.strip() for item in content.split(',')]
                    else:
                        product_names = [param_str]
        
        # 1. Buscar produtos no intelligent search
        product_response_final = []
        for product_name in product_names:
            product_response = self.intelligentSearch(
                product_name=product_name,
                url=base_url,
                store_url=store_url,
                vtex_segment=vtex_segment
            )
            product_response_final.append(product_response)

        # 2. Converter para lista de SKUs para simulação do carrinho
        sku_list = []
        for product_response in product_response_final:
            for product_name_vtex, product_data in product_response.items():
                for variation in product_data["variations"]:
                    sku_list.append({
                        "sku_id": variation["sku_id"],
                        "sku_name": variation["sku_name"],
                        "variations": variation["variations"],
                        "price": variation.get("price"),
                        "description": product_data["description"],
                        "brand": product_data["brand"],
                        "specification_groups": product_data["specification_groups"]
                    })
                
        # Print das SKUs encontradas no intelligent search
        found_skus = [product["sku_id"] for product in sku_list]
        print(f"SKUs encontradas no intelligent search: {found_skus}")
        print(f"Total de SKUs encontradas: {len(found_skus)}")
                
        # 3. Realizar simulação do carrinho para verificar disponibilidade
        #seller = self.getPreferredSellerId(postal_code, base_url, country="BRA")
        #if not seller:
        #    return TextResponse(data={"error": "No seller found for postal code: " + postal_code})
        
        #quantity = 1
        # products_with_stock = self.cartSimulation(
        #        base_url=base_url, 
        #        product_name=product_name,
        #        products_details=product_response_final, 
        #        seller=seller,
        #        quantity=quantity,
        #        postal_code=postal_code
        #    )
            
        # Print das SKUs que passaram na simulação do carrinho
        #skus_with_stock = [product.get("sku_id") for product in products_with_stock]
        #print(f"SKUs que passaram na simulação do carrinho: {skus_with_stock}")
        #print(f"Total de SKUs com estoque: {len(skus_with_stock)}")
            
        # 4. Filtrar produtos com estoque disponível usando a estrutura original
        #products_structured_with_stock = self.filterProductsWithStock(
        #        product_response, products_with_stock
        #    )
            
        # Print das SKUs no resultado final filtrado
        final_skus = []
        #for product_name_vtex, product_data in products_structured_with_stock.items():
        #    for variation in product_data["variations"]:
        #        final_skus.append(variation["sku_id"])
        print(f"SKUs no resultado final filtrado: {final_skus}")
        print(f"Total de SKUs no resultado final: {len(final_skus)}")

        json_data = json.dumps(sku_list)
        size_bytes = sys.getsizeof(json_data)
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024

        event_type = "lead"

        if "whatsapp" in contact_urn:
            if self.send_capi(auth_token, channel_uuid, contact_urn, event_type):
                print("CAPI event sent successfully")
            else:
                print("Failed to send CAPI event")

        print(f"Size of product_response: {size_bytes} bytes / {size_kb:.2f} KB / {size_mb:.4f} MB")

        return TextResponse(data=sku_list)