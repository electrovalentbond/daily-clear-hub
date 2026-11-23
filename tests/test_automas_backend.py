import io
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import call, patch

from core.automas_backend import _ApiUnavailable, _request, check_automas, run_automas
from core.config_loader import GameConfig
from core.errors import RunAborted

SCRIPT = "11111111-1111-4111-8111-111111111111"
TASK = "22222222-2222-4222-8222-222222222222"
USER = "33333333-3333-4333-8333-333333333333"
OTHER = "44444444-4444-4444-8444-444444444444"


def _game(options=None):
    return GameConfig("崩坏3", True, "automas", 120, {"script_id": SCRIPT, **(options or {})})


def _terminal(completed=1, incomplete=0, **changes):
    return {
        "code": 200,
        "status": "success",
        "taskId": TASK,
        "scriptId": SCRIPT,
        "userId": None,
        "mode": "AutoProxy",
        "queueId": None,
        "finishedAt": "2026-11-23 13:00:00",
        "detail": f"托管：\n\n    已完成账号数：{completed}；未完成账号数：{incomplete}\n\n    账号结果",
        **changes,
    }


def _start_replies():
    return [
        {"tasks": []},
        {"code": 200, "signal": "NoAction"},
        {"code": 200, "status": "success", "taskId": TASK},
    ]


class AutoMasBackendTest(unittest.TestCase):
    @patch("core.automas_backend._request")
    def test_mfw_verifies_effective_project_and_account(self, request):
        request.side_effect = [
            {"ready": True, "protocol": 1},
            {"code": 200, "status": "success", "index": [{"uid": SCRIPT, "type": "MaaFWConfig"}]},
            {"code": 200, "status": "success", "data": {"project": {"github": "https://github.com/miaojiuqing/MAA_bbb"}}},
            {"code": 200, "status": "success", "data": {USER: {"Info": {"Status": True, "RemainedDay": -1}}}},
        ]
        check_automas("honkai3", _game({"automas_port": 30000, "user_id": USER}))
        self.assertEqual(request.call_args_list, [
            call(30000, "/api/core/health"),
            call(30000, "/api/scripts/get", {"scriptId": SCRIPT}),
            call(30000, "/api/scripts/maafw/preview", {"scriptId": SCRIPT}),
            call(30000, "/api/scripts/user/get", {"scriptId": SCRIPT, "userId": USER}),
        ])

    @patch("core.automas_backend._request")
    def test_wrong_project_or_specialized_type_is_rejected(self, request):
        health = {"ready": True, "protocol": 1}
        index = {"code": 200, "status": "success", "index": [{"uid": SCRIPT, "type": "MaaFWConfig"}]}
        request.side_effect = [
            health, index,
            {"code": 200, "status": "success", "data": {"project": {"github": "https://github.com/MaaEnd/MaaEnd"}}},
        ]
        with self.assertRaisesRegex(ValueError, "未使用"):
            check_automas("honkai3", _game())
        request.side_effect = [health, index]
        with self.assertRaisesRegex(ValueError, "BetterGIConfig"):
            check_automas("genshin", _game())

    @patch("core.automas_backend._request")
    def test_dispatch_exact_user_waits_for_new_run_and_cleanup(self, request):
        request.side_effect = [
            *_start_replies(),
            _terminal(status="running", userId=USER, finishedAt=None),
            _terminal(userId=USER),
            {"tasks": [{"taskId": TASK}]},
            {"tasks": []},
        ]
        with patch("core.automas_backend.time.sleep"), redirect_stdout(io.StringIO()) as stdout:
            run_automas("honkai3", _game({"user_id": USER}))
        self.assertIn("确认完成 1 个账号", stdout.getvalue())
        self.assertEqual(
            request.call_args_list[2],
            call(36163, "/api/dispatch/start", {"taskId": SCRIPT, "mode": "AutoProxy", "userId": USER}),
        )
        self.assertEqual(
            [entry.args[1] for entry in request.call_args_list[3:]],
            [f"/api/dispatch/task/{TASK}"] * 2 + ["/api/dispatch/runtime-snapshot"] * 2,
        )

    @patch("core.automas_backend._request")
    def test_task_completion_alone_is_not_a_success(self, request):
        unmatched = (
            _terminal(completed=0),
            _terminal(incomplete=1),
            _terminal(detail="任务未加载"),
            _terminal(status="cancelled"),
        )
        for result in unmatched:
            with self.subTest(result=result), redirect_stdout(io.StringIO()):
                request.side_effect = [*_start_replies(), result, {"tasks": []}]
                with self.assertRaises(ValueError):
                    run_automas("endfield", _game())

    @patch("core.automas_backend._request")
    def test_busy_and_pending_power_never_dispatch(self, request):
        request.return_value = {"tasks": [{"taskId": OTHER}]}
        with self.assertRaisesRegex(RunAborted, "运行中的任务"):
            run_automas("honkai3", _game())
        request.assert_called_once()
        request.reset_mock()
        request.side_effect = [{"tasks": []}, {"code": 200, "signal": "Shutdown"}]
        with self.assertRaisesRegex(RunAborted, "电源操作"):
            run_automas("honkai3", _game())
        self.assertEqual(request.call_count, 2)

    @patch("core.automas_backend._request")
    def test_mismatched_task_identity_never_stops_other_script(self, request):
        request.side_effect = [*_start_replies(), _terminal(scriptId=OTHER), _terminal(scriptId=OTHER)]
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RunAborted, "未收到停止确认"):
            run_automas("honkai3", _game())
        self.assertNotIn("/api/dispatch/stop", [entry.args[1] for entry in request.call_args_list])

    @patch("core.automas_backend._request")
    def test_poll_transport_error_retries_read_without_resubmitting(self, request):
        request.side_effect = [
            *_start_replies(),
            _ApiUnavailable("暂不可用"),
            _terminal(),
            {"tasks": []},
        ]
        with patch("core.automas_backend.time.sleep"), redirect_stdout(io.StringIO()):
            run_automas("honkai3", _game())
        self.assertEqual(1, [entry.args[1] for entry in request.call_args_list].count("/api/dispatch/start"))

    @patch("core.automas_backend._request")
    def test_new_upstream_run_after_terminal_blocks_remaining_queue(self, request):
        request.side_effect = [
            *_start_replies(), _terminal(), {"tasks": [{"taskId": OTHER}]}, _terminal(),
        ]
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RunAborted, "启动了其他任务"):
            run_automas("honkai3", _game())
        self.assertNotIn("/api/dispatch/stop", [entry.args[1] for entry in request.call_args_list])

    @patch("core.automas_backend._wait_for_task", side_effect=ValueError("等待超时"))
    @patch("core.automas_backend._request")
    def test_uncertain_running_task_requests_own_stop_and_aborts_queue(self, request, _wait):
        request.side_effect = [
            *_start_replies(), _terminal(status="running", finishedAt=None),
            {"code": 200, "status": "success"},
        ]
        with redirect_stdout(io.StringIO()), self.assertRaisesRegex(RunAborted, "已请求停止"):
            run_automas("honkai3", _game())
        self.assertEqual(
            request.call_args,
            call(36163, "/api/dispatch/stop", {"taskId": TASK}, timeout=3),
        )

    def test_loopback_client_does_not_follow_redirect(self):
        class Redirect(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", "/different-endpoint")
                self.end_headers()

            def log_message(self, *_):
                pass

        with HTTPServer(("127.0.0.1", 0), Redirect) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaisesRegex(ValueError, "HTTP 302"):
                    _request(server.server_port, "/api/core/health")
            finally:
                server.shutdown()
                thread.join()
