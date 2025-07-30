from json import loads
from logging import getLogger

from re import search
from httpx import AsyncClient
from httpx._types import ProxyTypes

from ..errors import RPCError

log = getLogger(__name__)


class Connection:
    TIMEOUT = 20
    BASE_URL = "https://tapi.bale.ai"
    OTP_CLIENT_BASE_URL = "https://safir.bale.ai"
    SHORT_URL = "https://ble.ir"

    def __init__(
        self,
        token: str,
        otp_client_id: str = None,
        otp_client_secret: str = None,
        time_out: int = None,
        proxy: ProxyTypes = None,
        base_url: str = None,
        short_url: str = None,
    ):
        self.token = token
        self.otp_client_id = otp_client_id
        self.otp_client_secret = otp_client_secret
        self.client = None
        self.is_started = False
        self.time_out = time_out or self.TIMEOUT
        self.proxy = proxy
        self.base_url = base_url or self.BASE_URL
        self.short_url = short_url or self.SHORT_URL

    async def start(self):
        if self.is_started:
            raise ConnectionError("Connection is already started")
        self.is_started = True
        self.client = AsyncClient(proxy=self.proxy)

    async def stop(self):
        if not self.is_started:
            raise ConnectionError("Connection is already stopped")
        self.is_started = False
        await self.client.aclose()
        self.client = None

    def bot_url(self) -> str:
        return f"{self.base_url}/bot{self.token}"

    def file_url(self, file_id: str) -> str:
        return f"{self.base_url}/file/bot{self.token}/{file_id}"

    async def get_peer_info(self, query: str):
        response = await self.client.get(f"{self.short_url}/{query}")
        json_info = search(
            r"({.*})",
            search(
                r'(<script id="__NEXT_DATA__" type="application/json">.*</script>)',
                response.text,
            )[0],
        )[0]
        return loads(json_info)

    async def request(
        self,
        method: str,
        service: str,
        data: dict = None,
        json: dict = None,
        files: dict = None,
    ):
        if json:
            log.info(f"[{service}] JSON{json}")
        if data:
            log.info(f"[{service}] DATA{data} - FILES{files}")
        response = await self.client.request(
            method,
            f"{self.bot_url()}/{service}",
            data=data,
            files=files,
            json=json,
            timeout=self.time_out,
        )
        response_json = response.json()
        if response.status_code != 200:
            code = response.status_code or response_json.get("error_code")
            raise RPCError.create(
                code,
                response_json.get("description"),
                service,
                response_json.get("parameters"),
            )
        return response_json.get("result")

    async def download_file(self, file_id: str):
        response = await self.client.get(self.file_url(file_id))
        if response.status_code != 200:
            response_json = response.json()
            raise RPCError.create(
                response.status_code, response_json.get("description"), "downloadFile"
            )
        return response.read()

    async def get_otp_client_auth_token(self) -> str:
        response = await self.client.post(
            f"{self.OTP_CLIENT_BASE_URL}/api/v2/auth/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            params={
                "grant_type": "client_credentials",
                "client_secret": self.otp_client_secret,
                "scope": "read",
                "client_id": self.otp_client_id,
            },
        )
        status_code = response.status_code
        if status_code != 200:
            if status_code == 400:
                description = "Failed to Parse Request"
            elif status_code == 401:
                description = "Client authentication failed"
            elif status_code == 500:
                description = "Internal server error occurred"
            raise RPCError.create(status_code, description)
        return response.json()["access_token"]

    async def send_otp(self, phone: str, otp: int) -> int:
        if isinstance(otp, str) and otp.isnumeric():
            otp = int(otp)
        elif not isinstance(otp, int):
            raise TypeError("One time password must be integers")
        
        response = await self.client.post(
            f"{self.OTP_CLIENT_BASE_URL}/api/v2/send_otp",
            headers={
                "Authorization": f"Bearer {await self.get_otp_client_auth_token()}",
                "Content-Type": "application/json",
            },
            json={"phone": phone, "otp": otp},
        )
        response_json = response.json()
        if response.status_code != 200:
            raise RPCError.create(
                response.status_code, response_json["message"].capitalize()
            )
        return response_json["balance"]
