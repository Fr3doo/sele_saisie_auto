"""Exemple simple de plugin enregistrant un hook."""

from sele_saisie_auto import shared_utils
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.plugins import hook


@hook("before_submit")
def notify_before_submit(driver) -> None:
    """Affiche un message dans le journal avant la soumission."""
    write_log(
        "Plugin before_submit called",
        shared_utils.get_log_file(),
        "DEBUG",
    )
