from sele_saisie_auto import plugins


def test_hooks_called_in_registration_order():
    plugins.clear()
    calls: list[str] = []

    def first():
        calls.append("first")

    def second():
        calls.append("second")

    plugins.register("before_submit", first)
    plugins.register("before_submit", second)
    plugins.call("before_submit")

    assert calls == ["first", "second"]


def test_clear_removes_all_hooks():
    plugins.clear()
    called: list[str] = []

    def cb():
        called.append("cb")

    plugins.register("after_run", cb)
    plugins.call("after_run")
    assert called == ["cb"]

    plugins.clear()
    called.clear()

    plugins.call("after_run")
    assert called == []

    plugins.register("after_run", cb)
    plugins.call("after_run")
    assert called == ["cb"]
