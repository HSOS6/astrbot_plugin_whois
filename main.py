import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star, register

API_URL = "https://api.whoiscx.com/whois/?domain={}"


@register(
    "astrbot_plugin_whois",
    "5060ti个马力的6999",
    "域名 WHOIS 查询",
    "v1.0.0",
)
class WhoisPlugin(Star):

    @filter.command("whois", alias={"查域名"})
    async def whois(self, event: AstrMessageEvent, domain: str):
        yield event.plain_result(f"正在查询 {domain}，请稍候...")

        try:
            data = await self.fetch(domain)
        except Exception as e:
            yield event.plain_result(f"查询失败: {e}")
            return

        text = self.format_result(data)

        # 使用 AstrBot 内置文转图
        url = await self.text_to_image(text)
        yield event.image_result(url)

    async def fetch(self, domain: str) -> dict:
        url = API_URL.format(domain)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                result = await resp.json()

        if result.get("status") != 1:
            raise ValueError("接口返回失败")

        return result["data"]

    def format_result(self, d: dict) -> str:
        info = d.get("info", {})

        def v(x, default="未公开"):
            return x if x not in (None, "", []) else default

        def render_list(items):
            if not items:
                return "- 无"
            return "\n".join(f"- {i}" for i in items)

        text = f"""
## WHOIS 查询结果
### 基本信息
- 域名: {d.get('domain')}
- 域名后缀: {d.get('domain_suffix')}
- 查询时间: {d.get('query_time')}
- 状态码: {d.get('status', 1)} (成功)
- 是否可注册: {'是' if d.get('is_available') else '否'}
### 注册信息
- 注册人: {v(info.get('registrant_name'))}
- 注册邮箱: {v(info.get('registrant_email'))}
- 注册商: {v(info.get('registrar_name'))}
### 时间信息
- 创建时间: {v(info.get('creation_time'))}
- 到期时间: {v(info.get('expiration_time'))}
- 已注册天数: {v(info.get('creation_days'), '未知')} 天
- 剩余有效期: {v(info.get('valid_days'), '未知')} 天
- 是否过期: {'是' if info.get('is_expire') else '否'}
### 域名状态
{render_list(info.get("domain_status", []))}
### DNS 服务器
{render_list(info.get("name_server", []))}
### Whois 服务器
- {v(info.get("whois_server"))}
"""

        return text.strip()
