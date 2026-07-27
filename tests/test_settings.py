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
    ):
        fn()
        print("ok", fn.__name__)
    print("all passed")
