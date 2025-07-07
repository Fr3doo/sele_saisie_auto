import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto import gui_builder  # noqa: E402

pytestmark = pytest.mark.slow

sep_instance = None


class DummyWidget:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pack_kwargs = None
        self.grid_kwargs = None

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs


class FakeNotebook:
    def __init__(self):
        self.add_calls = []

    def add(self, frame, text):
        self.add_calls.append((frame, text))


def setup_module(module):
    # Patch ttk and tk widget constructors with DummyWidget
    module._patches = []
    module.sep_instance = None

    def new_separator(*args, **kwargs):
        module.sep_instance = DummyWidget(*args, **kwargs)
        return module.sep_instance

    for mod, name in [
        (gui_builder.ttk, "Frame"),
        (gui_builder.ttk, "LabelFrame"),
        (gui_builder.ttk, "Label"),
        (gui_builder.ttk, "Entry"),
        (gui_builder.ttk, "Checkbutton"),
        (gui_builder.ttk, "Combobox"),
        (gui_builder.ttk, "Button"),
        (gui_builder.tk, "Button"),
    ]:
        original = getattr(mod, name)
        module._patches.append((mod, name, original))
        setattr(mod, name, DummyWidget)

    module._patches.append((gui_builder.ttk, "Separator", gui_builder.ttk.Separator))
    gui_builder.ttk.Separator = new_separator


def teardown_module(module):
    for mod, name, original in module._patches:
        setattr(mod, name, original)


def test_build_widgets():
    nb = FakeNotebook()
    tab = gui_builder.create_tab(nb, "Tab")
    assert isinstance(tab, DummyWidget)
    assert nb.add_calls == [(tab, "Tab")]

    frame = gui_builder.create_a_frame(tab)
    assert isinstance(frame, DummyWidget)
    assert frame.pack_kwargs["fill"] == "both"

    lframe = gui_builder.create_labeled_frame(frame, text="lbl")
    assert isinstance(lframe, DummyWidget)
    assert lframe.pack_kwargs["expand"] is True

    title = gui_builder.create_title_label_with_grid(frame, "t", 0, 0)
    assert isinstance(title, DummyWidget)
    assert title.grid_kwargs["row"] == 0

    lbl = gui_builder.create_modern_label_with_pack(frame, "hi")
    assert isinstance(lbl, DummyWidget)
    assert lbl.pack_kwargs == {"side": None, "padx": 0, "pady": 0, "sticky": None}

    entry = gui_builder.create_modern_entry_with_pack(frame, var="v")
    assert isinstance(entry, DummyWidget)
    assert entry.pack_kwargs["padx"] == 0

    chk = gui_builder.create_modern_checkbox_with_pack(frame, var="c")
    assert isinstance(chk, DummyWidget)
    assert chk.pack_kwargs["side"] is None

    label_g = gui_builder.create_modern_label_with_grid(frame, "g", 1, 1)
    assert isinstance(label_g, DummyWidget)
    assert label_g.grid_kwargs["column"] == 1

    entry_g = gui_builder.create_modern_entry_with_grid(frame, var="v", row=2, col=2)
    assert isinstance(entry_g, DummyWidget)
    assert entry_g.grid_kwargs["row"] == 2

    pwd = gui_builder.create_modern_entry_with_grid_for_password(
        frame, var="p", row=3, col=3
    )
    assert isinstance(pwd, DummyWidget)
    assert pwd.kwargs.get("show") == "*"

    combo_p = gui_builder.create_combobox_with_pack(frame, var="v", values=["a"])
    assert isinstance(combo_p, DummyWidget)
    assert combo_p.pack_kwargs["pady"] == 5

    combo = gui_builder.create_combobox(frame, var="v", values=["b"], row=4, col=4)
    assert isinstance(combo, DummyWidget)
    assert combo.grid_kwargs["row"] == 4

    btn_s = gui_builder.create_button_with_style(frame, "ok", command=lambda: None)
    assert isinstance(btn_s, DummyWidget)
    assert btn_s.pack_kwargs["ipady"] is None

    btn = gui_builder.create_button_without_style(frame, "go", command=lambda: None)
    assert isinstance(btn, DummyWidget)
    assert btn.pack_kwargs["fill"] == "x"

    gui_builder.seperator_ttk(frame)
    assert isinstance(sep_instance, DummyWidget)
    assert sep_instance.pack_kwargs["fill"] == "x"


def test_create_tab_invalid_object():
    """Ensure ``create_tab`` fails clearly with an invalid notebook."""
    with pytest.raises(AttributeError):
        gui_builder.create_tab(DummyWidget(), "Bad")
