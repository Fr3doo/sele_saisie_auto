# saisie_automatiser_psatime.py

# ----------------------------------------------------------------------------- #
# ---------------- Import des bibliothèques nécessaires ----------------------- #
# ----------------------------------------------------------------------------- #

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from multiprocessing import shared_memory

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

from sele_saisie_auto import (
    console_ui,
    messages,
    plugins,
    remplir_jours_feuille_de_temps,
)
from sele_saisie_auto.additional_info_locators import AdditionalInfoLocators
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.additional_info_page import AdditionalInfoPage
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.automation.date_entry_page import DateEntryPage
from sele_saisie_auto.automation.login_handler import LoginHandler
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.error_handler import log_error
from sele_saisie_auto.locators import Locators
from sele_saisie_auto.logger_utils import initialize_logger, write_log
from sele_saisie_auto.remplir_informations_supp_utils import (
    set_log_file as set_log_file_infos,
)
from sele_saisie_auto.selenium_utils import (
    click_element_without_wait,  # noqa: F401
    detecter_doublons_jours,
    modifier_date_input,  # noqa: F401
    send_keys_to_element,  # noqa: F401
    switch_to_default_content,
    switch_to_iframe_by_id_or_name,
    wait_for_dom_after,
    wait_for_element,
)
from sele_saisie_auto.selenium_utils import set_log_file as set_log_file_selenium
from sele_saisie_auto.shared_memory_service import SharedMemoryService
from sele_saisie_auto.shared_utils import program_break_time

# ----------------------------------------------------------------------------- #
# ------------------------------- CONSTANTE ----------------------------------- #
# ----------------------------------------------------------------------------- #


@dataclass
class SaisieContext:
    """Container for runtime configuration and services."""

    config: "AppConfig"
    encryption_service: EncryptionService
    shared_memory_service: SharedMemoryService
    informations_projet_mission: dict[str, str]
    descriptions: list[dict[str, object]]


@dataclass
class Credentials:
    """Encrypted credentials and their shared memory handles."""

    aes_key: bytes
    mem_key: shared_memory.SharedMemory
    login: bytes
    mem_login: shared_memory.SharedMemory
    password: bytes
    mem_password: shared_memory.SharedMemory


__all__ = [
    "PSATimeAutomation",
    "SaisieContext",
    "Credentials",
    "modifier_date_input",
    "send_keys_to_element",
    "click_element_without_wait",
]


# ----------------------------------------------------------------------------
#
# --------------------------- CLASSE PRINCIPALE ------------------------------
#
# ----------------------------------------------------------------------------


class PSATimeAutomation:
    """Automatise la saisie de la feuille de temps PSA Time."""

    def __init__(self, log_file: str, app_config: AppConfig) -> None:
        """Initialise la configuration et les dépendances."""

        self.log_file = log_file
        set_log_file_selenium(log_file)
        set_log_file_infos(log_file)
        initialize_logger(app_config.raw, log_level_override=app_config.debug_mode)
        shm_service = SharedMemoryService(log_file)
        self.context = SaisieContext(
            config=app_config,
            encryption_service=EncryptionService(log_file, shm_service),
            shared_memory_service=shm_service,
            informations_projet_mission={
                item_projet: {
                    opt.label.lower(): opt.code
                    for opt in app_config.cgi_options_billing_action
                }.get(value.lower(), value)
                for item_projet, value in app_config.project_information.items()
            },
            descriptions=[
                {
                    "description_cible": "Temps de repos de 11h entre 2 jours travaillés respecté",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "periode_repos_respectee"
                    ],
                },
                {
                    "description_cible": (
                        "Mon temps de travail effectif a débuté entre 8h00 et 10h00 et Mon temps de travail effectif a pris fin entre 16h30 et 19h00"
                    ),
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "horaire_travail_effectif"
                    ],
                },
                {
                    "description_cible": "J’ai travaillé plus d’une demi-journée",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR100.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.additional_information[
                        "plus_demi_journee_travaillee"
                    ],
                },
                {
                    "description_cible": "Durée de la pause déjeuner",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR200.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_DAILYREST_SPECIAL.value,
                    "type_element": "input",
                    "valeurs_a_remplir": app_config.additional_information[
                        "duree_pause_dejeuner"
                    ],
                },
                {
                    "description_cible": "Matin",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_LOCATION_A.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.work_location_am,
                },
                {
                    "description_cible": "Après-midi",
                    "id_value_ligne": AdditionalInfoLocators.ROW_DESCR.value,
                    "id_value_jours": AdditionalInfoLocators.DAY_UC_LOCATION_A.value,
                    "type_element": "select",
                    "valeurs_a_remplir": app_config.work_location_pm,
                },
            ],
        )
        self.browser_session = BrowserSession(log_file)
        self.login_handler = LoginHandler(
            log_file,
            self.context.encryption_service,
            self.browser_session,
        )
        self.date_entry_page = DateEntryPage(self)
        self.additional_info_page = AdditionalInfoPage(self)

        write_log("📌 Chargement des configurations...", self.log_file, "DEBUG")
        write_log(
            f"👉 Login : {self.context.config.encrypted_login} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )
        write_log(
            f"👉 Password : {self.context.config.encrypted_mdp} - pas visible, normal",
            self.log_file,
            "DEBUG",
        )
        write_log(f"👉 URL : {self.context.config.url}", self.log_file, "DEBUG")
        write_log(
            f"👉 Date cible : {self.context.config.date_cible}",
            self.log_file,
            "DEBUG",
        )

        write_log("👉 Planning de travail de la semaine:", self.log_file, "DEBUG")
        for day, (activity, hours) in self.context.config.work_schedule.items():
            write_log(
                f"🔹 '{day}': ('{activity}', '{hours}')",
                self.log_file,
                "DEBUG",
            )

        write_log("👉 Infos_supp_cgi_periode_repos_respectee:", self.log_file, "DEBUG")
        for day, status in self.context.config.additional_information[
            "periode_repos_respectee"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Infos_supp_cgi_horaire_travail_effectif:", self.log_file, "DEBUG")
        for day, status in self.context.config.additional_information[
            "horaire_travail_effectif"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Planning de travail de la semaine:", self.log_file, "DEBUG")
        for day, status in self.context.config.additional_information[
            "plus_demi_journee_travaillee"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Infos_supp_cgi_duree_pause_dejeuner:", self.log_file, "DEBUG")
        for day, status in self.context.config.additional_information[
            "duree_pause_dejeuner"
        ].items():
            write_log(f"🔹 '{day}': '{status}'", self.log_file, "DEBUG")

        write_log("👉 Lieu de travail Matin:", self.log_file, "DEBUG")
        for day, location in self.context.config.work_location_am.items():
            write_log(f"🔹 '{day}': '{location}'", self.log_file, "DEBUG")

        write_log("👉 Lieu de travail Apres-midi:", self.log_file, "DEBUG")
        for day, location in self.context.config.work_location_pm.items():
            write_log(f"🔹 '{day}': '{location}'", self.log_file, "DEBUG")

    def log_initialisation(self) -> None:
        """Initialise les logs et vérifie les configurations essentielles."""
        if not self.log_file:
            raise RuntimeError(f"Fichier de log {messages.INTROUVABLE}.")
        write_log(
            "📌 Démarrage de la fonction 'saisie_automatiser_psatime.run()'",
            self.log_file,
            "INFO",
        )
        write_log(
            f"🔍 Chemin du fichier log : {self.log_file}",
            self.log_file,
            "DEBUG",
        )

    def initialize_shared_memory(self):
        """Récupère les données de la mémoire partagée pour le login."""
        memoire_cle = memoire_nom = memoire_mdp = None

        memoire_cle, cle_aes = (
            self.context.shared_memory_service.recuperer_de_memoire_partagee(
                MEMOIRE_PARTAGEE_CLE, TAILLE_CLE
            )
        )
        write_log(f"💀 Clé AES récupérée : {cle_aes.hex()}", self.log_file, "CRITICAL")

        memoire_nom = shared_memory.SharedMemory(name="memoire_nom")
        taille_nom = len(bytes(memoire_nom.buf).rstrip(b"\x00"))
        nom_utilisateur_chiffre = bytes(memoire_nom.buf[:taille_nom])
        write_log(
            f"💀 Taille du login chiffré : {len(nom_utilisateur_chiffre)}",
            self.log_file,
            "CRITICAL",
        )

        memoire_mdp = shared_memory.SharedMemory(name="memoire_mdp")
        taille_mdp = len(bytes(memoire_mdp.buf).rstrip(b"\x00"))
        mot_de_passe_chiffre = bytes(memoire_mdp.buf[:taille_mdp])
        write_log(
            f"💀 Taille du mot de passe chiffré : {len(mot_de_passe_chiffre)}",
            self.log_file,
            "CRITICAL",
        )

        if not memoire_nom or not memoire_mdp or not memoire_cle:
            write_log(
                "🚨 La mémoire partagée n'a pas été initialisée correctement. Assurez-vous que les identifiants ont été chiffrés",
                self.log_file,
                "ERROR",
            )
            sys.exit(1)

        return Credentials(
            aes_key=cle_aes,
            mem_key=memoire_cle,
            login=nom_utilisateur_chiffre,
            mem_login=memoire_nom,
            password=mot_de_passe_chiffre,
            mem_password=memoire_mdp,
        )

    def wait_for_dom(self, driver):
        """Wait until the DOM is stable using :class:`BrowserSession`."""
        self.browser_session.wait_for_dom(driver)

    def setup_browser(self, session: BrowserSession | None = None):
        """Configure et démarre le navigateur via :class:`BrowserSession`."""
        return self.browser_session.open(
            self.context.config.url, fullscreen=False, headless=False
        )

    @wait_for_dom_after
    def switch_to_iframe_main_target_win0(self, driver):
        switched_to_iframe = None
        element_present = wait_for_element(
            driver, By.ID, Locators.MAIN_FRAME.value, timeout=DEFAULT_TIMEOUT
        )
        if element_present:
            switched_to_iframe = switch_to_iframe_by_id_or_name(
                driver, Locators.MAIN_FRAME.value
            )
        self.wait_for_dom(driver)
        if switched_to_iframe is None:
            raise NameError("main_target_win0 not found")
        return switched_to_iframe

    def navigate_from_home_to_date_entry_page(self, driver):
        """Delegate navigation to :class:`DateEntryPage`."""
        return self.date_entry_page.navigate_from_home_to_date_entry_page(driver)

    def submit_date_cible(self, driver):
        """Delegate submission to :class:`DateEntryPage`."""
        return self.date_entry_page.submit_date_cible(driver)

    @wait_for_dom_after
    def navigate_from_work_schedule_to_additional_information_page(self, driver):
        """Delegate to :class:`AdditionalInfoPage`."""
        return self.additional_info_page.navigate_from_work_schedule_to_additional_information_page(
            driver
        )

    @wait_for_dom_after
    def submit_and_validate_additional_information(self, driver):
        """Delegate to :class:`AdditionalInfoPage`."""
        return self.additional_info_page.submit_and_validate_additional_information(
            driver
        )

    @wait_for_dom_after
    def save_draft_and_validate(self, driver):
        """Delegate to :class:`AdditionalInfoPage`."""
        return self.additional_info_page.save_draft_and_validate(driver)

    def cleanup_resources(
        self,
        session,
        memoire_cle,
        memoire_nom,
        memoire_mdp,
    ) -> None:
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
        if session is not None:
            session.close()
        write_log(
            "🏁 [FIN] Clé et données supprimées de manière sécurisée, des mémoires partagées du fichier saisie_automatiser_psatime.",
            self.log_file,
            "INFO",
        )

    def _handle_date_alert(self, driver) -> None:
        self.date_entry_page._handle_date_alert(driver)

    def _click_action_button(self, driver) -> None:
        self.date_entry_page._click_action_button(driver, CHOIX_USER)

    def _process_date_entry(self, driver) -> None:
        self.date_entry_page.handle_date_input(driver, self.context.config.date_cible)
        program_break_time(
            1,
            "Veuillez patienter. Court délai pour stabilisation du DOM",
        )
        print()
        if self.submit_date_cible(driver):
            self._handle_date_alert(driver)

    def _fill_and_save_timesheet(self, driver) -> None:
        self.wait_for_dom(driver)
        self.switch_to_iframe_main_target_win0(driver)
        program_break_time(
            1,
            "Veuillez patienter. Court délai pour stabilisation du DOM",
        )
        print()
        self._click_action_button(driver)
        self.wait_for_dom(driver)
        remplir_jours_feuille_de_temps.main(driver, self.log_file)
        self.navigate_from_work_schedule_to_additional_information_page(driver)
        self.submit_and_validate_additional_information(driver)
        switch_to_default_content(driver)
        self.wait_for_dom(driver)
        if self.switch_to_iframe_main_target_win0(driver):
            detecter_doublons_jours(driver)
            plugins.call("before_submit", driver)
            if self.save_draft_and_validate(driver):
                self.additional_info_page._handle_save_alerts(driver)

    def run(self) -> None:  # pragma: no cover
        """Point d'entrée principal de l'automatisation."""
        manager = ConfigManager(log_file=self.log_file)
        app_cfg = manager.load()
        self.__init__(self.log_file, app_cfg)
        self.log_initialisation()
        credentials = self.initialize_shared_memory()

        with self.browser_session as session:
            driver = self.setup_browser(session)
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
            except NoSuchElementException as e:
                log_error(f"❌ L'élément n'a pas été trouvé : {str(e)}", self.log_file)
            except TimeoutException as e:
                log_error(
                    f"❌ Temps d'attente dépassé pour un élément : {str(e)}",
                    self.log_file,
                )
            except WebDriverException as e:
                log_error(
                    f"❌ Erreur liée au {messages.WEBDRIVER} : {str(e)}", self.log_file
                )
            except Exception as e:
                log_error(f"❌ {messages.ERREUR_INATTENDUE} : {str(e)}", self.log_file)
            finally:
                try:
                    if session.driver is not None:
                        console_ui.ask_continue(
                            "INFO : Controler et soumettez votre PSATime, Puis appuyer sur ENTRER "
                        )
                    else:
                        console_ui.ask_continue(
                            "ERROR : Controler les Log, Puis appuyer sur ENTRER ET relancer l'outil "
                        )
                    seprateur_menu_affichage_console()
                except ValueError:
                    pass
                finally:
                    self.cleanup_resources(
                        session,
                        credentials.mem_key,
                        credentials.mem_login,
                        credentials.mem_password,
                    )


CHOIX_USER = True  # true pour créer une nouvelle feuille de temps
DEFAULT_TIMEOUT = 10  # Délai d'attente par défaut
LONG_TIMEOUT = 20

# Configuration memoire partagée et cryptage
MEMOIRE_PARTAGEE_CLE = "memoire_partagee_cle"
MEMOIRE_PARTAGEE_DONNEES = "memoire_partagee_donnees"
TAILLE_CLE = 32  # 256 bits pour AES-256
TAILLE_BLOC = 128  # Taille de bloc AES pour le padding


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS UTILS --------------------------------------------- #
# ------------------------------------------------------------------------------------------------- #


def seprateur_menu_affichage_log(log_file: str) -> None:
    write_log(
        "*************************************************************",
        log_file,
        "INFO",
    )


def seprateur_menu_affichage_console():
    console_ui.show_separator()


def get_next_saturday_if_not_saturday(date_str):
    """Retourne le prochain samedi si la date donnée n'est pas déjà un samedi."""
    initial_date = datetime.strptime(date_str, "%d/%m/%Y")
    initial_weekday = initial_date.weekday()
    if initial_weekday != 5:
        days_to_next_saturday = (5 - initial_weekday) % 7
        next_saturday_date = initial_date + timedelta(days=days_to_next_saturday)
        return next_saturday_date.strftime("%d/%m/%Y")
    return date_str


def est_en_mission(description):
    """Renvoie True si la description indique un jour 'En mission'."""
    return description == "En mission"


def ajouter_jour_a_jours_remplis(jour, jours_remplis):
    """Ajoute un jour à la liste jours_remplis si ce n'est pas déjà fait."""
    if jour not in jours_remplis:
        jours_remplis.append(jour)
    return jours_remplis


def afficher_message_insertion(jour, valeur, tentative, message, log_file: str) -> None:
    """Affiche un message d'insertion de la valeur."""
    if message == messages.TENTATIVE_INSERTION:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' ({message}{tentative + 1})",
            log_file,
            "DEBUG",
        )
    else:
        write_log(
            f"⚠️ Valeur '{valeur}' confirmée pour le jour '{jour}' {message})",
            log_file,
            "DEBUG",
        )


# ------------------------------------------------------------------------------------------------- #
# ----------------------------------- FONCTIONS PRINCIPALES --------------------------------------- #
# ------------------------------------------------------------------------------------------------- #


# ------------------------------------------------------------------------------------------------------------------ #
# -------------------------------------------- CODE PRINCIPAL ------------------------------------------------------ #
# ------------------------------------------------------------------------------------------------------------------ #


def main(log_file: str | None = None) -> None:  # pragma: no cover
    """Point d'entrée principal du script.

    Parameters
    ----------
    log_file : str | None, optional
        Chemin du fichier log. S'il vaut ``None``, il sera déterminé via
        :func:`get_log_file`.
    """
    if log_file is None:
        from sele_saisie_auto.shared_utils import get_log_file

        log_file = get_log_file()

    cfg = ConfigManager(log_file=log_file).load()
    PSATimeAutomation(log_file, cfg).run()


# ----------------------------------------------------------------------------
# Wrapper API pour compatibilité
# ----------------------------------------------------------------------------

_AUTOMATION: PSATimeAutomation | None = None
context: SaisieContext | None = None
LOG_FILE: str | None = None


def initialize(log_file: str, app_config: AppConfig) -> None:
    """Instancie l'automatisation."""
    global _AUTOMATION, context, LOG_FILE
    _AUTOMATION = PSATimeAutomation(log_file, app_config)
    context = _AUTOMATION.context
    LOG_FILE = log_file


def log_initialisation() -> None:
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    _AUTOMATION.log_initialisation()


def initialize_shared_memory():
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.initialize_shared_memory()


def setup_browser(session: BrowserSession):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.setup_browser(session)


def connect_to_psatime(driver, cle_aes, login_c, pwd_c):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.login_handler.connect_to_psatime(driver, cle_aes, login_c, pwd_c)


def switch_to_iframe_main_target_win0(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.switch_to_iframe_main_target_win0(driver)


def navigate_from_home_to_date_entry_page(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.navigate_from_home_to_date_entry_page(driver)


def submit_date_cible(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.submit_date_cible(driver)


def navigate_from_work_schedule_to_additional_information_page(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.navigate_from_work_schedule_to_additional_information_page(
        driver
    )


def submit_and_validate_additional_information(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.submit_and_validate_additional_information(driver)


def save_draft_and_validate(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.save_draft_and_validate(driver)


def cleanup_resources(session, memoire_cle, memoire_nom, memoire_mdp):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    return _AUTOMATION.cleanup_resources(session, memoire_cle, memoire_nom, memoire_mdp)


def wait_for_dom(driver):
    if not _AUTOMATION:
        raise RuntimeError("Automation non initialisée")
    _AUTOMATION.wait_for_dom(driver)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
