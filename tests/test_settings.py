"""Settings + cloud ASR + list_models unit checks."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jarvis import settings as settings_mod
from jarvis.settings import (
    ASR_MIMO,
    ASR_OPENAI_AUDIO,
    ASR_SENSEVOICE,
    LLM_PRESET_CUSTOM,
    LLM_PRESET_MIMO,
    PRESET_LABELS,
    Settings,
    invalidate_settings_cache,
    list_models,
    load_settings,
    openai_chat_url,
    preset_from_label,
    probe_connection,
    save_settings,
    uses_cloud_asr,
)
from jarvis.ear import transcribe_mimo, transcribe_openai_audio, transcribe_path


def _isolated_settings(tmp: Path):
    path = tmp / "settings.json"
    return mock.patch.multiple(
        settings_mod,
        SETTINGS_DIR=tmp,
        SETTINGS_PATH=path,
    )


def test_openai_chat_url():
    assert openai_chat_url("https://api.deepseek.com") == (
        "https://api.deepseek.com/v1/chat/completions"
    )
    assert openai_chat_url("https://api.xiaomimimo.com/v1") == (
        "https://api.xiaomimimo.com/v1/chat/completions"
    )


def test_save_load_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            s = Settings(
                asr_provider=ASR_OPENAI_AUDIO,
                asr_api_key="ak",
                asr_model="my-asr",
                llm_api_key="lk",
                llm_model="llama3",
                custom_models=["llama3", "qwen2.5"],
                wake_threshold=0.7,
            )
            save_settings(s)
            invalidate_settings_cache()
            loaded = load_settings(force=True)
            assert loaded.asr_provider == ASR_OPENAI_AUDIO
            assert loaded.asr_api_key == "ak"
            assert loaded.asr_model == "my-asr"
            assert loaded.llm_model == "llama3"
            assert loaded.custom_models == ["llama3", "qwen2.5"]
            assert uses_cloud_asr(loaded)


def test_legacy_mimo_migrates():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            path = tmp / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "asr_provider": "mimo",
                        "mimo_api_key": "old",
                        "mimo_base_url": "https://api.xiaomimimo.com/v1",
                    }
                ),
                encoding="utf-8",
            )
            loaded = load_settings(force=True)
            assert loaded.asr_provider == ASR_OPENAI_AUDIO
            assert loaded.asr_api_key == "old"
            assert ASR_MIMO not in (loaded.asr_provider,)


def test_list_models_openai():
    fake = {"data": [{"id": "deepseek-chat"}, {"id": "deepseek-reasoner"}]}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(fake).encode("utf-8")

    with mock.patch("jarvis.settings.urllib.request.urlopen", return_value=_Resp()):
        ids = list_models("https://api.deepseek.com", "k")
    assert "deepseek-chat" in ids


def test_list_models_ollama_fallback():
    calls = {"n": 0}

    class _Fail:
        def __enter__(self):
            raise urllib_error()

        def __exit__(self, *a):
            return False

    def urllib_error():
        import urllib.error

        raise urllib.error.URLError("nope")

    class _Tags:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"models": [{"name": "llama3:latest"}, {"name": "qwen2.5:7b"}]}
            ).encode("utf-8")

    def fake_urlopen(req, timeout=20):  # noqa: ARG001
        calls["n"] += 1
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "/api/tags" in url:
            return _Tags()
        import urllib.error

        raise urllib.error.URLError("no models")

    with mock.patch("jarvis.settings.urllib.request.urlopen", side_effect=fake_urlopen):
        ids = list_models("http://127.0.0.1:11434/v1", "ollama")
    assert "llama3:latest" in ids
    assert "qwen2.5:7b" in ids


def test_transcribe_openai_audio_uses_model():
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "t.wav"
        wav.write_bytes(b"RIFF....WAVEfmt ")
        fake = {"choices": [{"message": {"content": "開 Cursor"}}]}
        captured: dict = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps(fake).encode("utf-8")

        def capture(req, timeout=60):  # noqa: ARG001
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _Resp()

        with mock.patch("jarvis.ear.urllib.request.urlopen", side_effect=capture):
            text = transcribe_openai_audio(
                wav,
                api_key="k",
                base_url="https://api.xiaomimimo.com/v1",
                model="custom-asr",
            )
        assert text == "開 Cursor"
        assert captured["body"]["model"] == "custom-asr"
        assert captured["url"].endswith("/chat/completions")


def test_transcribe_path_routes_cloud():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        wav = tmp / "a.wav"
        wav.write_bytes(b"xx")
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            save_settings(
                Settings(asr_provider=ASR_OPENAI_AUDIO, asr_api_key="k", asr_model="m")
            )
            with mock.patch(
                "jarvis.ear.transcribe_openai_audio", return_value="關 Discord"
            ) as cloud:
                with mock.patch("jarvis.ear.transcribe_wav") as sv:
                    out = transcribe_path(wav)
            assert out == "關 Discord"
            cloud.assert_called_once()
            sv.assert_not_called()


def test_transcribe_path_sensevoice():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        wav = tmp / "a.wav"
        wav.write_bytes(b"xx")
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            save_settings(Settings(asr_provider=ASR_SENSEVOICE))
            with mock.patch("jarvis.ear.transcribe_wav", return_value="開 CS") as sv:
                with mock.patch("jarvis.ear.transcribe_openai_audio") as cloud:
                    out = transcribe_path(wav)
            assert out == "開 CS"
            sv.assert_called_once()
            cloud.assert_not_called()


def test_brain_reads_settings_key():
    from jarvis import brain

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        with _isolated_settings(tmp):
            invalidate_settings_cache()
            save_settings(Settings(llm_api_key="from-settings"))
            with mock.patch.object(brain, "_load_dotenv", lambda: None):
                with mock.patch.dict(
                    "os.environ",
                    {"JARVIS_LLM_API_KEY": "", "OPENAI_API_KEY": ""},
                    clear=False,
                ):
                    assert brain._api_key() == "from-settings"
                    assert brain.llm_configured() is True


def test_mimo_alias():
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "t.wav"
        wav.write_bytes(b"x")
        with mock.patch(
            "jarvis.ear.transcribe_openai_audio", return_value="hi"
        ) as fn:
            assert transcribe_mimo(wav, api_key="k") == "hi"
            fn.assert_called_once()


def test_preset_from_label():
    assert preset_from_label(PRESET_LABELS[LLM_PRESET_MIMO]) == LLM_PRESET_MIMO
    assert preset_from_label("mimo") == LLM_PRESET_MIMO
    assert preset_from_label("nope") == LLM_PRESET_CUSTOM


def test_probe_connection_ok():
    with mock.patch(
        "jarvis.settings.list_models", return_value=["a", "b", "c"]
    ):
        msg = probe_connection("http://x", "k")
        assert "連線 OK" in msg
        assert "a" in msg


def test_probe_connection_raises():
    with mock.patch(
        "jarvis.settings.list_models",
        side_effect=RuntimeError("boom"),
    ):
        try:
            probe_connection("http://x", "k")
        except RuntimeError as exc:
            assert "boom" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")


def test_normalize_hotkey_human_and_pynput():
    from jarvis.settings import hotkey_display, normalize_hotkey

    assert normalize_hotkey("Ctrl+Alt+J") == "<ctrl>+<alt>+j"
    assert normalize_hotkey("<ctrl>+<alt>+j") == "<ctrl>+<alt>+j"
    assert normalize_hotkey("ctrl-shift-j") == "<ctrl>+<shift>+j"
    assert hotkey_display("<ctrl>+<alt>+j") == "Ctrl+Alt+J"
    try:
        normalize_hotkey("Ctrl+Alt")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for mods-only")


def test_tts_settings_clamp_and_defaults():
    from jarvis.settings import ASR_FUN_ASR, _clamp

    s = _clamp(
        Settings(tts_enabled=True, tts_length_scale=0.1, tts_volume=99.0)
    )
    assert s.tts_length_scale == 0.50
    assert s.tts_volume == 3.0
    d = Settings()
    assert d.tts_enabled is True
    assert d.tts_length_scale == 0.85
    assert d.tts_volume == 1.6
    assert d.tts_output_device is None
    assert d.text_wake is False
    assert d.alert_voice is True
    assert d.alert_discord is True
    assert d.alert_cursor is True
    assert d.alert_cursor_hooks is True
    assert d.alert_cursor_toast is True
    assert d.alert_cursor_uia is True
    assert d.alert_cursor_watch is False
    assert d.alert_always is True
    assert d.alert_tts == "hermes"
    assert d.alerts_mcp_port == 8765
    assert d.voice_frontend == "hermes"
    a = _clamp(Settings(alert_cd_seconds=0.0))
    assert a.alert_cd_seconds == 0.0
    a2 = _clamp(Settings(alert_cd_seconds=0.1))
    assert a2.alert_cd_seconds == 0.1
    assert _clamp(Settings(alert_tts="piper")).alert_tts == "piper"
    # tts_output_device 支援存名（str = device 名，Windows index 會 reorder）；空 → None
    named = _clamp(Settings(tts_output_device="耳機 (2- Arctis Nova 7)"))
    assert named.tts_output_device == "耳機 (2- Arctis Nova 7)"
    assert _clamp(Settings(tts_output_device="  ")).tts_output_device is None
    f = _clamp(Settings(asr_provider="fun_asr"))
    assert f.asr_provider == ASR_FUN_ASR
    vf = _clamp(Settings(voice_frontend="JARVIS"))
    assert vf.voice_frontend == "jarvis"
    junk = _clamp(Settings(voice_frontend="nope"))
    assert junk.voice_frontend == "hermes"


def test_uses_hermes_voice_frontend():
    from jarvis.settings import (
        VOICE_FRONTEND_JARVIS,
        uses_hermes_voice_frontend,
    )

    assert uses_hermes_voice_frontend(Settings()) is True
    assert (
        uses_hermes_voice_frontend(
            Settings(voice_frontend=VOICE_FRONTEND_JARVIS)
        )
        is False
    )


if __name__ == "__main__":
    for fn in (
        test_openai_chat_url,
        test_save_load_roundtrip,
        test_legacy_mimo_migrates,
        test_list_models_openai,
        test_list_models_ollama_fallback,
        test_transcribe_openai_audio_uses_model,
        test_transcribe_path_routes_cloud,
        test_transcribe_path_sensevoice,
        test_brain_reads_settings_key,
        test_mimo_alias,
        test_preset_from_label,
        test_probe_connection_ok,
        test_probe_connection_raises,
        test_normalize_hotkey_human_and_pynput,
        test_tts_settings_clamp_and_defaults,
        test_uses_hermes_voice_frontend,
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
