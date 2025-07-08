# pragma: no cover
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

from sele_saisie_auto import console_ui, messages, plugins
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation import (
    AdditionalInfoPage,
    BrowserSession,
    DateEntryPage,
    LoginHandler,
)
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.error_handler import log_error
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.remplir_jours_feuille_de_temps import (
    TimeSheetHelper,
    context_from_app_config,
)
from sele_saisie_auto.selenium_utils import detecter_doublons_jours, wait_for_dom_after
from sele_saisie_auto.timeouts import DEFAULT_TIMEOUT
from sele_saisie_auto.utils.misc import program_break_time

# pragma: no cover

if TYPE_CHECKING:
    from sele_saisie_auto.saisie_automatiser_psatime import SaisieContext


class AutomationOrchestrator:
    """Coordinate all sub-services to fill and submit a PSA Time sheet.

    The orchestrator binds together the different automation helpers and
    exposes a single :meth:`run` entry point.  The global sequence executed is
    roughly as follows:

    1. Récupération des identifiants chiffrés depuis la mémoire partagée.
    2. Ouverture du navigateur Selenium et connexion au portail PSA Time.
    3. Sélection de la date cible, puis affichage de la grille de saisie.
    4. Remplissage des journées via :class:`TimeSheetHelper`.
    5. Saisie des informations supplémentaires et sauvegarde du brouillon.
    6. Vérification d’éventuels doublons puis exécution des hooks ``plugins``.
    7. Libération des ressources (mémoires partagées, navigateur, logs).

    All low level Selenium operations remain delegated to their respective
    services, keeping this class focused on the overall workflow.
    """

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        browser_session: BrowserSession,
        login_handler: LoginHandler,
        date_entry_page: DateEntryPage,
        additional_info_page: AdditionalInfoPage,
        context: SaisieContext,
        choix_user: bool = True,
        *,
        timesheet_helper_cls: type[TimeSheetHelper] = TimeSheetHelper,
    ) -> None:
        self.config = config
        self.logger = logger
        self.browser_session = browser_session
        self.login_handler = login_handler
        self.date_entry_page = date_entry_page
        self.additional_info_page = additional_info_page
        self.context = context
        self.choix_user = choix_user
        self.timesheet_helper_cls = timesheet_helper_cls

    def initialize_shared_memory(self):  # pragma: no cover - tested elsewhere
        """Retrieve credentials from shared memory."""
        credentials = self.context.encryption_service.retrieve_credentials()

        if (
            credentials.mem_login is None
            or credentials.mem_password is None
            or credentials.mem_key is None
        ):
            self.logger.error(
                "🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés"
            )
            sys.exit(1)

        return credentials

    # ------------------------------------------------------------------
    # DOM & iframe helpers
    # ------------------------------------------------------------------
    def wait_for_dom(self, driver) -> None:  # pragma: no cover - simple wrapper
        """Delegate DOM wait to :class:`BrowserSession`."""

        self.browser_session.wait_for_dom(driver)

    @wait_for_dom_after
    def switch_to_iframe_main_target_win0(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Switch to the ``main_target_win0`` iframe."""

        waiter = self.browser_session.waiter
        switched_to_iframe = None
        element_present = waiter.wait_for_element(
            driver,
            By.ID,
            Locators.MAIN_FRAME.value,
            timeout=DEFAULT_TIMEOUT,
        )
        if element_present:
            switched_to_iframe = self.browser_session.go_to_iframe(
                Locators.MAIN_FRAME.value
            )
        self.wait_for_dom(driver)
        if switched_to_iframe is None:
            raise NameError("main_target_win0 not found")
        return switched_to_iframe

    def _process_date_entry(self, driver) -> None:  # pragma: no cover - simple wrapper
        """Renseigne la date cible dans l'interface."""

        self.date_entry_page.process_date(driver, self.config.date_cible)

    def navigate_from_home_to_date_entry_page(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Navigate to the date entry page."""

        return self.date_entry_page.navigate_from_home_to_date_entry_page(driver)

    def submit_date_cible(self, driver):  # pragma: no cover - simple wrapper
        """Submit the selected date."""

        return self.date_entry_page.submit_date_cible(driver)

    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Open the additional information modal."""

        return self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    @wait_for_dom_after
    def submit_and_validate_additional_information(
        self, driver
    ):  # pragma: no cover - simple wrapper
        """Fill in and submit the additional information."""

        return self.additional_info_page.submit_and_validate_additional_information(
            driver
        )

    @wait_for_dom_after
    def save_draft_and_validate(self, driver):  # pragma: no cover - simple wrapper
        """Save the current timesheet as draft."""

        return self.additional_info_page.save_draft_and_validate(driver)

    def _fill_and_save_timesheet(self, driver) -> None:
        """Fill the timesheet grid and persist a draft.

        This helper method chains the different steps executed once the date
        selection page is displayed:

        1. Appel du bouton d'action pour ouvrir la grille de travail.
        2. Utilisation de :class:`TimeSheetHelper` pour renseigner chaque jour.
        3. Ouverture de la fenêtre d'informations supplémentaires puis
           validation des champs requis.
        4. Retour sur la page principale, détection des doublons de jours et,
           si tout est valide, sauvegarde du brouillon.
        """

        self.wait_for_dom(driver)
        self.switch_to_iframe_main_target_win0(driver)
        program_break_time(1, messages.WAIT_STABILISATION)
        self.logger.debug(messages.DOM_STABLE)
        self.date_entry_page._click_action_button(driver, self.choix_user)
        self.wait_for_dom(driver)
        helper = self.timesheet_helper_cls(
            context_from_app_config(self.config, self.logger.log_file),
            self.logger,
            waiter=self.browser_session.waiter,
        )
        helper.run(driver)
        self.navigate_from_work_schedule_to_additional_information_page(driver)
        self.submit_and_validate_additional_information(driver)
        self.browser_session.go_to_default_content()
        self.wait_for_dom(driver)
        if self.switch_to_iframe_main_target_win0(driver):
            detecter_doublons_jours(driver)
            plugins.call("before_submit", driver)
            if self.save_draft_and_validate(driver):
                self.additional_info_page._handle_save_alerts(driver)

    def run(  # pragma: no cover - integration tested via main automation
        self,
        *,
        headless: bool = False,
        no_sandbox: bool = False,
    ) -> None:
        """Execute the full automation workflow.

        The method orchestrates the entire PSA Time procedure:

        1. Chargement de la configuration et récupération des identifiants.
        2. Ouverture d'une session navigateur via :class:`BrowserSession`.
        3. Connexion à PSA Time à l'aide de :class:`LoginHandler`.
        4. Navigation vers la page de sélection de date et remplissage de la
           feuille de temps.
        5. Appel des vérifications finales puis sauvegarde du brouillon.
        6. En toute circonstance, fermeture du navigateur et nettoyage de la
           mémoire partagée.
        """

        if self.config is None:
            self.config = ConfigManager().load()

        credentials = self.initialize_shared_memory()

        with self.browser_session as session:
            driver = session.open(
                self.config.url,
                headless=headless,
                no_sandbox=no_sandbox,
            )
            try:
                self.login_handler.connect_to_psatime(
                    driver,
                    credentials.aes_key,
                    credentials.login,
                    credentials.password,
                )
                if self.navigate_from_home_to_date_entry_page(driver):
                    self._process_date_entry(driver)
                    self._fill_and_save_timesheet(driver)
                self.wait_for_dom(driver)
                self.switch_to_iframe_main_target_win0(driver)
                self.wait_for_dom(driver)
            except NoSuchElementException as e:  # pragma: no cover - UI issue
                log_error(
                    f"❌ L'élément n'a pas été trouvé : {str(e)}", self.logger.log_file
                )
            except TimeoutException as e:  # pragma: no cover - UI slow
                log_error(
                    f"❌ Temps d'attente dépassé pour un élément : {str(e)}",
                    self.logger.log_file,
                )
            except WebDriverException as e:  # pragma: no cover - driver error
                log_error(
                    f"❌ Erreur liée au {messages.WEBDRIVER} : {str(e)}",
                    self.logger.log_file,
                )
            except Exception as e:  # pragma: no cover - unexpected
                log_error(
                    f"❌ {messages.ERREUR_INATTENDUE} : {str(e)}",
                    self.logger.log_file,
                )
            finally:
                try:
                    if session.driver is not None:
                        console_ui.ask_continue(  # pragma: no cover - manual step
                            "INFO : Controler et soumettez votre PSATime, Puis appuyer sur ENTRER "
                        )
                    else:
                        console_ui.ask_continue(  # pragma: no cover - manual step
                            "ERROR : Controler les Log, Puis appuyer sur ENTRER ET relancer l'outil "
                        )
                    console_ui.show_separator()  # pragma: no cover - manual step
                except ValueError:
                    pass
                finally:
                    self.cleanup_resources(
                        credentials.mem_key,
                        credentials.mem_login,
                        credentials.mem_password,
                    )

    def cleanup_resources(
        self,
        memoire_cle,
        memoire_nom,
        memoire_mdp,
    ) -> None:
        """Ferme le navigateur et libère les mémoires partagées."""
        if memoire_cle:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_cle
            )
        if memoire_nom:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_nom
            )
        if memoire_mdp:
            self.context.shared_memory_service.supprimer_memoire_partagee_securisee(
                memoire_mdp
            )
        self.browser_session.close()
        self.logger.info(
            "🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier automation_orchestrator."
        )
