from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json

class GetCartInfo(Tool):

    def execute(self, context: Context) -> TextResponse:
        orderform_id = context.parameters.get("orderform_id", "")

        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        if not store_url.startswith("https://"):
            store_url = f"https://{store_url}"
        if not base_url.startswith("https://"):
            base_url = f"https://{base_url}"

        headers = {
            "Content-Type": "application/json"
        }
        if orderform_id:
            orderform_data = self.get_orderform_data(base_url, headers, orderform_id)
            return TextResponse(orderform_data)            
       
    def get_orderform_data(self, base_url, headers, orderform_id):
        """Cria um novo OrderForm e retorna seu ID"""
        orderform_url = f"{base_url}/api/checkout/pub/orderForm/{orderform_id}"
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
        
        if not orderform_id:
            raise Exception("Erro: OrderFormId não encontrado na resposta")
        
        return orderform_data
