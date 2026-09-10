import json

from palmcue.settings import Settings, load_settings, save_settings


def test_round_trip(tmp_path):
    path = tmp_path / "nested" / "settings.json"
    settings = Settings(mode="showcase", click=True)
    save_settings(path, settings)
    assert load_settings(path) == (settings, "")
    assert list(path.parent.iterdir()) == [path]


def test_missing_and_corrupt(tmp_path):
    path = tmp_path / "settings.json"
    assert load_settings(path) == (Settings(), "")
    path.write_text("{bad", encoding="utf-8")
    settings, warning = load_settings(path)
    assert settings == Settings()
    assert warning
    assert path.read_text() == "{bad"


def test_untrusted_values():
    settings = Settings.from_dict(
        json.loads(
            '{"hold_seconds": NaN, "camera": true, "click": "yes", '
            '"mode": "broken", "area": "anywhere", "extra": 1}'
        )
    )
    assert settings == Settings()
    assert Settings.from_dict({"hold_seconds": 0}).hold_seconds == 0.6


def test_debug_preview_is_opt_in():
    assert not Settings().debug_preview
    assert Settings.from_dict({"debug_preview": True}).debug_preview
