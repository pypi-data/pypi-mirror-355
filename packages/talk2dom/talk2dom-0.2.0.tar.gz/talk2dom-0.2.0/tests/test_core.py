from talk2dom.core import Selector


def test_selector_model():
    s = Selector(selector_type="xpath", selector_value="/html/body/div")
    assert s.selector_type == "xpath"
    assert s.selector_value.startswith("/")


def test_call_llm_with_fake_html(monkeypatch):
    def fake_llm(*args, **kwargs):
        return Selector(selector_type="xpath", selector_value="//button")

    from talk2dom import core

    monkeypatch.setattr(core, "call_llm", fake_llm)
    result = core.call_llm(
        "Click the button",
        "<html><body><button>Click me</button></body></html>",
        "gpt-4o",
        "openai",
    )
    assert result.selector_type == "xpath"
