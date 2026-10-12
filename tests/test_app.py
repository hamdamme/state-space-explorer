from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppTests(unittest.TestCase):
    def test_search_playback_and_comparison(self):
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 3)
        self.assertEqual(app.slider[0].value, 0)
        app.button[3].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.slider[0].value, 1)
        app.button[5].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.slider[0].value, app.slider[0].max)
        self.assertEqual(len(app.session_state["search"]["results"]), 3)

    def test_playback_position_survives_reruns(self):
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.button[0].click().run()
        app.button[1].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.session_state["playing"])
        previous = app.session_state["position"]
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(app.session_state["position"], previous)
        app.button[1].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertFalse(app.session_state["playing"])

    def test_invalid_input_is_reported(self):
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.text_input[2].set_value("invalid").run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 1)
        self.assertIsNone(app.session_state["search"])

    def test_unreachable_scenario(self):
        app = AppTest.from_file(APP, default_timeout=15).run()
        app.selectbox[0].select("Unreachable goal").run()
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.warning), 1)
        self.assertIsNone(app.session_state["search"]["results"]["A*"].path)


if __name__ == "__main__":
    unittest.main()
