from dataclasses import dataclass


UPDATE_CHECK_URL = "https://raw.githubusercontent.com/Dr-hydra/FH6Farm/refs/heads/main/version.json"
ALLOWED_UPDATE_URL_PREFIXES = (
    "https://github.com/YOUSTHEONE/",
    "https://ifdian.net/",
)


@dataclass(frozen=True)
class UpdateCheckResult:
    message: str
    text_color: str
    url_to_open: str = ""


def parse_version(version):
    try:
        return tuple(int(part) for part in str(version).split("."))
    except Exception:
        return (0, 0, 0)


def check_for_update(current_version, http_get=None, update_url=UPDATE_CHECK_URL):
    http_get = http_get or _default_http_get

    try:
        response = http_get(update_url, timeout=5)
        if response.status_code != 200:
            return UpdateCheckResult("检查更新失败 (服务器异常)", "#DA3633")

        data = response.json()
        remote_version = data.get("version", "0.0.0")
        remote_url = data.get("url", "")

        if parse_version(remote_version) <= parse_version(current_version):
            return UpdateCheckResult(f"当前已是最新版本 (v{current_version})", "gray")

        if remote_url.startswith(ALLOWED_UPDATE_URL_PREFIXES):
            return UpdateCheckResult(
                f"发现新版本 v{remote_version}，已打开浏览器！",
                "#2EA043",
                remote_url,
            )

        return UpdateCheckResult("发现更新，但链接不可信，已拦截", "#DA3633")
    except Exception:
        return UpdateCheckResult("检查更新失败 (网络超时或无法访问)", "#DA3633")


def _default_http_get(url, timeout):
    import requests

    return requests.get(url, timeout=timeout)
