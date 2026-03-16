from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
import sys
import ast
from urllib.parse import quote
import re

class SearchProduct(Tool):
    
    def _normalize_word_to_singular(self, word):
        """
        Converte uma palavra do plural para singular em português.
        Aplica regras comuns de pluralização reversa.
        
        Args:
            word (str): Palavra no plural
            
        Returns:
            str: Palavra no singular
        """
        if not word or len(word) < 2:
            return word
        
        word = word.strip()
        
        # Dicionário de exceções para adjetivos e palavras irregulares
        exceptions = {
            "azuis": "azul",
            "brancas": "branco",
            "brancos": "branco",
            "pretas": "preto",
            "pretos": "preto",
            "vermelhas": "vermelho",
            "vermelhos": "vermelho",
            "verdes": "verde",
            "amarelas": "amarelo",
            "amarelos": "amarelo",
            "cinzas": "cinza",
            "rosas": "rosa",
            "roxas": "roxo",
            "roxos": "roxo",
            "beiges": "bege",
            "marrom": "marrom",  # marrom não muda no plural
            "grandes": "grande",
            "pequenas": "pequeno",
            "pequenos": "pequeno",
        }
        
        # Verificar se é uma exceção conhecida
        if word.lower() in exceptions:
            return exceptions[word.lower()]
        
        # Casos especiais de pluralização reversa
        # Palavras terminadas em "ões" -> "ão"
        if word.endswith("ões"):
            return word[:-3] + "ão"
        
        # Palavras terminadas em "ais" -> "al"
        if word.endswith("ais") and len(word) > 3:
            return word[:-3] + "al"
        
        # Palavras terminadas em "eis" -> "el"
        if word.endswith("eis") and len(word) > 3:
            return word[:-3] + "el"
        
        # Palavras terminadas em "óis" -> "ol"
        if word.endswith("óis"):
            return word[:-3] + "ol"
        
        # Palavras terminadas em "ns" -> "m"
        if word.endswith("ns") and len(word) > 2:
            return word[:-2] + "m"
        
        # Palavras terminadas em "is" -> "il" (casos comuns, mas com cuidado)
        # Não aplicar para adjetivos de cor comuns que terminam em "is"
        if word.endswith("is") and len(word) > 4:
            # Exceções: palavras que terminam em "is" mas não devem virar "il"
            # Ex: "azuis" já foi tratado acima, mas outras podem existir
            # Por segurança, só aplicar se não for um adjetivo de cor comum
            if not word.lower() in ["azuis", "brancas", "pretas", "verdes"]:
                return word[:-2] + "il"
        
        # Palavras terminadas em "us" -> "u" (alguns casos)
        if word.endswith("us") and len(word) > 4:
            return word[:-1]
        
        # Caso geral: remover "s" final se a palavra terminar em "s"
        # Mas não remover se for apenas uma letra ou se terminar em "ss"
        if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
            return word[:-1]
        
        return word
    
    def _normalize_to_singular(self, text):
        """
        Converte texto do plural para singular em português.
        Normaliza cada palavra individualmente para lidar com frases completas.
        
        Args:
            text (str): Texto no plural (pode ser uma frase)
            
        Returns:
            str: Texto no singular
        """
        if not text:
            return text
        
        text = text.strip()
        
        # Dividir o texto em palavras e normalizar cada uma
        words = text.split()
        normalized_words = [self._normalize_word_to_singular(word) for word in words]
        
        return " ".join(normalized_words)    
    def intelligentSearch(self, product_name, url, store_url):
        """
        Searches for products by name and collects detailed information, determining seller ID if necessary.

        Args:
            product_name (str): Name of the product to search for
            url (str): Base URL for the search
            store_url (str): Store URL for product links

        Returns:
            dict: Dictionary with product names as keys and their details including all variations
        """
        products_structured = {}

        # Normalizar o nome do produto para singular antes de buscar
        # Isso ajuda quando o usuário busca no plural
        normalized_name = self._normalize_to_singular(product_name)
        #print(f"product_name original: {product_name}")
        #print(f"product_name normalizado (singular): {normalized_name}")

        # Codificar o nome do produto para garantir que caracteres especiais sejam tratados corretamente
        encoded_product_name = quote(normalized_name, safe='')
        search_url = f"https://vendamais.lamoda.com.br/api/catalog_system/pub/products/search/?ft={encoded_product_name}"
        #print(f"search_url: {search_url}")

        headers = {
            "Accept": "application/json"
        }

        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            products = response.json() 

            #print(f"Total de produtos retornados pela API: {len(products)}")
            
            for product in products:
                if not product.get("items"):
                    print(f"Skipping product {product.get('productId')} due to missing items.")
                    continue
                
                product_name_vtex = product.get("productName", "")
                #print(f"Processando produto: {product_name_vtex} (ID: {product.get('productId')})")
                
                # Capturar todas as variações (items) do produto
                variations = []
                for item in product.get("items", []):
                    sku_id = item.get("itemId")
                    sku_name = item.get("nameComplete")
                    variation_item = item.get("variations", [])
                    # Tentar múltiplas formas de obter o preço e IsAvailable
                    price = None
                    is_available = False
                    
                    # Método 1: sellers[0].commertialOffer.Price e IsAvailable
                    sellers = item.get("sellers", [])
                    if sellers and len(sellers) > 0:
                        commercial_offer = sellers[0].get("commertialOffer", {})
                        price = commercial_offer.get("Price")
                        is_available = commercial_offer.get("IsAvailable", False)
                        #if price is not None:
                            #print(f"  Preço encontrado via commertialOffer.Price: {price}")
                    
                    # Método 2: campo price direto no item
                    if price is None:
                        price = item.get("price")
                        #if price is not None:
                            #print(f"  Preço encontrado via item.price: {price}")
                    
                    # Método 3: sellers[0].Price (estrutura antiga)
                    if price is None and sellers and len(sellers) > 0:
                        price = sellers[0].get("Price")
                        #if price is not None:
                            #print(f"  Preço encontrado via sellers[0].Price: {price}")
                    
                    if price is None:
                        print(f"  AVISO: Preço não encontrado para SKU {sku_id}")
                    
                    if sku_id:
                        variation = {
                            "sku_id": sku_id,
                            "sku_name": sku_name,
                            "variations": variation_item,
                            "price": price,
                            "is_available": is_available
                        }
                        variations.append(variation)
                        #print(f"  Variação adicionada: SKU {sku_id} - {sku_name} - Preço: {price}")

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
                    
                    # Usar o preço da primeira variação como preço do produto
                    product_price = limited_variations[0].get("price") if limited_variations else None
                    
                    # O link já vem completo da API, usar diretamente sem modificações
                    product_link = product.get("link", "")
                    print(f"product_link: {product_link}")
                    
                    product_structured = {
                        "variations": limited_variations,
                        "description": description,
                        "brand": product.get("brand", ""),
                        "specification_groups": simplified_specs,
                        "productLink": product_link,
                        "price": product_price
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
        
        # Valores de availability que indicam falta de estoque
        unavailable_statuses = ["withoutstock", "unavailable", "outofstock", "nostock"]
        
        for i, item in enumerate(cart_simulation.get("items", [])):
            availability = item.get("availability", "").lower()
            # Verificar se está disponível: deve ser "available" e NÃO pode ser nenhum status de indisponibilidade
            if availability == "available" and availability not in unavailable_statuses:
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
            else:
                # Log para debug: produto sem estoque
                original_id = item.get("id")
                availability_status = item.get("availability", "unknown")
                #print(f"Produto {original_id} excluído - availability: {availability_status}")

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
    

    def cartSimulation(self, base_url, product_name, products_details, seller, quantity):
        """
        Performs cart simulation to check availability and delivery channel.
        
        Args:
            base_url (str): Base URL of the API
            product_name (str): Product name
            products_details (list): List of product details
            seller (str): Seller ID
            quantity (int): Quantity to simulate for each item
            
        Returns:
            list: List of details of selected products
        """
        if not products_details:
            return []
            
        items = []
        for product in products_details:
            sku_id = product.get("sku_id")
            # Só adicionar item se tiver sku_id válido
            if sku_id:
                items.append({"id": sku_id, "quantity": quantity, "seller": seller})
        
        # Se não houver itens válidos, retornar lista vazia
        if not items:
            print("Nenhum item válido para simulação do carrinho")
            return []
        url = f"{base_url}/api/checkout/pub/orderForms/simulation"
        payload = {
            "items": items
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {product_name}: {e}")
            return []
        else:
            sim_data = response.json()
            sim_items = sim_data.get("items", [])
            if sim_items:
                # Debug: logar availability de cada item
                for i, item in enumerate(sim_items):
                    print(f"Simulation item[{i}] id={item.get('id')} availability={item.get('availability')}")
                selected_products = self.selectProducts(
                    cart_simulation=sim_data,
                    products_details=products_details
                )
                print(f"Selected products after simulation: {len(selected_products)}")
                return selected_products
            else:
                print("Cart simulation returned empty items - no stock or invalid SKU/seller/CEP for this combination")
                return []
            
    
    def getPreferredSellerId(self, postal_code, url, country="BRA"):
        
        search_url = f"{url}/api/checkout/pub/regions?country={country}&postalCode={postal_code}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            response = response.json()

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

        print(f"product_names_param: {product_names_param}")
        # Verifica se o parâmetro está vazio ou representa um número (caso tenha entrado um CEP ou valor indevido)
        if not product_names_param or (
            isinstance(product_names_param, (int, float)) or
            (isinstance(product_names_param, str) and product_names_param.strip().isdigit())
        ):
            return TextResponse(data={"warning": "Informe o nome de pelo menos um produto para buscar"})

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
                        # String que parece uma lista: "[item1, item2]"
                        content = param_str[1:-1].strip()
                        if not content:
                            product_names = []
                        else:
                            product_names = [item.strip() for item in content.split(',')]
                    elif ',' in param_str:
                        # String com vírgulas mas sem colchetes: "item1, item2, item3"
                        # Dividir por vírgulas e limpar espaços
                        product_names = [item.strip() for item in param_str.split(',') if item.strip()]
                    else:
                        # String única sem vírgulas
                        product_names = [param_str]
        
        # 1. Buscar produtos no intelligent search
        product_response_final = []
        for product_name in product_names:
            product_response = self.intelligentSearch(
                product_name=product_name,
                url=base_url,
                store_url=store_url,
            )
            product_response_final.append(product_response)

        # 2. Converter para lista de SKUs (incluindo is_available da API de busca)
        sku_list = []
        for product_response in product_response_final:
            for product_name_vtex, product_data in product_response.items():
                for variation in product_data["variations"]:
                    sku_list.append({
                        "sku_id": variation["sku_id"],
                        "sku_name": variation["sku_name"],
                        "variations": variation["variations"],
                        "price": variation.get("price"),
                        "is_available": variation.get("is_available", False),
                        "description": product_data["description"],
                        "brand": product_data["brand"],
                        "specification_groups": product_data["specification_groups"],
                        "productLink": product_data.get("productLink", "")
                    })
        if not sku_list:
            print("Nenhuma SKU encontrada na busca")
            return TextResponse(data=sku_list)
        
        # 3. Verificar disponibilidade usando cartSimulation com prioridade para o seller "1"
        #    e fallback para o seller "lamodab2bcariacica", sempre simulando com quantity = 100.
        quantity = 100

        # Simulação com seller principal "1" para todos os SKUs
        products_with_stock_seller1 = self.cartSimulation(
            base_url=base_url,
            product_name=", ".join(product_names) if product_names else "",
            products_details=sku_list,
            seller="1",
            quantity=quantity,
        )

        # Identificar SKUs que ainda não ficaram disponíveis
        available_ids_seller1 = {p.get("sku_id") for p in products_with_stock_seller1}
        fallback_candidates = [
            p for p in sku_list
            if p.get("sku_id") and p.get("sku_id") not in available_ids_seller1
        ]

        # Simulação com seller fallback "lamodab2bcariacica" apenas para SKUs ainda indisponíveis
        products_with_stock_seller2 = []
        if fallback_candidates:
            products_with_stock_seller2 = self.cartSimulation(
                base_url=base_url,
                product_name=", ".join(product_names) if product_names else "",
                products_details=fallback_candidates,
                seller="lamodab2bcariacica",
                quantity=quantity,
            )

        # Unificar resultados de ambos os sellers, evitando duplicidade por sku_id
        products_with_stock_map = {}
        for p in products_with_stock_seller1 + products_with_stock_seller2:
            sku_id = p.get("sku_id")
            if sku_id and sku_id not in products_with_stock_map:
                products_with_stock_map[sku_id] = p

        products_with_stock = list(products_with_stock_map.values())
        print(
            f"SKUs disponíveis após cartSimulation: {len(products_with_stock)} de {len(sku_list)} "
            f"(seller '1' + fallback 'lamodab2bcariacica')"
        )

        # 4. Montar resultado final (mesmo formato de antes, sem o campo is_available na saída)
        final_skus = []
        for p in products_with_stock:
            final_skus.append({
                "sku_id": p["sku_id"],
                "sku_name": p["sku_name"],
                "variations": p["variations"],
                "price": p.get("price"),
                "description": p["description"],
                "brand": p["brand"],
                "specification_groups": p["specification_groups"],
                "productLink": p.get("productLink", "")
            })


        json_data = json.dumps(final_skus)
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

        if not final_skus:
            return TextResponse(data={"error": "Produto está faltando no estoque"})

        return TextResponse(data=final_skus)