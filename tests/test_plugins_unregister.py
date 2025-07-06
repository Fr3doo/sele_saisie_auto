from sele_saisie_auto import plugins


def test_unregister_removes_hook():
    plugins.clear()
    called: list[str] = []

    def cb():
        called.append("cb")

    plugins.register("after_run", cb)
    plugins.unregister("after_run", cb)
    plugins.call("after_run")
    assert called == []


def test_unregister_and_reregister():
    plugins.clear()
    called: list[str] = []

    def cb():
        called.append("cb")

    plugins.register("before_submit", cb)
    plugins.unregister("before_submit", cb)
    plugins.register("before_submit", cb)
    plugins.call("before_submit")
    assert called == ["cb"]


def test_unregister_nonexistent_hook():
    plugins.clear()
    called: list[str] = []

    def cb():
        called.append("cb")

    # unregister when hook name not present
    plugins.unregister("missing", cb)
    plugins.register("after_run", cb)

    # unregister function that is not registered under hook
    def other():
        called.append("other")

    plugins.unregister("after_run", other)
    plugins.call("after_run")
    assert called == ["cb"]
