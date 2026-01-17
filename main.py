import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

API_URL = "https://api.whoiscx.com/whois/?domain={}&raw=1"


@register(
    "astrbot_plugin_whois",
    "5060ti个马力的6999",
    "域名 WHOIS 查询插件",
    "v0.1.beta",
)
class WhoisPlugin(Star):

    @filter.command("whois", alias={"查域名"})
    async def whois(self, event: AstrMessageEvent, domain: str):
        yield event.plain_result(f"正在查询 `{domain}` 的 WHOIS")

        try:
            data = await self.fetch(domain)
        except Exception as e:
            yield event.plain_result(f"查询失败: {e}")
            return

        text = self.format_result(data)
        yield event.plain_result(text)

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

        def v(x, default="私密"):
            return x if x not in (None, "", []) else default

        lines = [
            "WHOIS 查询结果",
            "",
            f"状态码: {d.get('status', 1)} (成功)",
            f"是否可注册: {'是' if d.get('is_available') else '否'}",
            f"域名: {d.get('domain')}",
            f"域名后缀: {d.get('domain_suffix')}",
            f"查询时间: {d.get('query_time')}",
            "",
            f"注册人: {v(info.get('registrant_name'))}",
            f"注册邮箱: {v(info.get('registrant_email'))}",
            f"注册商: {v(info.get('registrar_name'))}",
            f"创建时间: {v(info.get('creation_time'))}",
            f"到期时间: {v(info.get('expiration_time'))}",
            f"已注册天数: {v(info.get('creation_days'), '未知')} 天",
            f"剩余有效期: {v(info.get('valid_days'), '未知')} 天",
            f"是否过期: {'是' if info.get('is_expire') else '否'}",
            "",
        ]

        # 域名状态
        status_list = info.get("domain_status", [])
        if status_list:
            lines.append("域名状态:")
            for s in status_list:
                lines.append(f"- {s}")
            lines.append("")

        # DNS
        ns_list = info.get("name_server", [])
        if ns_list:
            lines.append("DNS 服务器:")
            for n in ns_list:
                lines.append(f"- {n}")
            lines.append("")

        # whois server
        lines.append("Whois 服务器:")
        lines.append(v(info.get("whois_server")))
        lines.append("")


        return "\n".join(lines)