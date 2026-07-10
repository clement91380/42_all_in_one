"""Translations — FR / EN."""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # Navigation
    "nav_dashboard":  {"fr": "Tableau de bord", "en": "Dashboard"},
    "nav_norm":       {"fr": "Norminette",       "en": "Norminette"},
    "nav_compiler":   {"fr": "Compilation",      "en": "Compilation"},
    "nav_repo":       {"fr": "Verif. Repo",      "en": "Repo Check"},
    "nav_git":        {"fr": "Git / GitHub",     "en": "Git / GitHub"},
    "nav_exams":      {"fr": "Examens",          "en": "Exams"},
    "nav_predictor":  {"fr": "Predicteur",       "en": "Grade Predictor"},
    "nav_exam_mode":  {"fr": "Mode Examen",      "en": "Exam Mode"},
    "nav_settings":   {"fr": "Parametres",       "en": "Settings"},

    # Dashboard
    "dash_title":       {"fr": "42 All-in-One",                          "en": "42 All-in-One"},
    "dash_subtitle":    {"fr": "Accelere ton apprentissage 42",          "en": "Accelerate your 42 learning"},
    "card_norm":        {"fr": "Auto-format ton code\nCheck + Fix",      "en": "Auto-format your code\nCheck + Fix"},
    "card_compiler":    {"fr": "Verifie -Wall -Wextra -Werror\nmain() manquant detecte",
                         "en": "Verify -Wall -Wextra -Werror\nDetects missing main()"},
    "card_repo":        {"fr": "Clone ton repo GitHub\nVerifie tout automatiquement",
                         "en": "Clone your GitHub repo\nVerify everything automatically"},
    "card_git":         {"fr": "Add + Commit + Push en 1 clic\nLogin auto dans le message",
                         "en": "Add + Commit + Push in 1 click\nLogin auto-added to commit"},
    "card_exams":       {"fr": "Base d'exercices rank 02-06\nEntrainement examen",
                         "en": "Exercise bank ranks 02-06\nExam practice"},
    "card_predictor":   {"fr": "Estime ta note avant\nla soutenance",
                         "en": "Estimate your grade\nbefore evaluation"},
    "btn_open":         {"fr": "Ouvrir",  "en": "Open"},

    # Exam mode
    "exam_mode_title":  {"fr": "Mode Examen",      "en": "Exam Mode"},
    "exam_mode_active": {"fr": "EXAMEN EN COURS",  "en": "EXAM IN PROGRESS"},
    "exam_mode_info":   {"fr": "Les automatisations sont desactivees.\nSeule la norminette reste active.",
                         "en": "Automation is disabled.\nOnly norminette remains active."},
    "exam_start":       {"fr": "Demarrer l'examen",  "en": "Start Exam"},
    "exam_stop":        {"fr": "Terminer l'examen",  "en": "End Exam"},
    "exam_rank":        {"fr": "Rang :",             "en": "Rank:"},
    "exam_timer":       {"fr": "Temps :",            "en": "Time:"},
    "exam_pick":        {"fr": "Choisir un exercice", "en": "Pick an exercise"},
    "exam_check":       {"fr": "Verifier (norminette)", "en": "Check (norminette)"},
    "exam_compile":     {"fr": "Compiler",           "en": "Compile"},
    "exam_hint":        {"fr": "Indice",             "en": "Hint"},
    "exam_solution":    {"fr": "Voir le sujet",      "en": "View subject"},
    "exam_locked":      {"fr": "Desactive en mode examen", "en": "Disabled in exam mode"},

    # Norm frame
    "norm_title":       {"fr": "Norminette",         "en": "Norminette"},
    "norm_check":       {"fr": "Verifier",            "en": "Check"},
    "norm_fix":         {"fr": "Corriger tout",       "en": "Fix All"},
    "norm_select":      {"fr": "Choisir fichiers",    "en": "Select Files"},
    "norm_no_files":    {"fr": "Aucun fichier selectionne", "en": "No files selected"},

    # Git frame
    "git_title":        {"fr": "Git / GitHub",        "en": "Git / GitHub"},
    "git_connect":      {"fr": "Connecter",           "en": "Connect"},
    "git_connected":    {"fr": "Connecte comme :",    "en": "Connected as:"},
    "git_not_conn":     {"fr": "Non connecte",        "en": "Not connected"},
    "git_push_all":     {"fr": "Add + Commit + Push", "en": "Add + Commit + Push"},
    "git_commit_msg":   {"fr": "Message de commit :", "en": "Commit message:"},
    "git_open_folder":  {"fr": "Ouvrir dossier",      "en": "Open Folder"},
    "git_clone":        {"fr": "Cloner repo",         "en": "Clone Repo"},
    "git_new_repo":     {"fr": "Nouveau repo GitHub", "en": "New GitHub Repo"},

    # Settings
    "settings_title":   {"fr": "Parametres",         "en": "Settings"},
    "settings_lang":    {"fr": "Langue :",           "en": "Language:"},
    "settings_theme":   {"fr": "Theme :",            "en": "Theme:"},
    "settings_github":  {"fr": "Utilisateur GitHub :","en": "GitHub Username:"},
    "settings_login42": {"fr": "Login 42 :",         "en": "42 Login:"},
    "settings_save":    {"fr": "Sauvegarder",        "en": "Save"},
}


_lang = "fr"


def set_lang(lang: str):
    global _lang
    if lang in ("fr", "en"):
        _lang = lang


def get_lang() -> str:
    return _lang


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_lang, entry.get("en", key))
