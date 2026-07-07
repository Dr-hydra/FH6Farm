import unittest

from fh6auto_core.support import check_for_update, parse_version


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.data = data or {}

    def json(self):
        return dict(self.data)


class SupportTests(unittest.TestCase):
    def test_parse_version_handles_valid_and_invalid_versions(self):
        self.assertEqual((1, 2, 3), parse_version("1.2.3"))
        self.assertEqual((0, 0, 0), parse_version("bad"))

    def test_check_for_update_reports_current_version(self):
        result = check_for_update(
            "1.2.0",
            http_get=lambda _url, timeout: FakeResponse(data={"version": "1.2.0", "url": ""}),
        )

        self.assertEqual("当前已是最新版本 (v1.2.0)", result.message)
        self.assertEqual("gray", result.text_color)
        self.assertEqual("", result.url_to_open)

    def test_check_for_update_accepts_trusted_update_url(self):
        result = check_for_update(
            "1.2.0",
            http_get=lambda _url, timeout: FakeResponse(
                data={"version": "1.3.0", "url": "https://github.com/YOUSTHEONE/FH6Auto/releases"}
            ),
        )

        self.assertEqual("发现新版本 v1.3.0，已打开浏览器！", result.message)
        self.assertEqual("#2EA043", result.text_color)
        self.assertEqual("https://github.com/YOUSTHEONE/FH6Auto/releases", result.url_to_open)

    def test_check_for_update_blocks_untrusted_update_url(self):
        result = check_for_update(
            "1.2.0",
            http_get=lambda _url, timeout: FakeResponse(
                data={"version": "1.3.0", "url": "https://example.com/download"}
            ),
        )

        self.assertEqual("发现更新，但链接不可信，已拦截", result.message)
        self.assertEqual("#DA3633", result.text_color)
        self.assertEqual("", result.url_to_open)

    def test_check_for_update_reports_server_error(self):
        result = check_for_update(
            "1.2.0",
            http_get=lambda _url, timeout: FakeResponse(status_code=500),
        )

        self.assertEqual("检查更新失败 (服务器异常)", result.message)
        self.assertEqual("#DA3633", result.text_color)

    def test_check_for_update_reports_network_error(self):
        def raise_error(_url, timeout):
            raise TimeoutError("slow")

        result = check_for_update("1.2.0", http_get=raise_error)

        self.assertEqual("检查更新失败 (网络超时或无法访问)", result.message)
        self.assertEqual("#DA3633", result.text_color)


if __name__ == "__main__":
    unittest.main()
