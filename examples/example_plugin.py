"""Example plugin demonstrating hook registration."""

from __future__ import annotations

from sele_saisie_auto import shared_utils
from sele_saisie_auto.logger_utils import write_log
from sele_saisie_auto.plugins import hook
from sele_saisie_auto.saisie_automatiser_psatime import _ORCHESTRATOR


@hook("before_submit")
def notify_before_submit(driver) -> None:
    """Simple hook printing a message before submission.

    After the refactoring introducing :class:`AutomationOrchestrator`, the
    current orchestrator instance is exposed via the module-level variable
    ``_ORCHESTRATOR``.  Plugins can inspect it to read the configuration or
    access shared services.
    """
    write_log(
        "Plugin before_submit called",
        shared_utils.get_log_file(),
        "DEBUG",
    )
    if _ORCHESTRATOR is not None:
        write_log(
            f"Automation target date: {_ORCHESTRATOR.config.date_cible}",
            shared_utils.get_log_file(),
            "DEBUG",
        )
