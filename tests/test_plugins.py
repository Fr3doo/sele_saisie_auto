from sele_saisie_auto import plugins


def test_register_and_call():
    plugins.clear()
    calls = []
    plugins.register("before_submit", lambda d: calls.append(d))
    plugins.call("before_submit", "drv")
    assert calls == ["drv"]


def test_hook_decorator_registers():
    plugins.clear()
    called: list[int] = []

    @plugins.hook("after_run")
    def cb(data: int) -> None:
        called.append(data)

    plugins.call("after_run", 123)
    assert called == [123]


def test_call_returns_list_of_results():
    plugins.clear()

    @plugins.hook("after_run")
    def plus_one(x: int) -> int:
        return x + 1

    @plugins.hook("after_run")
    def times_two(x: int) -> int:
        return x * 2

    results = plugins.call("after_run", 3)
    assert results == [4, 6]


def test_unregister_removes_hook():
    plugins.clear()
    called: list[str] = []

    def cb() -> None:
        called.append("cb")

    plugins.register("after_run", cb)
    plugins.unregister("after_run", cb)
    plugins.call("after_run")
    assert called == []
