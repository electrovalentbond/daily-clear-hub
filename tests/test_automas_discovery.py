import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from core.auto_setup import resolve_automatic
from core.automas_backend import AutoMasProfile, discover_automas
from core.config_loader import GameConfig, HubConfig


def _profile(number, script_type, name, repository=None):
    return str(UUID(int=number)), script_type, name, repository


def _upstream(profiles, project_names=None):
    def reply(port, endpoint, payload=None, **kwargs):
        if endpoint == "/api/core/health":
            return {"ready": True, "protocol": 1}
        if endpoint == "/api/scripts/get" and payload == {}:
            return {
                "code": 200,
                "status": "success",
                "index": [{"uid": script_id, "type": script_type} for script_id, script_type, _, _ in profiles],
                "data": {script_id: {"Info": {"Name": name}} for script_id, _, name, _ in profiles},
            }
        if endpoint == "/api/scripts/maafw/preview":
            script_id = payload["scriptId"]
            repo = {uid: repo for uid, _, _, repo in profiles}[script_id]
            project = {"github": repo, "name": (project_names or {}).get(script_id)}
            return {"code": 200, "status": "success", "data": {"project": project}}
        raise AssertionError((endpoint, payload))

    return reply


class AutoMasDiscoveryTest(unittest.TestCase):
    def test_classifies_games_from_dedicated_types_and_effective_mfw_projects(self):
        targets = {
            "honkai3": _profile(1, "MaaFWConfig", "我的崩三", "https://github.com/miaojiuqing/Maa_bbb/"),
            "starrail": _profile(2, "HSRConfig", "列车"),
            "zzz": _profile(3, "ZzzOdConfig", "录像店"),
            "genshin": _profile(4, "BetterGIConfig", "提瓦特"),
            "bhxy2": _profile(5, "MaaFWConfig", "B 服账号", "https://github.com/freeze-12/MaaBH2"),
            "endfield": _profile(6, "MaaEndConfig", "工地"),
            "nikke": _profile(7, "MaaFWConfig", "前哨基地", "https://github.com/1204244136/MDA"),
            "gakumas": _profile(8, "MaaFWConfig", "学マス", "https://github.com/SuperWaterGod/MaaGakumasu"),
        }
        with patch("core.automas_backend._request", side_effect=_upstream(tuple(targets.values()))):
            results = discover_automas(36163, tuple(targets))

        self.assertEqual(results.keys(), targets.keys())
        for game_id, (script_id, _, name, _) in targets.items():
            with self.subTest(game=game_id):
                self.assertEqual(1, len(results[game_id]))
                self.assertEqual(script_id, results[game_id][0].script_id)
                self.assertEqual(name, results[game_id][0].name)

    def test_local_adapter_matches_interface_name_without_a_repository(self):
        profiles = (
            _profile(1, "MaaFWConfig", "DMM 日常"),
            _profile(2, "MaaFWConfig", "同名线上项目", "https://github.com/example/dotabyss"),
            _profile(3, "MaaFWConfig", "DailyClearDotAbyss"),
        )
        project_names = {profiles[0][0]: "DailyClearDotAbyss", profiles[1][0]: "DailyClearDotAbyss"}
        with patch("core.automas_backend._request", side_effect=_upstream(profiles, project_names)):
            result = discover_automas(36163, ("dotabyss",))
        self.assertEqual((AutoMasProfile(profiles[0][0], profiles[0][2]),), result["dotabyss"])

    def test_uu_variants_resolve_to_the_same_game_ids_as_the_standard_profiles(self):
        profiles = tuple(_profile(i, "MaaFWConfig", game) for i, game in enumerate(
            ("nikke", "gakumas", "dotabyss"), start=1,
        ))
        project_names = dict(zip(
            (row[0] for row in profiles),
            ("DailyClearHubUuNikke", "DailyClearHubUuGakumas", "DailyClearHubUuDotAbyss"),
        ))
        with patch("core.automas_backend._request", side_effect=_upstream(profiles, project_names)):
            result = discover_automas(36163, ("nikke", "gakumas", "dotabyss"))
        for script_id, _, game, _ in profiles:
            self.assertEqual((AutoMasProfile(script_id, game),), result[game])

    def test_mfw_fork_with_spoofed_name_does_not_match(self):
        profiles = (
            _profile(1, "MaaFWConfig", "MaaBH2", "https://github.com/freeze-12/MaaBH2-fork"),
            _profile(2, "GeneralConfig", "MaaBH2"),
        )
        with patch("core.automas_backend._request", side_effect=_upstream(profiles)):
            result = discover_automas(36163, ("bhxy2",))

        self.assertEqual({"bhxy2": ()}, result)

    def test_returns_each_profile_for_an_ambiguous_game(self):
        profiles = (
            _profile(1, "MaaEndConfig", "终末地专项"),
            _profile(2, "MaaFWConfig", "终末地 MFW", "https://github.com/MaaEnd/MaaEnd"),
        )
        with patch("core.automas_backend._request", side_effect=_upstream(profiles)):
            result = discover_automas(36163, ("endfield",))

        self.assertEqual({row[0] for row in profiles}, {profile.script_id for profile in result["endfield"]})

    def test_only_requested_games_and_no_mfw_preview_for_dedicated_selection(self):
        profiles = (
            _profile(1, "BetterGIConfig", "原神"),
            _profile(2, "MaaFWConfig", "终末地 MFW", "https://github.com/MaaEnd/MaaEnd"),
        )
        with patch("core.automas_backend._request", side_effect=_upstream(profiles)) as request:
            result = discover_automas(36163, ("genshin", "zzz"))

        self.assertEqual({"genshin", "zzz"}, result.keys())
        self.assertEqual(profiles[0][0], result["genshin"][0].script_id)
        self.assertEqual((), result["zzz"])
        self.assertEqual(
            ["/api/core/health", "/api/scripts/get"], [item.args[1] for item in request.call_args_list],
        )

    def test_resolver_preserves_queue_order_and_only_uses_unique_profiles(self):
        catalog = {
            game_id: GameConfig(game_id, False, "native", 300, {})
            for game_id in ("starrail", "genshin", "endfield", "pcr")
        }
        requested = ("endfield", "pcr", "starrail", "genshin")
        profiles = {
            "starrail": (AutoMasProfile(str(UUID(int=1)), "列车"),),
            "genshin": (),
            "endfield": (AutoMasProfile(str(UUID(int=2)), "工地"),),
        }
        with (
            patch("core.auto_setup.discover_automas", return_value=profiles) as discover,
            patch("core.auto_setup.discover_pcr", return_value=None) as pcr,
        ):
            result = resolve_automatic(HubConfig(catalog, requested), requested, 40000, Path("tools"))
        discover.assert_called_once_with(40000, ("endfield", "starrail", "genshin"))
        pcr.assert_called_once_with(catalog["pcr"], Path("tools"))
        self.assertEqual(("endfield", "starrail"), result.order)
        self.assertEqual("automas", result.games["starrail"].backend)
        self.assertEqual(3600, result.games["starrail"].timeout)
        self.assertEqual(40000, result.games["starrail"].options["automas_port"])

    def test_explicit_binding_preserves_user_and_resolves_duplicate(self):
        pinned = str(UUID(int=1))
        options = {"script_id": pinned, "user_id": str(UUID(int=3))}
        game = GameConfig("星铁", True, "automas", 900, options)
        hub = HubConfig({"starrail": game}, ("starrail",))
        first = AutoMasProfile(pinned, "主号")
        second = AutoMasProfile(str(UUID(int=2)), "副号")
        with patch("core.auto_setup.discover_automas", return_value={"starrail": (second, first)}):
            result = resolve_automatic(hub, hub.order, 36163, Path("tools"))
        self.assertEqual(options["user_id"], result.games["starrail"].options["user_id"])
        self.assertEqual("主号", result.games["starrail"].options["script_name"])
        self.assertEqual(900, result.games["starrail"].timeout)
        with patch("core.auto_setup.discover_automas", return_value={"starrail": (second,)}):
            with self.assertRaisesRegex(ValueError, "未匹配"):
                resolve_automatic(hub, hub.order, 36163, Path("tools"))
        no_pin = HubConfig({"starrail": GameConfig("星铁", False, "native", 300, {})}, hub.order)
        with patch("core.auto_setup.discover_automas", return_value={"starrail": (second, first)}):
            with self.assertRaisesRegex(ValueError, "有多个托管"):
                resolve_automatic(no_pin, hub.order, 36163, Path("tools"))
