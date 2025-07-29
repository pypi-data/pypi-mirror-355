"""BxUltra exchange subclass"""

import asyncio
from decimal import Decimal
import json
import logging
from typing import Type
import uuid

import httpx

import time
from pathlib import Path

from trd_utils.exchanges.bx_ultra.bx_utils import do_ultra_ss
from trd_utils.exchanges.bx_ultra.bx_types import (
    AssetsInfoResponse,
    ContractOrdersHistoryResponse,
    ContractsListResponse,
    CopyTraderFuturesStatsResponse,
    CopyTraderResumeResponse,
    CopyTraderTradePositionsResponse,
    HintListResponse,
    HomePageResponse,
    HotSearchResponse,
    QuotationRankResponse,
    SearchCopyTraderCondition,
    SearchCopyTradersResponse,
    UserFavoriteQuotationResponse,
    ZenDeskABStatusResponse,
    ZenDeskAuthResponse,
    ZoneModuleListResponse,
    BxApiResponse,
)
from trd_utils.cipher import AESCipher

from trd_utils.exchanges.exchange_base import ExchangeBase

PLATFORM_ID_ANDROID = "10"
PLATFORM_ID_WEB = "30"
PLATFORM_ID_TG = "100"

ANDROID_DEVICE_BRAND = "SM-N976N"
WEB_DEVICE_BRAND = "Windows 10_Chrome_127.0.0.0"
EDGE_DEVICE_BRAND = "Windows 10_Edge_131.0.0.0"

ANDROID_APP_VERSION = "4.28.3"
WEB_APP_VERSION = "4.78.12"
TG_APP_VERSION = "5.0.15"

ACCEPT_ENCODING_HEADER = "gzip, deflate, br, zstd"

logger = logging.getLogger(__name__)


class BXUltraClient(ExchangeBase):
    ###########################################################
    # region client parameters
    we_api_base_host: str = "\u0061pi-\u0061pp.w\u0065-\u0061pi.com"
    we_api_base_url: str = "https://\u0061pi-\u0061pp.w\u0065-\u0061pi.com/\u0061pi"
    original_base_host: str = "https://\u0062ing\u0078.co\u006d"
    qq_os_base_host: str = "https://\u0061pi-\u0061pp.\u0071\u0071-os.com"
    qq_os_base_url: str = "https://\u0061pi-\u0061pp.\u0071\u0071-os.com/\u0061pi"

    origin_header: str = "https://\u0062ing\u0078.co\u006d"
    app_id: str = "30004"
    main_app_id: str = "10009"
    trade_env: str = "real"
    timezone: str = "3"
    os_version: str = "7.1.2"
    device_brand: str = "SM-N976N"
    platform_lang: str = "en"
    sys_lang: str = "en"

    # endregion
    ###########################################################
    # region client constructor
    def __init__(
        self,
        account_name: str = "default",
        platform_id: str = PLATFORM_ID_ANDROID,
        device_brand: str = ANDROID_DEVICE_BRAND,
        app_version: str = ANDROID_APP_VERSION,
        http_verify: bool = True,
        fav_letter: str = "^",
        sessions_dir: str = "sessions",
    ):
        self.httpx_client = httpx.AsyncClient(
            verify=http_verify, http2=True, http1=False
        )
        self.account_name = account_name
        self.platform_id = platform_id
        self.device_brand = device_brand
        self.app_version = app_version
        self._fav_letter = fav_letter

        self.read_from_session_file(f"{sessions_dir}/{self.account_name}.bx")

    # endregion
    ###########################################################
    # region api/coin/v1
    async def get_zone_module_info(
        self,
        only_one_position: int = 0,
        biz_type: int = 10,
    ) -> ZoneModuleListResponse:
        """
        Fetches and returns zone module info from the API.
        Available zones are: All, Forex, Indices, MEME, Elon-inspired,
        Innovation, AI Agent, BTC Ecosystem, TON Ecosystem, Commodities,
        GameFi, Fan Tokens , Layer1 & Layer2, SOL Ecosystem, RWA, LST, DePin, AI
        """
        params = {
            "bizType": f"{biz_type}",
        }
        headers = self.get_headers(params)
        headers["Only_one_position"] = f"{only_one_position}"
        return await self.invoke_get(
            f"{self.we_api_base_url}/coin/v1/zone/module-info",
            headers=headers,
            params=params,
            model=ZoneModuleListResponse,
        )

    async def get_user_favorite_quotation(
        self,
        only_one_position: int = 0,
        biz_type: int = 1,
    ) -> UserFavoriteQuotationResponse:
        params = {
            "bizType": f"{biz_type}",
        }
        headers = self.get_headers(params)
        headers["Only_one_position"] = f"{only_one_position}"
        return await self.invoke_get(
            f"{self.we_api_base_url}/coin/v1/user/favorite/quotation",
            headers=headers,
            params=params,
            model=UserFavoriteQuotationResponse,
        )

    async def get_quotation_rank(
        self,
        only_one_position: int = 0,
        order_flag: int = 0,
    ) -> QuotationRankResponse:
        params = {
            "orderFlag": f"{order_flag}",
        }
        headers = self.get_headers(params)
        headers["Only_one_position"] = f"{only_one_position}"
        return await self.invoke_get(
            f"{self.we_api_base_url}/coin/v1/rank/quotation-rank",
            headers=headers,
            params=params,
            model=QuotationRankResponse,
        )

    async def get_hot_search(
        self,
        only_one_position: int = 0,
        biz_type: int = 30,
    ) -> HotSearchResponse:
        params = {
            "bizType": f"{biz_type}",
        }
        headers = self.get_headers(params)
        headers["Only_one_position"] = f"{only_one_position}"
        return await self.invoke_get(
            f"{self.we_api_base_url}/coin/v1/quotation/hot-search",
            headers=headers,
            params=params,
            model=HotSearchResponse,
        )

    async def get_homepage(
        self,
        only_one_position: int = 0,
        biz_type: int = 30,
    ) -> HomePageResponse:
        params = {
            "biz-type": f"{biz_type}",
        }
        headers = self.get_headers(params)
        headers["Only_one_position"] = f"{only_one_position}"
        return await self.invoke_get(
            f"{self.we_api_base_url}/coin/v1/discovery/homepage",
            headers=headers,
            params=params,
            model=HomePageResponse,
        )

    # endregion
    ###########################################################
    # region customer
    async def get_zendesk_ab_status(self) -> ZenDeskABStatusResponse:
        headers = self.get_headers()
        return await self.invoke_get(
            f"{self.we_api_base_url}/customer/v1/zendesk/ab-status",
            headers=headers,
            model=ZenDeskABStatusResponse,
        )
    async def do_zendesk_auth(self) -> ZenDeskAuthResponse:
        headers = self.get_headers(needs_auth=True)
        return await self.invoke_get(
            f"{self.we_api_base_url}/customer/v1/zendesk/auth/jwt",
            headers=headers,
            model=ZenDeskAuthResponse,
        )
    # endregion
    ###########################################################
    # region platform-tool
    async def get_hint_list(self) -> HintListResponse:
        headers = self.get_headers()
        return await self.invoke_get(
            f"{self.we_api_base_url}/platform-tool/v1/hint/list",
            headers=headers,
            model=HintListResponse,
        )

    # endregion
    ###########################################################
    # region asset-manager
    async def get_assets_info(self) -> AssetsInfoResponse:
        headers = self.get_headers(needs_auth=True)
        return await self.invoke_get(
            f"{self.we_api_base_url}/asset-manager/v1/assets/account-total-overview",
            headers=headers,
            model=AssetsInfoResponse,
        )

    # endregion
    ###########################################################
    # region contract
    async def get_contract_list(
        self,
        quotation_coin_id: int = -1,
        margin_type: int = -1,
        page_size: int = 20,
        page_id: int = 0,
        margin_coin_name: str = "",
        create_type: str = -1,
    ) -> ContractsListResponse:
        params = {
            "quotationCoinId": f"{quotation_coin_id}",
            "marginType": f"{margin_type}",
            "pageSize": f"{page_size}",
            "pageId": f"{page_id}",
            "createType": f"{create_type}",
        }
        if margin_coin_name:
            params["marginCoinName"] = margin_coin_name
        headers = self.get_headers(params, needs_auth=True)
        return await self.invoke_get(
            f"{self.we_api_base_url}/v4/contract/order/hold",
            headers=headers,
            params=params,
            model=ContractsListResponse,
        )

    async def get_contract_order_history(
        self,
        fund_type: int = 1,
        paging_size: int = 10,
        page_id: int = 0,
        from_order_no: int = 0,
        margin_coin_name: str = "USDT",
        margin_type: int = 0,
    ) -> ContractOrdersHistoryResponse:
        params = {
            "fundType": f"{fund_type}",
            "pagingSize": f"{paging_size}",
            "pageId": f"{page_id}",
            "marginCoinName": margin_coin_name,
            "marginType": f"{margin_type}",
        }
        if from_order_no:
            params["fromOrderNo"] = f"{from_order_no}"

        headers = self.get_headers(params, needs_auth=True)
        return await self.invoke_get(
            f"{self.we_api_base_url}/v2/contract/order/history",
            headers=headers,
            params=params,
            model=ContractOrdersHistoryResponse,
        )

    async def get_today_contract_earnings(
        self,
        margin_coin_name: str = "USDT",
        page_size: int = 10,
        max_total_size: int = 500,
        delay_per_fetch: float = 1.0,
    ) -> Decimal:
        """
        Fetches today's earnings from the contract orders.
        NOTE: This method is a bit slow due to the API rate limiting.
        NOTE: If the user has not opened ANY contract orders today,
            this method will return None.
        """
        return await self._get_period_contract_earnings(
            period="day",
            margin_coin_name=margin_coin_name,
            page_size=page_size,
            max_total_size=max_total_size,
            delay_per_fetch=delay_per_fetch,
        )

    async def get_this_week_contract_earnings(
        self,
        margin_coin_name: str = "USDT",
        page_size: int = 10,
        max_total_size: int = 500,
        delay_per_fetch: float = 1.0,
    ) -> Decimal:
        """
        Fetches this week's earnings from the contract orders.
        NOTE: This method is a bit slow due to the API rate limiting.
        NOTE: If the user has not opened ANY contract orders this week,
            this method will return None.
        """
        return await self._get_period_contract_earnings(
            period="week",
            margin_coin_name=margin_coin_name,
            page_size=page_size,
            max_total_size=max_total_size,
            delay_per_fetch=delay_per_fetch,
        )

    async def get_this_month_contract_earnings(
        self,
        margin_coin_name: str = "USDT",
        page_size: int = 10,
        max_total_size: int = 500,
        delay_per_fetch: float = 1.0,
    ) -> Decimal:
        """
        Fetches this month's earnings from the contract orders.
        NOTE: This method is a bit slow due to the API rate limiting.
        NOTE: If the user has not opened ANY contract orders this week,
            this method will return None.
        """
        return await self._get_period_contract_earnings(
            period="month",
            margin_coin_name=margin_coin_name,
            page_size=page_size,
            max_total_size=max_total_size,
            delay_per_fetch=delay_per_fetch,
        )

    async def _get_period_contract_earnings(
        self,
        period: str,
        margin_coin_name: str = "USDT",
        page_size: int = 10,
        max_total_size: int = 500,
        delay_per_fetch: float = 1.0,
    ) -> Decimal:
        total_fetched = 0
        total_earnings = Decimal("0.00")
        has_earned_any = False
        while total_fetched < max_total_size:
            current_page = total_fetched // page_size
            result = await self.get_contract_order_history(
                page_id=current_page,
                paging_size=page_size,
                margin_coin_name=margin_coin_name,
            )
            if period == "day":
                temp_earnings = result.get_today_earnings()
            elif period == "week":
                temp_earnings = result.get_this_week_earnings()
            elif period == "month":
                temp_earnings = result.get_this_month_earnings()
            if temp_earnings is None:
                # all ended
                break
            total_earnings += temp_earnings
            has_earned_any = True
            total_fetched += page_size
            if result.get_orders_len() < page_size:
                break
            await asyncio.sleep(delay_per_fetch)

        if not has_earned_any:
            return None
        return total_earnings

    # endregion
    ###########################################################
    # region copy-trade-facade
    async def get_copy_trade_trader_positions(
        self,
        uid: int | str,
        api_identity: str,
        page_size: int = 20,
        page_id: int = 0,
        copy_trade_label_type: int = 1,
    ) -> CopyTraderTradePositionsResponse:
        params = {
            "uid": f"{uid}",
            "apiIdentity": f"{api_identity}",
            "pageSize": f"{page_size}",
            "pageId": f"{page_id}",
            "copyTradeLabelType": f"{copy_trade_label_type}",
        }
        headers = self.get_headers(params)
        return await self.invoke_get(
            f"{self.we_api_base_url}/copy-trade-facade/v2/real/trader/positions",
            headers=headers,
            params=params,
            model=CopyTraderTradePositionsResponse,
        )

    async def search_copy_traders(
        self,
        exchange_id: int = 2,
        nick_name: str = "",
        conditions: list[SearchCopyTraderCondition] = None,
        page_id: int = 0,
        page_size: int = 20,
        sort: str = "comprehensive",
        order: str = "desc",
    ) -> SearchCopyTradersResponse:
        params = {
            "pageId": f"{page_id}",
            "pageSize": f"{page_size}",
            "sort": sort,
            "order": order,
        }
        if conditions is None:
            conditions = [
                {"key": "exchangeId", "selected": "2", "type": "singleSelect"}
            ]
        else:
            conditions = [x.to_dict() for x in conditions]

        payload = {
            "conditions": conditions,
            "exchangeId": f"{exchange_id}",
            "nickName": nick_name,
        }
        headers = self.get_headers(payload)
        return await self.invoke_post(
            f"{self.we_api_base_url}/v6/copy-trade/search/search",
            headers=headers,
            params=params,
            content=payload,
            model=SearchCopyTradersResponse,
        )

    async def get_copy_trader_futures_stats(
        self,
        uid: int | str,
        api_identity: str,
    ) -> CopyTraderFuturesStatsResponse:
        params = {
            "uid": f"{uid}",
            "apiIdentity": f"{api_identity}",
        }
        headers = self.get_headers(params)
        return await self.invoke_get(
            f"{self.we_api_base_url}/copy-trade-facade/v4/trader/account/futures/stat",
            headers=headers,
            params=params,
            model=CopyTraderFuturesStatsResponse,
        )

    async def get_copy_trader_resume(
        self,
        uid: int | str,
    ) -> CopyTraderResumeResponse:
        params = {
            "uid": f"{uid}",
        }
        headers = self.get_headers(params)
        return await self.invoke_get(
            f"{self.we_api_base_url}/copy-trade-facade/v1/trader/resume",
            headers=headers,
            params=params,
            model=CopyTraderResumeResponse,
        )

    # endregion
    ###########################################################
    # region welfare
    async def do_daily_check_in(self):
        headers = self.get_headers(needs_auth=True)
        return await self.invoke_post(
            f"{self.original_base_host}/api/act-operation/v1/welfare/sign-in/do",
            headers=headers,
            content="",
            model=None,
        )

    # endregion
    ###########################################################
    # region client helper methods
    def get_headers(self, payload=None, needs_auth: bool = False) -> dict:
        the_timestamp = int(time.time() * 1000)
        the_headers = {
            "Host": self.we_api_base_host,
            "Content-Type": "application/json",
            "Mainappid": self.main_app_id,
            "Accept": "application/json",
            "Origin": self.origin_header,
            "Traceid": self.trace_id,
            "App_version": self.app_version,
            "Platformid": self.platform_id,
            "Device_id": self.device_id,
            "Device_brand": self.device_brand,
            "Channel": self.channel_header,
            "Appid": self.app_id,
            "Trade_env": self.trade_env,
            "Timezone": self.timezone,
            "Lang": self.platform_lang,
            "Syslang": self.sys_lang,
            "Sign": do_ultra_ss(
                e_param=None,
                se_param=None,
                le_param=None,
                timestamp=the_timestamp,
                trace_id=self.trace_id,
                device_id=self.device_id,
                platform_id=self.platform_id,
                app_version=self.app_version,
                payload_data=payload,
            ),
            "Timestamp": f"{the_timestamp}",
            "Accept-Encoding": ACCEPT_ENCODING_HEADER,
            "User-Agent": self.user_agent,
            "Connection": "close",
            "appsiteid": "0",
        }

        if self.x_requested_with:
            the_headers["X-Requested-With"] = self.x_requested_with

        if needs_auth:
            the_headers["Authorization"] = f"Bearer {self.authorization_token}"
        return the_headers

    async def invoke_get(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        model: Type[BxApiResponse] | None = None,
        parse_float=Decimal,
    ) -> "BxApiResponse":
        """
        Invokes the specific request to the specific url with the specific params and headers.
        """
        response = await self.httpx_client.get(
            url=url,
            headers=headers,
            params=params,
        )
        return model.deserialize(response.json(parse_float=parse_float))

    async def invoke_post(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        content: dict | str | bytes = "",
        model: Type[BxApiResponse] | None = None,
        parse_float=Decimal,
    ) -> "BxApiResponse":
        """
        Invokes the specific request to the specific url with the specific params and headers.
        """

        if isinstance(content, dict):
            content = json.dumps(content, separators=(",", ":"), sort_keys=True)

        response = await self.httpx_client.post(
            url=url,
            headers=headers,
            params=params,
            content=content,
        )
        if not model:
            return response.json()

        return model.deserialize(response.json(parse_float=parse_float))

    async def aclose(self) -> None:
        await self.httpx_client.aclose()
        logger.info("BXUltraClient closed")
        return True

    def read_from_session_file(self, file_path: str) -> None:
        """
        Reads from session file; if it doesn't exist, creates it.
        """
        # check if path exists
        target_path = Path(file_path)
        if not target_path.exists():
            return self._save_session_file(file_path=file_path)

        aes = AESCipher(key=f"bx_{self.account_name}_bx", fav_letter=self._fav_letter)
        content = aes.decrypt(target_path.read_text()).decode("utf-8")
        json_data: dict = json.loads(content)

        self.device_id = json_data.get("device_id", self.device_id)
        self.trace_id = json_data.get("trace_id", self.trace_id)
        self.app_version = json_data.get("app_version", self.app_version)
        self.platform_id = json_data.get("platform_id", self.platform_id)
        self.install_channel = json_data.get("install_channel", self.install_channel)
        self.channel_header = json_data.get("channel_header", self.channel_header)
        self.authorization_token = json_data.get(
            "authorization_token", self.authorization_token
        )
        self.app_id = json_data.get("app_id", self.app_id)
        self.trade_env = json_data.get("trade_env", self.trade_env)
        self.timezone = json_data.get("timezone", self.timezone)
        self.os_version = json_data.get("os_version", self.os_version)
        self.device_brand = json_data.get("device_brand", self.device_brand)
        self.platform_lang = json_data.get("platform_lang", self.platform_lang)
        self.sys_lang = json_data.get("sys_lang", self.sys_lang)
        self.user_agent = json_data.get("user_agent", self.user_agent)

    def _save_session_file(self, file_path: str) -> None:
        """
        Saves current information to the session file.
        """
        if not self.device_id:
            self.device_id = uuid.uuid4().hex.replace("-", "") + "##"

        if not self.trace_id:
            self.trace_id = uuid.uuid4().hex.replace("-", "")

        json_data = {
            "device_id": self.device_id,
            "trace_id": self.trace_id,
            "app_version": self.app_version,
            "platform_id": self.platform_id,
            "install_channel": self.install_channel,
            "channel_header": self.channel_header,
            "authorization_token": self.authorization_token,
            "app_id": self.app_id,
            "trade_env": self.trade_env,
            "timezone": self.timezone,
            "os_version": self.os_version,
            "device_brand": self.device_brand,
            "platform_lang": self.platform_lang,
            "sys_lang": self.sys_lang,
            "user_agent": self.user_agent,
        }
        aes = AESCipher(key=f"bx_{self.account_name}_bx", fav_letter=self._fav_letter)
        target_path = Path(file_path)
        target_path.write_text(aes.encrypt(json.dumps(json_data)))

    # endregion
    ###########################################################
