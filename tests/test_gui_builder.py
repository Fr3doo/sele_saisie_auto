import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402
from sele_saisie_auto import gui_builder  # noqa: E402

pytestmark = pytest.mark.slow


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


@pytest.fixture(autouse=True)
def patch_widgets(monkeypatch):
    """
    Remplace les widgets tk/ttk par DummyWidget et capture Separator.
    """
    holder = {}

    def new_separator(*args, **kwargs):
        holder["sep"] = DummyWidget(*args, **kwargs)
        return holder["sep"]

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
        monkeypatch.setattr(mod, name, DummyWidget)

    monkeypatch.setattr(gui_builder.ttk, "Separator", new_separator)
    return holder


# ─────────── tests ciblés : create_tab ───────────


def test_create_tab_returns_frame(patch_widgets):
    nb = FakeNotebook()
    tab = gui_builder.create_tab(nb, "Tab")
    assert isinstance(tab, DummyWidget)


def test_create_tab_adds_to_notebook(patch_widgets):
    nb = FakeNotebook()
    tab = gui_builder.create_tab(nb, "Tab")
    assert nb.add_calls == [(tab, "Tab")]


# ─────────── tests ciblés : helpers pack() ───────────


def test_create_a_frame_packs_fill_both(patch_widgets):
    parent = DummyWidget()
    frame = gui_builder.create_a_frame(parent)
    assert frame.pack_kwargs.get("fill") == "both"


def test_create_labeled_frame_expands(patch_widgets):
    parent = DummyWidget()
    lf = gui_builder.create_labeled_frame(parent, text="lbl")
    assert lf.pack_kwargs.get("expand") is True


def test_modern_label_with_pack_padx_zero(patch_widgets):
    parent = DummyWidget()
    lbl = gui_builder.create_modern_label_with_pack(parent, "hi")
    assert lbl.pack_kwargs.get("padx") == 0


def test_modern_entry_with_pack_padx_zero(patch_widgets):
    parent = DummyWidget()
    entry = gui_builder.create_modern_entry_with_pack(parent, var="v")
    assert entry.pack_kwargs.get("padx") == 0


def test_modern_checkbox_with_pack_side_none(patch_widgets):
    parent = DummyWidget()
    chk = gui_builder.create_modern_checkbox_with_pack(parent, var="c")
    assert chk.pack_kwargs.get("side") is None


def test_combobox_with_pack_pady_5(patch_widgets):
    parent = DummyWidget()
    combo = gui_builder.create_combobox_with_pack(parent, var="v", values=["a"])
    assert combo.pack_kwargs.get("pady") == 5


def test_button_with_style_ipady_none(patch_widgets):
    parent = DummyWidget()
    btn = gui_builder.create_button_with_style(parent, "ok", command=lambda: None)
    assert btn.pack_kwargs.get("ipady") is None


def test_button_without_style_fill_x(patch_widgets):
    parent = DummyWidget()
    btn = gui_builder.create_button_without_style(parent, "go", command=lambda: None)
    assert btn.pack_kwargs.get("fill") == "x"


# ─────────── tests ciblés : helpers grid() ───────────


def test_title_label_with_grid_row_is_0(patch_widgets):
    parent = DummyWidget()
    title = gui_builder.create_title_label_with_grid(parent, "t", 0, 0)
    assert title.grid_kwargs.get("row") == 0


def test_modern_label_with_grid_column_is_1(patch_widgets):
    parent = DummyWidget()
    lbl = gui_builder.create_modern_label_with_grid(parent, "g", 1, 1)
    assert lbl.grid_kwargs.get("column") == 1


def test_modern_entry_with_grid_row_is_2(patch_widgets):
    parent = DummyWidget()
    entry = gui_builder.create_modern_entry_with_grid(parent, var="v", row=2, col=2)
    assert entry.grid_kwargs.get("row") == 2


def test_combobox_with_grid_row_is_4(patch_widgets):
    parent = DummyWidget()
    combo = gui_builder.create_combobox(parent, var="v", values=["b"], row=4, col=4)
    assert combo.grid_kwargs.get("row") == 4


# ─────────── cas spécifiques ───────────


def test_password_entry_sets_show_asterisk(patch_widgets):
    parent = DummyWidget()
    pwd = gui_builder.create_modern_entry_with_grid_for_password(
        parent, var="p", row=3, col=3
    )
    assert pwd.kwargs.get("show") == "*"


def test_separator_ttk_sets_fill_x(patch_widgets):
    parent = DummyWidget()
    gui_builder.seperator_ttk(parent)
    assert patch_widgets["sep"].pack_kwargs.get("fill") == "x"


def test_create_tab_invalid_object():
    with pytest.raises(AttributeError):
        gui_builder.create_tab(DummyWidget(), "Bad")
