import unittest

from games.rewards import Key, Outcome, RewardFlow, RewardPage


MAIL = RewardPage("mail", "邮件", (("mail_button", "mail_page"),), "claim", "empty")
PASS = RewardPage("pass", "通行证", ((Key("f4"), "pass_page"),), "claim", "empty")
FLOW = RewardFlow("demo", "home", "back", "popup_close", (MAIL, PASS))


class RewardScreen:
    def __init__(self, rewards=1, *, stuck=False, contradictory=False, back_fails=False):
        self.screen = "home"
        self.rewards = rewards
        self.stuck = stuck
        self.contradictory = contradictory
        self.back_fails = back_fails
        self.actions = []

    def wait_for(self, names, *, anchor=None, timeout=5):
        visible = {
            "home": {"home", "mail_button"},
            "mail": {"mail_page"},
            "pass": {"pass_page"},
            "popup": {"popup_close"},
            "unknown": {"claim", "empty"},
        }[self.screen].copy()
        if self.screen in ("mail", "pass"):
            if not self.back_fails:
                visible.add("back")
            visible.add("claim" if self.rewards else "empty")
            if self.contradictory:
                visible.add("empty")
        if anchor and anchor not in visible:
            return set()
        return visible.intersection(names)

    def click_feature(self, feature):
        if not self.wait_for((feature,)):
            return False
        self.actions.append(feature)
        if feature == "mail_button":
            self.screen = "mail"
        elif feature == "back":
            self.screen = "home"
        elif feature == "claim" and not self.stuck:
            self.rewards -= 1
            self.screen = "popup"
        elif feature == "popup_close":
            self.screen = "mail"
        return True

    def press(self, key):
        self.actions.append(key)
        self.screen = "pass"


class TestRewardFlow(unittest.TestCase):
    def test_multiple_claims_require_feedback_and_return_home(self):
        ctx = RewardScreen(2)
        result = FLOW.run_page(ctx, MAIL)
        self.assertEqual(Outcome.CLAIMED, result.outcome)
        self.assertEqual(["mail_button", "claim", "popup_close", "claim", "popup_close", "back"], ctx.actions)
        self.assertEqual("home", ctx.screen)

    def test_no_reward_is_explicit_and_rerun_is_idempotent(self):
        ctx = RewardScreen()
        FLOW.run_page(ctx, MAIL)
        self.assertEqual(Outcome.EMPTY, FLOW.run_page(ctx, MAIL).outcome)
        self.assertEqual(1, ctx.actions.count("claim"))

    def test_key_navigation_requires_known_start(self):
        ctx = RewardScreen(0)
        ctx.screen = "unknown"
        self.assertEqual(Outcome.FAILED, FLOW.run_page(ctx, PASS).outcome)
        self.assertEqual([], ctx.actions)
        ctx.screen = "home"
        self.assertEqual(Outcome.EMPTY, FLOW.run_page(ctx, PASS).outcome)
        self.assertEqual(["f4", "back"], ctx.actions)
        self.assertNotIn("f4", FLOW.required_features((PASS,)))

    def test_stalled_click_is_not_repeated_or_counted_as_success(self):
        ctx = RewardScreen(stuck=True)
        self.assertEqual(Outcome.FAILED, FLOW.run_page(ctx, MAIL).outcome)
        self.assertEqual(1, ctx.actions.count("claim"))
        self.assertEqual("home", ctx.screen)

    def test_conflicting_indicators_fail_before_claim(self):
        ctx = RewardScreen(contradictory=True)
        self.assertEqual(Outcome.FAILED, FLOW.run_page(ctx, MAIL).outcome)
        self.assertNotIn("claim", ctx.actions)

    def test_return_failure_fails_the_step(self):
        ctx = RewardScreen(back_fails=True)
        self.assertEqual(Outcome.FAILED, FLOW.run_page(ctx, MAIL).outcome)
        self.assertIn("claim", ctx.actions)
