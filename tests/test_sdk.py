from patchbay_sdk import PluginResult

def test_success_result() -> None:
    result = PluginResult(status="success", data={"ok": True})
    assert result.status == "success"
    assert result.data["ok"] is True

def test_error_result_requires_message() -> None:
    try:
        PluginResult(status="error")
    except ValueError as exc:
        assert "error results" in str(exc)
    else:
        raise AssertionError("expected ValueError")
