from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class CheckGiftcardBalance(Tool):

    def _get_giftcard_id_from_masterdata(
        self,
        base_url: str,
        app_key: str,
        app_token: str,
        email: str,
    ) -> int:
        """
        Usa a API de Master Data (`/api/dataentities/GD/search`) para buscar o cartão
        e retornar apenas o `cardId` (giftCardId).
        """
        # Garantir que a URL base não tenha aspas extras nem barra no final
        base_url = base_url.strip().strip('"').strip("'").rstrip("/")

        # Endpoint da API de Master Data (GD)
        search_url = f"{base_url}/api/dataentities/GD/search"

        # Data atual para filtrar cartões não expirados
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Filtros semelhantes ao curl informado:
        # _where=expiringDate>NOW AND email={email} AND balance>0
        where_clause = f"expiringDate>{now_iso} AND email={email} AND balance>0"

        params = {
            "_size": 1,
            "_offset": 0,
            "_fields": "cardId",
            "_where": where_clause,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-VTEX-API-AppKey": app_key,
            "X-VTEX-API-AppToken": app_token,
        }

        response = requests.get(search_url, headers=headers, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Erro ao consultar Master Data (GD): {response.status_code} - {response.text}"
            )

        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            raise Exception(
                "Nenhum giftcard encontrado para os filtros informados (email, expiringDate e balance)."
            )

        first_item = data[0]
        card_id = first_item.get("cardId")
        if card_id is None:
            raise Exception("Resposta da API de Master Data não contém o campo 'cardId'.")

        return card_id

    def execute(self, context: Context) -> TextResponse:
        # Agora o ID do giftcard será obtido via Master Data a partir do e-mail
        email = context.parameters.get("email", "")

        if not email:
            return TextResponse(
                data="Erro: e-mail não fornecido para buscar o giftcard"
            )

        base_url = context.credentials.get("BASE_URL", "")
        app_key = context.credentials.get("VTEX_APP_KEY", "")
        app_token = context.credentials.get("VTEX_APP_TOKEN", "")

        if not base_url:
            return TextResponse(data="Erro: Base URL não configurada")

        if not app_key or not app_token:
            return TextResponse(data="Erro: Credenciais VTEX não configuradas")

        # Garantir que a URL base não tenha aspas extras nem barra no final
        base_url = base_url.strip().strip('"').strip("'").rstrip("/")

        try:
            # 1) Buscar o giftCardId (cardId) na API de Master Data (GD)
            giftcard_id = self._get_giftcard_id_from_masterdata(
                base_url=base_url,
                app_key=app_key,
                app_token=app_token,
                email=email,
            )

            # 2) Construir URL da API de giftcards com o ID obtido
            api_url = f"{base_url}/api/giftcards/{giftcard_id}"

            # Configurar headers
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-VTEX-API-AppKey": app_key,
                "X-VTEX-API-AppToken": app_token,
            }

            # Fazer requisição à API de giftcards
            response = requests.get(api_url, headers=headers, timeout=30)

            if response.status_code == 200:
                giftcard_data = response.json()

                # Extrair informações relevantes da API
                giftcard_id_api = giftcard_data.get("id", "")
                balance = giftcard_data.get("balance", 0)
                emission_date = giftcard_data.get("emissionDate", "")
                expiring_date = giftcard_data.get("expiringDate", "")
                currency_code = giftcard_data.get("currencyCode", "BRL")
                transactions = giftcard_data.get("transactions", {})

                # Formatar resposta
                result = {
                    "status": "success",
                    "giftcard_id": giftcard_id_api or giftcard_id,
                    "balance": balance,
                    "currency_code": currency_code,
                    "emission_date": emission_date,
                    "expiring_date": expiring_date,
                    "transactions": transactions,
                    "message": f"Saldo do giftcard: {currency_code} {balance:.2f}",
                }

                return TextResponse(data=json.dumps(result, ensure_ascii=False))

            elif response.status_code == 404:
                return TextResponse(
                    data=json.dumps(
                        {
                            "status": "error",
                            "message": f"Giftcard com ID '{giftcard_id}' não encontrado",
                        },
                        ensure_ascii=False,
                    )
                )

            else:
                error_msg = f"Erro ao consultar giftcard: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {json.dumps(error_detail, ensure_ascii=False)}"
                except Exception:
                    error_msg += f" - {response.text}"

                return TextResponse(
                    data=json.dumps(
                        {"status": "error", "message": error_msg}, ensure_ascii=False
                    )
                )

        except requests.exceptions.Timeout:
            return TextResponse(
                data=json.dumps(
                    {
                        "status": "error",
                        "message": "Timeout ao consultar giftcard. Tente novamente.",
                    },
                    ensure_ascii=False,
                )
            )

        except requests.exceptions.RequestException as e:
            return TextResponse(
                data=json.dumps(
                    {"status": "error", "message": f"Erro na requisição: {str(e)}"},
                    ensure_ascii=False,
                )
            )

        except Exception as e:
            return TextResponse(
                data=json.dumps(
                    {"status": "error", "message": f"Erro inesperado: {str(e)}"},
                    ensure_ascii=False,
                )
            )
