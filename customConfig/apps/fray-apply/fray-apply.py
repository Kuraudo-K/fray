#!/usr/bin/env python3
"""
Fray Editor Config - éditeur / apply de config (Python).
Adapté du GLF Config Editor ; chemins Fray, CLI fray-update.
Icône : charcoal-crimson. Binaire : fray-apply.
"""

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('Vte', '2.91')
    from gi.repository import Gtk, Gdk, GLib, Pango, Vte
    _HAS_VTE = True
except (ValueError, ImportError):
    from gi.repository import Gtk, Gdk, GLib, Pango
    _HAS_VTE = False
import subprocess, os, re, threading, json, tempfile, shutil, socket, difflib
from datetime import datetime

def _default_flake_dir():
    env = os.environ.get("FRAY_FLAKE", "").strip()
    if env:
        return env
    return '/home/kouro/Téléchargements/GLF pc/NIX/fray'

FLAKE_DIR = _default_flake_dir()
CUSTOM_DIR = os.path.join(FLAKE_DIR, "customConfig")
CONFIG_FILE = os.path.join(CUSTOM_DIR, "default.nix")
LOG_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Fray-Logs")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Téléchargements")
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".config", "fray-apply")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
BACKUP_DIR = os.path.join(SETTINGS_DIR, "backups")
BACKUP_INDEX = os.path.join(BACKUP_DIR, "index.json")
PKG_SEARCH_CACHE = os.path.join(SETTINGS_DIR, "pkg_search_cache.json")

def _display_home_path(path):
    """Chemin affiché avec ~ au lieu de /home/utilisateur (pour l'interface)."""
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path

BACKUP_DIR_DISPLAY = _display_home_path(BACKUP_DIR)
APP_DIR       = os.path.dirname(os.path.abspath(__file__))
APP_ID        = "fray-apply"

_ICON_PNG_B64 = (
    "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"
    "RU5ErkJggg=="
)


def _icon_png_bytes():
    import base64
    return base64.b64decode(_ICON_PNG_B64)

def _materialize_icon():
    """Extrait l'icône PNG intégrée vers ~/.config/fray-apply/."""
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        path = os.path.join(SETTINGS_DIR, f"{APP_ID}.png")
        data = _icon_png_bytes()
        stale = True
        if os.path.isfile(path):
            try:
                with open(path, 'rb') as f:
                    stale = f.read() != data
            except Exception:
                pass
        if stale:
            with open(path, 'wb') as f:
                f.write(data)
        return path
    except Exception:
        return ""


def _icon_theme_search_paths(icon_path):
    """Chemins Gtk.IconTheme pour une icône (hicolor ou dossier parent)."""
    if not icon_path:
        return []
    paths = []
    parts = icon_path.split(os.sep)
    for i, part in enumerate(parts):
        if i > 0 and parts[i - 1] == "hicolor" and "x" in part:
            left, _, right = part.partition("x")
            if left.isdigit() and right.isdigit():
                paths.append(os.sep.join(parts[:i]))
                break
    parent = os.path.dirname(icon_path)
    if parent and parent not in paths:
        paths.append(parent)
    return paths


def _find_icon_path():
    """Cherche l'icône charcoal-crimson (env, branding, thème, fallback)."""
    for env_key in ("FRAY_APPLY_ICON", "FRAY_ICON"):
        env_icon = os.environ.get(env_key, "").strip()
        if env_icon and os.path.isfile(env_icon):
            return env_icon
    for path in (
        "/run/current-system/sw/share/fray/logo/fray-icon.png",
        "/run/current-system/sw/share/fray/logo/04gr10-charcoal-crimson.png",
        "/run/current-system/sw/share/pixmaps/fray.png",
    ):
        if os.path.isfile(path):
            return path
    for base in (
        os.path.join(APP_DIR, "share", "icons", "hicolor"),
        "/run/current-system/sw/share/icons/hicolor",
        "/usr/share/icons/hicolor",
    ):
        for size in ("256x256", "128x128", "48x48"):
            for name in (APP_ID, "fray"):
                path = os.path.join(base, size, "apps", f"{name}.png")
                if os.path.isfile(path):
                    return path
    embedded = _materialize_icon()
    if embedded:
        return embedded
    return ""

ICON_PATH = _find_icon_path()

def _setup_app_identity():
    """Identité application pour GNOME/KDE (icône barre des tâches + menu)."""
    GLib.set_application_name("Fray Editor Config")
    GLib.set_prgname(APP_ID)
    try:
        Gdk.set_program_class(APP_ID)
    except Exception:
        pass
    if ICON_PATH and os.path.isfile(ICON_PATH):
        try:
            Gtk.Window.set_default_icon_from_file(ICON_PATH)
        except Exception:
            pass
        try:
            theme = Gtk.IconTheme.get_default()
            if theme:
                for search_path in _icon_theme_search_paths(ICON_PATH):
                    theme.append_search_path(search_path)
        except Exception:
            pass
    try:
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property('gtk-xft-antialias', True)
            settings.set_property('gtk-xft-hinting', True)
            settings.set_property('gtk-xft-hintstyle', 'hintmedium')
    except Exception:
        pass
NOVICE_PAGE_IDS = ('config', 'packages', 'restore', 'system')
NOVICE_TAB_COUNT = len(NOVICE_PAGE_IDS)
NOVICE_HIDDEN_SYS_CMDS = frozenset({
    'fray-update --switch', '__nh-switch__', 'fray-cleanup', '__fray-repair__',
})

# Script de maintenance intégré (ex cleaning.nix / fray-cleanup)
FRAY_MAINTENANCE_SCRIPT = r'''#!/usr/bin/env bash
export PAGER=cat
export SYSTEMD_PAGER=cat
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

header() {
  echo -e "\n${BOLD}${CYAN}Fray - maintenance${RESET}\n"
}
pause()      { echo -e "\n${YELLOW}Appuie sur Entrée pour continuer...${RESET}"; read -r _; }
pause_etape(){ echo -e "\n${YELLOW}Appuie sur Entrée pour l'étape suivante...${RESET}"; read -r _; }
confirm()    { echo -e "${YELLOW}$1 [o/N]${RESET} "; read -r rep; [[ "$rep" =~ ^[oO]$ ]]; }

command -v nix-env &>/dev/null || { echo "Nix introuvable."; exit 1; }

action_lister_generations() {
  echo -e "${CYAN}-- Générations système actuelles --${RESET}"
  sudo nix-env --list-generations --profile /nix/var/nix/profiles/system | cat
  pause
}

action_nettoyer_par_jours() {
  echo -e "${CYAN}-- Nettoyage par ancienneté --${RESET}"
  echo -n "Supprimer les générations de plus de combien de jours ? "
  read -r jours
  [[ "$jours" =~ ^[0-9]+$ ]] || { echo -e "${RED}Valeur invalide.${RESET}"; return; }
  confirm "Supprimer les générations de plus de ${jours} jours ?" || return
  sudo nix-collect-garbage --delete-older-than "${jours}d"
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_nettoyer_par_nombre() {
  echo -e "${CYAN}-- Nettoyage par nombre de générations --${RESET}"
  echo -n "Combien de générations récentes conserver ? "
  read -r garder
  { [[ "$garder" =~ ^[0-9]+$ ]] && [[ "$garder" -ge 1 ]]; } \
    || { echo -e "${RED}Valeur invalide (minimum 1).${RESET}"; return; }
  confirm "Conserver les ${garder} dernières générations et supprimer le reste ?" || return
  sudo nix-env --delete-generations "+${garder}" --profile /nix/var/nix/profiles/system
  sudo nix-collect-garbage
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_optimiser_store() {
  echo -e "${CYAN}-- Optimisation du store Nix --${RESET}"
  confirm "Lancer la déduplication dans /nix/store ?" || return
  sudo nix-store --optimise
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_nettoyer_logs() {
  echo -e "${CYAN}-- Nettoyage des logs journald --${RESET}"
  echo -n "Conserver les logs des combien derniers jours ? [défaut : 5] "
  read -r logdays
  logdays=${logdays:-5}
  [[ "$logdays" =~ ^[0-9]+$ ]] || { echo -e "${RED}Valeur invalide.${RESET}"; return; }
  confirm "Supprimer les logs de plus de ${logdays} jours ?" || return
  sudo journalctl --vacuum-time="${logdays}d"
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_vider_corbeille() {
  echo -e "${CYAN}-- Vider la corbeille --${RESET}"
  confirm "Vider définitivement la corbeille (~/.local/share/Trash) ?" || return
  rm -rf ~/.local/share/Trash/*
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_nettoyer_flatpak() {
  echo -e "${CYAN}-- Nettoyage des Flatpak inutilisés --${RESET}"
  confirm "Supprimer les Flatpak inutilisés ?" || return
  flatpak uninstall --unused -y
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_reparer_nix() {
  echo -e "${CYAN}-- Réparation du store Nix --${RESET}"
  confirm "Vérifier l'intégrité du store Nix ?" || return
  echo -e "\n${CYAN}-> Vérification du store Nix...${RESET}"
  sudo nix-store --verify --check-contents
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_reparer_flatpak() {
  echo -e "${CYAN}-- Réparation Flatpak --${RESET}"
  confirm "Vérifier l'intégrité des Flatpak ?" || return
  echo -e "\n${CYAN}-> Réparation des Flatpak...${RESET}"
  flatpak repair
  echo -e "${GREEN}Terminé.${RESET}"; pause
}

action_reparer_tout() {
  echo -e "${CYAN}-- Réparation complète --${RESET}\n"
  do_nix=0; do_flat=0
  confirm "Vérifier l'intégrité du store Nix ?" && do_nix=1
  confirm "Vérifier l'intégrité des Flatpak ?" && do_flat=1
  if [[ "$do_nix" -eq 0 && "$do_flat" -eq 0 ]]; then
    echo -e "${YELLOW}Aucune action sélectionnée.${RESET}"; pause; return
  fi
  if [[ "$do_nix" -eq 1 ]]; then
    echo -e "\n${CYAN}-> Vérification du store Nix...${RESET}"
    sudo nix-store --verify --check-contents
    echo -e "${GREEN}Store Nix : terminé.${RESET}"
    [[ "$do_flat" -eq 1 ]] && pause_etape
  fi
  if [[ "$do_flat" -eq 1 ]]; then
    echo -e "\n${CYAN}-> Réparation des Flatpak...${RESET}"
    flatpak repair
    echo -e "${GREEN}Flatpak : terminé.${RESET}"
  fi
  echo -e "\n${GREEN}${BOLD}Réparation terminée.${RESET}"; pause
}

action_tout() {
  echo -e "${CYAN}-- Nettoyage complet -- collecte des paramètres --${RESET}\n"
  echo -e "${BOLD}Méthode de suppression des générations :${RESET}"
  echo "  1) Par ancienneté (jours)"
  echo "  2) Par nombre à conserver"
  echo -n "Choix : "
  read -r gen_methode
  gen_jours=""; gen_garder=""
  case "$gen_methode" in
    1)
      echo -n "Supprimer les générations de plus de combien de jours ? "
      read -r gen_jours
      [[ "$gen_jours" =~ ^[0-9]+$ ]] || { echo -e "${RED}Valeur invalide, étape ignorée.${RESET}"; gen_methode="skip"; }
      ;;
    2)
      echo -n "Combien de générations récentes conserver ? "
      read -r gen_garder
      { [[ "$gen_garder" =~ ^[0-9]+$ ]] && [[ "$gen_garder" -ge 1 ]]; } \
        || { echo -e "${RED}Valeur invalide, étape ignorée.${RESET}"; gen_methode="skip"; }
      ;;
    *) echo -e "${RED}Choix invalide, étape générations ignorée.${RESET}"; gen_methode="skip" ;;
  esac
  echo -n "Conserver les logs des combien derniers jours ? [défaut : 5] "
  read -r logdays
  logdays=${logdays:-5}
  [[ "$logdays" =~ ^[0-9]+$ ]] || logdays=5
  echo -e "\n${BOLD}Récapitulatif :${RESET}"
  case "$gen_methode" in
    1)    echo "  1. Supprimer les générations de plus de ${gen_jours} jours" ;;
    2)    echo "  1. Conserver les ${gen_garder} dernières générations" ;;
    skip) echo -e "  1. ${RED}Générations : ignorées${RESET}" ;;
  esac
  echo "  2. Optimiser le store Nix"
  echo "  3. Supprimer les logs de plus de ${logdays} jours"
  echo "  4. Vider la corbeille"
  echo "  5. Supprimer les Flatpak inutilisés"
  confirm "\nLancer le nettoyage complet ?" || return
  echo -e "\n${CYAN}-- Étape 1/5 : Générations --${RESET}"
  case "$gen_methode" in
    1) sudo nix-collect-garbage --delete-older-than "${gen_jours}d" && echo -e "${GREEN}Terminé.${RESET}" ;;
    2) sudo nix-env --delete-generations "+${gen_garder}" --profile /nix/var/nix/profiles/system \
         && sudo nix-collect-garbage && echo -e "${GREEN}Terminé.${RESET}" ;;
    skip) echo -e "${YELLOW}Ignorée.${RESET}" ;;
  esac
  pause_etape
  echo -e "\n${CYAN}-- Étape 2/5 : Optimisation du store Nix --${RESET}"
  sudo nix-store --optimise
  echo -e "${GREEN}Terminé.${RESET}"; pause_etape
  echo -e "\n${CYAN}-- Étape 3/5 : Logs journald --${RESET}"
  sudo journalctl --vacuum-time="${logdays}d"
  echo -e "${GREEN}Terminé.${RESET}"; pause_etape
  echo -e "\n${CYAN}-- Étape 4/5 : Corbeille --${RESET}"
  rm -rf ~/.local/share/Trash/*
  echo -e "${GREEN}Terminé.${RESET}"; pause_etape
  echo -e "\n${CYAN}-- Étape 5/5 : Flatpak inutilisés --${RESET}"
  flatpak uninstall --unused -y
  echo -e "${GREEN}Terminé.${RESET}"
  echo -e "\n${GREEN}${BOLD}Nettoyage complet terminé.${RESET}"; pause
}

if [[ "${1:-}" == "--repair-only" ]]; then
  sudo -v
  while true; do
    clear; header
    echo -e "  ${BOLD}1)${RESET} Réparer le Nix Store"
    echo -e "  ${BOLD}2)${RESET} Réparer les Flatpak"
    echo -e "  ${BOLD}3)${RESET} Tout lancer"
    echo -e "  ${BOLD}q)${RESET} Quitter"
    echo ""
    echo -n "Choix : "
    read -r choix
    case "$choix" in
      1) action_reparer_nix ;;
      2) action_reparer_flatpak ;;
      3) action_reparer_tout ;;
      q|Q) echo -e "\n${GREEN}À bientôt.${RESET}\n"; exit 0 ;;
      *) echo -e "${RED}Choix invalide.${RESET}"; sleep 1 ;;
    esac
  done
fi

sudo -v

while true; do
  clear; header
  echo -e "  ${BOLD}1)${RESET} Lister les générations système"
  echo -e "  ${BOLD}2)${RESET} Nettoyer par ancienneté (jours)"
  echo -e "  ${BOLD}3)${RESET} Nettoyer par nombre de générations"
  echo -e "  ${BOLD}4)${RESET} Optimiser le store Nix"
  echo -e "  ${BOLD}5)${RESET} Nettoyer les logs journald"
  echo -e "  ${BOLD}6)${RESET} Vider la corbeille"
  echo -e "  ${BOLD}7)${RESET} Nettoyer les Flatpak inutilisés"
  echo -e "  ${BOLD}8)${RESET} Nettoyage complet (tout enchaîner)"
  echo -e "  ${BOLD}q)${RESET} Quitter"
  echo ""
  echo -n "Choix : "
  read -r choix
  case "$choix" in
    1) action_lister_generations ;;
    2) action_nettoyer_par_jours ;;
    3) action_nettoyer_par_nombre ;;
    4) action_optimiser_store ;;
    5) action_nettoyer_logs ;;
    6) action_vider_corbeille ;;
    7) action_nettoyer_flatpak ;;
    8) action_tout ;;
    q|Q) echo -e "\n${GREEN}À bientôt.${RESET}\n"; exit 0 ;;
    *) echo -e "${RED}Choix invalide.${RESET}"; sleep 1 ;;
  esac
done
'''

def _load_settings():
    try:
        with open(SETTINGS_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _init_settings():
    """Premier lancement -> mode Novice par défaut, persistance explicite."""
    if os.path.isfile(SETTINGS_FILE):
        data = _load_settings()
        if 'advanced_mode' not in data:
            data['advanced_mode'] = False
            _save_settings(data)
        return data
    defaults = {
        'advanced_mode': False,
        'pkg_target_path': CONFIG_FILE,
        'pkg_search_unstable': True,
        'pkg_no_prefix': False,
        'move_show_downloads': True,
        'move_show_custom': True,
    }
    _save_settings(defaults)
    return defaults

def _save_settings(data):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _pkg_cache_load():
    try:
        with open(PKG_SEARCH_CACHE, encoding='utf-8') as f:
            raw = json.load(f)
        out = {}
        for k, v in raw.items():
            q, flag = k.rsplit('|', 1)
            out[(q, flag == '1')] = v
        return out
    except Exception:
        return {}

def _pkg_cache_save(cache):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        items = list(cache.items())
        if len(items) > 200:
            items = items[-200:]
        raw = {f"{q}|{1 if both else 0}": v for (q, both), v in items}
        with open(PKG_SEARCH_CACHE, 'w', encoding='utf-8') as f:
            json.dump(raw, f)
    except Exception:
        pass

def _backup_load_index():
    try:
        with open(BACKUP_INDEX, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'backups': []}

def _backup_save_index(data):
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(BACKUP_INDEX, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _backup_remove_by_ids(ids):
    """Supprime des sauvegardes (fichiers + entrées index)."""
    id_set = set(ids)
    if not id_set:
        return 0
    for backup_id in id_set:
        backup_sub = os.path.join(BACKUP_DIR, backup_id)
        if os.path.isdir(backup_sub):
            shutil.rmtree(backup_sub, ignore_errors=True)
    index = _backup_load_index()
    before = len(index.get('backups', []))
    index['backups'] = [b for b in index.get('backups', []) if b['id'] not in id_set]
    _backup_save_index(index)
    return before - len(index['backups'])

def _backup_purge_pre_restore():
    """Retire les anciennes pré-restaurations (doublons inutiles)."""
    ids = [b['id'] for b in _backup_load_index().get('backups', [])
           if b.get('action') == 'pre-restore']
    return _backup_remove_by_ids(ids)

def _backup_action_label(action):
    return {
        'edit': 'Édition', 'delete': 'Suppression', 'move': 'Déplacement',
        'create': 'Création', 'packages': 'Packages', 'config': 'Configuration',
        'pre-restore': 'Pré-restauration',
    }.get(action, action)

def _backup_diff_desc(old, new, rel_path):
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    ranges = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, old_lines, new_lines).get_opcodes():
        if tag == 'equal':
            continue
        if i1 + 1 == i2:
            ranges.append(str(i1 + 1))
        elif i2 > i1:
            ranges.append(f"{i1 + 1}–{i2}")
    if ranges:
        shown = ', '.join(ranges[:4])
        if len(ranges) > 4:
            shown += '…'
        return f"Édition {rel_path} - lignes {shown}"
    return f"Édition {rel_path}"

def _backup_read_storage(finfo):
    storage = finfo.get('storage', '')
    if not storage:
        return None
    path = os.path.join(BACKUP_DIR, storage)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def _backup_read_after(finfo):
    storage = finfo.get('after_storage', '')
    if not storage:
        return None
    path = os.path.join(BACKUP_DIR, storage)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def _backup_save_after_snapshot(backup_id, path, content):
    safe = re.sub(r'[^\w.-]+', '_', path.strip('/'))
    after_storage = f"{backup_id}/after_{safe}.nix"
    after_abs = os.path.join(BACKUP_DIR, after_storage)
    try:
        os.makedirs(os.path.dirname(after_abs), exist_ok=True)
        with open(after_abs, 'w', encoding='utf-8') as f:
            f.write(content)
        return after_storage
    except Exception:
        return None

def _backup_commit_after(backup_id, paths=None):
    """Enregistre l'état « après » réel d'une sauvegarde (post-écriture)."""
    if not backup_id:
        return
    path_set = set(paths) if paths else None
    index = _backup_load_index()
    changed = False
    for rec in index.get('backups', []):
        if rec['id'] != backup_id:
            continue
        for finfo in rec.get('files', []):
            path = finfo.get('path', '')
            if path_set is not None and path not in path_set:
                continue
            content, _ = read_file(path)
            if content is None:
                continue
            after_storage = _backup_save_after_snapshot(rec['id'], path, content)
            if after_storage:
                finfo['after_storage'] = after_storage
                changed = True
        break
    if changed:
        _backup_save_index(index)

def _backup_maintain_after_links():
    """Recrée les copies « état après » uniquement via la révision suivante (#N+1)."""
    index = _backup_load_index()
    backups = index.get('backups', [])
    changed = False
    for rec in backups:
        for finfo in rec.get('files', []):
            path = finfo.get('path', '')
            rev = finfo.get('revision', 0)
            if not path or not rev or _backup_read_after(finfo) is not None:
                continue
            _, next_f = _backup_find_finfo_by_revision(path, rev + 1)
            if not next_f:
                continue
            content = _backup_read_storage(next_f)
            if content is None:
                continue
            after_storage = _backup_save_after_snapshot(rec['id'], path, content)
            if after_storage:
                finfo['after_storage'] = after_storage
                changed = True
    if changed:
        _backup_save_index(index)

def _backup_diff_stats(old, new):
    if old is None:
        old = ''
    if new is None:
        new = ''
    added = removed = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, old.splitlines(), new.splitlines()).get_opcodes():
        if tag in ('insert', 'replace'):
            added += j2 - j1
        if tag in ('delete', 'replace'):
            removed += i2 - i1
    return added, removed

def _backup_restore_effect_label(backup_content, path, backup_id=None, finfo=None):
    """Décrit l'annulation sélective (pas le remplacement complet du fichier)."""
    if backup_content is None:
        return "introuvable", "err"
    current_content, _ = read_file(path)
    if current_content is None:
        current_content = ''
    if backup_id and finfo is not None:
        after = _backup_after_content(path, backup_id, finfo)
        if after is None:
            return "historique incomplet", "err"
        return _backup_selective_preview(current_content, backup_content, after)
    if backup_content == current_content:
        return "identique (aucun changement)", "same"
    added, removed = _backup_diff_stats(current_content, backup_content)
    parts = []
    if removed:
        parts.append(f"{removed} ligne(s) retirée(s)")
    if added:
        parts.append(f"{added} ligne(s) rétablie(s)")
    return ', '.join(parts) if parts else "modifié", "mod"

def _backup_newer_for_paths(backup_id, paths):
    paths = set(paths)
    newer = []
    for rec in _backup_load_index().get('backups', []):
        if rec['id'] == backup_id:
            break
        overlap = [f.get('rel_path', f.get('basename', '?'))
                   for f in rec.get('files', [])
                   if f.get('path') in paths]
        if overlap:
            newer.append((rec, overlap))
    return newer

def _backup_revision_map():
    """Numérote chaque sauvegarde par fichier (1 = plus ancienne modification)."""
    rev = {}
    counters = {}
    for rec in reversed(_backup_load_index().get('backups', [])):
        for finfo in rec.get('files', []):
            path = finfo.get('path', '')
            if not path:
                continue
            counters[path] = counters.get(path, 0) + 1
            rev[(rec['id'], path)] = counters[path]
    return rev

def _backup_file_revision(backup_id, path):
    return _backup_revision_map().get((backup_id, path), 0)

def _backup_max_revision(path):
    best = 0
    for rec in _backup_load_index().get('backups', []):
        for finfo in rec.get('files', []):
            if finfo.get('path') == path:
                best = max(best, finfo.get('revision', 0))
    return best

def _backup_find_finfo_by_revision(path, revision):
    for rec in _backup_load_index().get('backups', []):
        for finfo in rec.get('files', []):
            if finfo.get('path') == path and finfo.get('revision') == revision:
                return rec, finfo
    return None, None

def _backup_after_content(path, backup_id, finfo=None):
    """État du fichier juste après la modification liée à cette sauvegarde."""
    if not finfo:
        for rec in _backup_load_index().get('backups', []):
            if rec['id'] != backup_id:
                continue
            for nf in rec.get('files', []):
                if nf.get('path') == path:
                    finfo = nf
                    break
            break
    if not finfo:
        content, _ = read_file(path)
        return content

    content = _backup_read_after(finfo)
    if content is not None:
        return content

    rev = finfo.get('revision', 0)
    if rev:
        _, next_f = _backup_find_finfo_by_revision(path, rev + 1)
        if next_f:
            content = _backup_read_storage(next_f)
            if content is not None:
                return content
        if rev >= _backup_max_revision(path):
            content = _backup_read_after(finfo)
            if content is not None:
                return content
            return None

    return None

def _backup_line_label(text):
    if text == '':
        return '(ligne vide)'
    if not text.strip():
        return f'(ligne blanche : {repr(text)})'
    return text.strip()

def _backup_map_equal_lines(left, right):
    """Aligne les lignes identiques entre deux versions (index gauche -> index droite)."""
    sm = difflib.SequenceMatcher(None, left, right)
    mapping = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                mapping[i1 + k] = j1 + k
    return mapping

def _backup_find_context_pos(result, context_lines):
    """Position dans result juste après la plus longue fin de contexte trouvée."""
    if not context_lines:
        return 0
    for size in range(len(context_lines), 0, -1):
        ctx = context_lines[-size:]
        for start in range(len(result) - size, -1, -1):
            if result[start:start + size] == ctx:
                return start + size
    return None

def _backup_find_chunk(result, ref_lines, start, end, hint=None):
    """Trouve un bloc de lignes consécutives dans result (contexte multi-lignes)."""
    chunk = ref_lines[start:end]
    if not chunk:
        return None
    if hint is not None and 0 <= hint <= len(result) - len(chunk):
        if result[hint:hint + len(chunk)] == chunk:
            return hint
    ctx = ref_lines[max(0, start - 4):start]
    pos = _backup_find_context_pos(result, ctx)
    if pos is not None and pos + len(chunk) <= len(result):
        if result[pos:pos + len(chunk)] == chunk:
            return pos
    for i in range(len(result) - len(chunk) + 1):
        if result[i:i + len(chunk)] != chunk:
            continue
        if ctx and (i < len(ctx) or result[i - len(ctx):i] != ctx):
            continue
        return i
    return None

def _backup_revert_selective(current, before, after):
    """
    Annule uniquement le changement before->after sur le fichier actuel.
    Utilise les blocs de diff (opcodes) avec contexte multi-lignes pour éviter
    les mauvaises correspondances sur les lignes dupliquées ou vides.
    """
    before = before if before is not None else ''
    after = after if after is not None else ''
    current = current if current is not None else ''
    if before == after:
        return current, []

    b_lines = before.splitlines()
    a_lines = after.splitlines()
    result = list(current.splitlines())
    notes = []

    sm = difflib.SequenceMatcher(None, b_lines, a_lines)
    for tag, i1, i2, j1, j2 in reversed(list(sm.get_opcodes())):
        if tag == 'equal':
            continue

        a_to_c = _backup_map_equal_lines(a_lines, result)
        b_to_c = _backup_map_equal_lines(b_lines, result)

        if tag == 'insert':
            chunk = a_lines[j1:j2]
            pos = _backup_find_chunk(result, a_lines, j1, j2, a_to_c.get(j1))
            if pos is not None and result[pos:pos + len(chunk)] == chunk:
                del result[pos:pos + len(chunk)]
                for line in chunk:
                    notes.append(f"Retiré : {_backup_line_label(line)}")
            else:
                for line in chunk:
                    notes.append(f"Déjà absent : {_backup_line_label(line)}")

        elif tag == 'delete':
            chunk = b_lines[i1:i2]
            pos = b_to_c.get(i1)
            if pos is None:
                pos = _backup_find_context_pos(result, b_lines[max(0, i1 - 4):i1])
            if pos is None:
                pos = min(i1, len(result))
            if (pos + len(chunk) <= len(result) and
                    result[pos:pos + len(chunk)] == chunk):
                notes.append(f"Déjà présent : {_backup_line_label(chunk[0])}"
                             + (f" (+{len(chunk) - 1})" if len(chunk) > 1 else ""))
            else:
                for k, line in enumerate(chunk):
                    result.insert(pos + k, line)
                    notes.append(f"Rétabli : {_backup_line_label(line)}")

        elif tag == 'replace':
            rem = a_lines[j1:j2]
            add = b_lines[i1:i2]
            pos = _backup_find_chunk(result, a_lines, j1, j2, a_to_c.get(j1))
            if pos is not None and result[pos:pos + len(rem)] == rem:
                result[pos:pos + len(rem)] = add
                notes.append(
                    f"Bloc L{pos + 1} rétabli ({len(rem)}->{len(add)} ligne(s))")
            else:
                notes.append("Bloc modifié introuvable dans le fichier actuel")

    out = '\n'.join(result)
    if current.endswith('\n'):
        out += '\n'
    return out, notes

def _backup_selective_preview(current, before, after):
    """Résumé de l'annulation sélective pour l'interface."""
    if before == after:
        return "rien à annuler", "same"
    new_content, notes = _backup_revert_selective(current, before, after)
    if new_content == (current or ''):
        return "aucun changement nécessaire", "same"
    actions = [n for n in notes if not n.startswith(('Déjà', 'Modification introuvable'))]
    if not actions:
        return "changements déjà absents du fichier", "warn"
    parts = []
    n_rem = sum(1 for n in notes if n.startswith('Retiré'))
    n_add = sum(1 for n in notes if n.startswith('Rétabli'))
    n_mod = sum(1 for n in notes if n.startswith('L'))
    if n_rem:
        parts.append(f"{n_rem} retrait(s)")
    if n_add:
        parts.append(f"{n_add} rétablissement(s)")
    if n_mod:
        parts.append(f"{n_mod} modification(s)")
    return ', '.join(parts) + " - reste du fichier conservé", "mod"

def _backup_format_line_ranges(line_nums):
    if not line_nums:
        return ""
    nums = sorted(set(line_nums))
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append(f"{start}" if start == prev else f"{start}–{prev}")
        start = prev = n
    ranges.append(f"{start}" if start == prev else f"{start}–{prev}")
    return ', '.join(ranges)

def _backup_analyze_change(before, after):
    """Analyse before->after : lignes touchées, ajouts, suppressions, modifications."""
    before = before if before is not None else ''
    after = after if after is not None else ''
    if before == after:
        return None
    old_lines = before.splitlines()
    new_lines = after.splitlines()
    affected_old = set()
    affected_new = set()
    added = []
    removed = []
    modified = []

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, old_lines, new_lines).get_opcodes():
        if tag == 'equal':
            continue
        if tag == 'delete':
            for i in range(i1, i2):
                affected_old.add(i + 1)
                removed.append((i + 1, old_lines[i]))
        elif tag == 'insert':
            for j in range(j1, j2):
                affected_new.add(j + 1)
                added.append((j + 1, new_lines[j]))
        elif tag == 'replace':
            ocount, ncount = i2 - i1, j2 - j1
            pairs = max(ocount, ncount)
            for k in range(pairs):
                oi = i1 + k if k < ocount else None
                nj = j1 + k if k < ncount else None
                if oi is not None:
                    affected_old.add(oi + 1)
                if nj is not None:
                    affected_new.add(nj + 1)
                if oi is not None and nj is not None:
                    old_l = old_lines[oi]
                    new_l = new_lines[nj]
                    if old_l != new_l:
                        modified.append((oi + 1, nj + 1, old_l, new_l))
                elif oi is not None:
                    removed.append((oi + 1, old_lines[oi]))
                elif nj is not None:
                    added.append((nj + 1, new_lines[nj]))

    return {
        'affected_old': affected_old,
        'affected_new': affected_new,
        'added': added,
        'removed': removed,
        'modified': modified,
    }

def _backup_format_change_lines(analysis, max_items=6):
    if not analysis:
        return ["   (aucune différence enregistrée)"]
    out = []
    aff = sorted(analysis['affected_old'] | analysis['affected_new'])
    if aff:
        out.append(f"   Lignes concernées : {_backup_format_line_ranges(aff)}")
    if analysis['removed']:
        out.append(f"   − Supprimé ({len(analysis['removed'])}) :")
        for ln, text in analysis['removed'][:max_items]:
            out.append(f"      L{ln}  {_backup_line_label(text)}")
        if len(analysis['removed']) > max_items:
            out.append(f"      … +{len(analysis['removed']) - max_items} ligne(s)")
    if analysis['added']:
        out.append(f"   + Ajouté ({len(analysis['added'])}) :")
        for ln, text in analysis['added'][:max_items]:
            out.append(f"      L{ln}  {_backup_line_label(text)}")
        if len(analysis['added']) > max_items:
            out.append(f"      … +{len(analysis['added']) - max_items} ligne(s)")
    if analysis['modified']:
        out.append(f"   ~ Modifié ({len(analysis['modified'])}) :")
        for old_ln, new_ln, old_t, new_t in analysis['modified'][:max_items]:
            out.append(f"      L{old_ln}->L{new_ln}")
            out.append(f"         − {old_t.strip()}")
            out.append(f"         + {new_t.strip()}")
        if len(analysis['modified']) > max_items:
            out.append(f"      … +{len(analysis['modified']) - max_items} modification(s)")
    return out

def _backup_file_history_lines(path, current_backup_id, max_items=8):
    """Historique numéroté des sauvegardes pour un même fichier."""
    entries = []
    for rec in reversed(_backup_load_index().get('backups', [])):
        for finfo in rec.get('files', []):
            if finfo.get('path') != path:
                continue
            rev = _backup_file_revision(rec['id'], path)
            marker = " ← sélection" if rec['id'] == current_backup_id else ""
            entries.append(
                f"   #{rev}  {rec.get('timestamp', '')} - "
                f"{rec.get('description', '')}{marker}")
    if len(entries) > max_items:
        return entries[-max_items:]
    return entries

# Thème sombre - clair et confortable
CSS_DARK = b"""
* { font-family: 'Noto Sans', sans-serif; }
window {
    background: #282c3e;
    border: 1px solid #474f70;
    border-radius: 0;
}
decoration, .solid-csd decoration, window decoration {
    background-color: #282c3e;
    box-shadow: none;
    border: none;
}
filechooser toolbar, filechooser toolbar .background,
filechooser .path-bar-box, filechooser .path-bar-box .background,
.path-bar-box, .path-bar-box .background, .path-bar-box box {
    background-color: #313650;
    background-image: none;
    color: #dce4f8;
}
.hbar {
    background: #313650;
    border-bottom: 1px solid #474f70;
    color: #e0e8ff;
}
.hbar title {
    color: #e0e8ff;
    font-weight: bold;
}
.hbar subtitle {
    color: #9aa8c0;
}
headerbar button {
    color: #e0e8ff;
    background: transparent;
    border-radius: 0;
    min-width: 32px;
    min-height: 32px;
}
headerbar button:hover {
    background: #474f70;
}
notebook { background: #282c3e; }
notebook > header { background: #313650; border-bottom: 2px solid #474f70; padding:0; }
.bg { background: #282c3e; }
notebook > header > tabs > tab {
    background: transparent; color: #9aa8c0;
    padding: 10px 16px; border: none;
    border-bottom: 3px solid transparent;
    font-size: 12px; font-weight: 500; margin-bottom: -2px;
}
notebook > header > tabs > tab:checked { color: #72aef5; border-bottom: 3px solid #72aef5; }
notebook > header > tabs > tab:hover:not(:checked) { color: #dce4f8; background: #3a3f58; }
.pad { padding: 18px; background: #282c3e; }
label.h1 { color: #e0e8ff; font-size: 14px; font-weight: 700; }
label.h2 { color: #9aa8c0; font-size: 12px; }
label.path { color: #72aef5; font-size: 12px; font-family: monospace; }
label.ok   { color: #50d080; font-size: 12px; }
label.err  { color: #f07575; font-size: 12px; }
label.warn { color: #e8b840; font-size: 12px; }
.entry, .code-entry {
    background: #313650; color: #90ccff;
    caret-color: #e0e8ff;
    border: 1px solid #474f70; border-radius: 8px;
    padding: 10px 14px; font-size: 13px; font-family: monospace;
}
.entry:focus, .code-entry:focus { border-color: #72aef5; }
textview.entry text { background-color: #232840; color: #c8d4f4; caret-color: #e0e8ff; }
textview.code text  { background-color: #1a1e2e; color: #d0daf8; caret-color: #e0e8ff; }
textview.entry > * { background-color: #232840; }
textview.code  > * { background-color: #1a1e2e; }
.entry-search {
    background: #313650; color: #dce4f8;
    caret-color: #e0e8ff;
    border: 1px solid #474f70; border-radius: 8px;
    padding: 9px 14px; font-size: 13px;
}
.btn-primary {
    background: #1e7a3c; color: #fff;
    border: 1px solid #28a050; border-radius: 8px;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
    text-shadow: none;
}
.btn-primary:hover { background: #28a050; }
.btn-secondary {
    background: #3a3f58; color: #e8ecff;
    border: 1px solid #474f70; border-radius: 8px;
    padding: 8px 16px; font-size: 13px; font-weight: 600;
    text-shadow: none;
}
.btn-secondary:hover { background: #474f70; }
.btn-warn {
    background: #8c2020; color: #fff;
    border: 1px solid #c04040; border-radius: 8px;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
    text-shadow: none;
}
.btn-warn:hover { background: #a83030; }
button, button label { text-shadow: none; -gtk-icon-shadow: none; }
.infobox {
    background: #253560; border: 1px solid #4a68a8;
    border-left: 4px solid #72aef5; border-radius: 6px; padding: 10px 14px;
}
.infobox label { color: #c8dcf8; }
.warnbox {
    background: #3a2d00; border: 1px solid #806010;
    border-left: 4px solid #e8b840; border-radius: 6px; padding: 10px 14px;
}
.warnbox label { color: #edd070; }
.code {
    background: #282c3e; color: #d8e0f8;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace; font-size: 12px;
}
.terminal {
    background: #12141f; color: #dce4f8;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace; font-size: 12px;
}
treeview { background: #313650; color: #ccd4e8; font-size: 12px; }
treeview:selected { background: #2055a0; color: #fff; }
treeview header button {
    background: #3a3f58; color: #9aa8c0;
    border-bottom: 1px solid #474f70; padding: 5px 8px; font-size: 11px;
}
radiobutton label, checkbutton label { color: #ccd4e8; font-size: 12px; }
#term-lbl { color: #ffffff; font-weight: bold; font-size: 13px; }
#term-header { background: #1a1e30; border-top: 1px solid #3a3f58; padding: 6px 8px; }
checkbutton check {
    background: #3a3f58;
    border: 2px solid #72aef5;
    border-radius: 3px;
    min-width: 14px;
    min-height: 14px;
    color: #e0e8ff;
}
checkbutton:checked check { background: #1e7a3c; border-color: #28a050; color: #ffffff; }
checkbutton:hover check { border-color: #90ccff; background: #474f70; }
separator { background: #3a3f58; min-height: 1px; min-width: 1px; }
spinner { color: #72aef5; }
.lineno { background: #1a1e2e; color: #4a5270; font-size: 11px; border-right: 1px solid #3a3f58; }
textview.lineno text { background-color: #1a1e2e; color: #4a5270; }
textview.lineno > * { background-color: #1a1e2e; }
dialog { background: #282c3e; color: #dce4f8; }
dialog > * { background: #282c3e; }
dialog .dialog-vbox { background: #282c3e; }
dialog .dialog-vbox > * { background: #282c3e; }
dialog .message-dialog-content-area { background: #282c3e; }
dialog .message-area { background: #282c3e; }
messagedialog { background: #282c3e; }
messagedialog .message-area { background: #282c3e; }
messagedialog .message-area label { color: #dce4f8; }
dialog label { color: #dce4f8; }
dialog label.message-dialog-title { color: #e0e8ff; font-weight: bold; }
dialog label.secondary-label { color: #c8d4f4; }
dialog button {
    background: #3a3f58; color: #e8ecff;
    border: 1px solid #474f70; border-radius: 6px;
    padding: 8px 16px; font-size: 13px; font-weight: 600;
    text-shadow: none;
}
dialog button:hover { background: #474f70; }
dialog .action-area { background: #282c3e; border-top: 1px solid #474f70; padding: 8px; }
dialog scrolledwindow { background: #282c3e; }
dialog treeview { background: #313650; color: #ccd4e8; }
dialog treeview:selected { background: #2055a0; color: #fff; }
dialog entry { background: #313650; color: #c8d4f4; border: 1px solid #474f70; border-radius: 4px; }
.sidebar { background: #1e2236; }
.sidebar row { background: #1e2236; color: #ccd4e8; }
.sidebar row:hover { background: #2d3250; }
.sidebar row:selected { background: #2055a0; color: #fff; }
pathbar { background: #313650; color: #ccd4e8; }
pathbar button { background: #3a3f58; color: #ccd4e8; border: none; }
pathbar button:hover { background: #474f70; }
pathbar button:checked { background: #2055a0; color: #fff; }
.message-dialog { background: #282c3e; }
.message-dialog .message-area { background: #282c3e; }
.message-dialog .message-area > * { background: #282c3e; }
.message-dialog .message-area .message-text { background: #282c3e; }
.message-dialog .message-area image { background: #282c3e; }
.message-dialog .message-area label { color: #dce4f8; }
listbox { background: #313650; }
listbox row { background: #313650; color: #ccd4e8; }
listbox row:selected { background: #2055a0; color: #fff; }
listbox row:hover { background: #3a3f58; }
.search-bar {
    background: #252840;
    border-bottom: 1px solid #474f70;
    padding: 4px 8px;
}
.search-bar entry {
    background: #313650; color: #dce4f8;
    caret-color: #e0e8ff;
    border: 1px solid #474f70; border-radius: 6px;
    padding: 4px 10px; font-size: 12px;
}
.search-bar entry:focus { border-color: #72aef5; caret-color: #e0e8ff; }
entry.entry-search {
    background: #313650; color: #dce4f8;
    caret-color: #e0e8ff;
    border: 1px solid #474f70; border-radius: 8px;
    padding: 9px 14px; font-size: 13px;
}
entry.entry-search:focus { border-color: #72aef5; caret-color: #e0e8ff; }
.search-count { color: #9aa8c0; font-size: 11px; }
.path-bar-box { background-color: #313650; }
.path-bar-box button { background-color: #3a3f58; color: #ccd4e8; border: none; }
.path-bar-box button:hover { background-color: #474f70; }
.path-bar-box button:checked { background-color: #2055a0; color: #fff; }
.sidebar-panel {
    background: #1e2236;
    border-right: 1px solid #474f70;
    padding: 12px 6px;
}
.content-panel { background: #282c3e; }
.nav-btn {
    background: transparent; color: #9aa8c0;
    border: none; border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 14px; font-size: 13px; font-weight: 500;
}
.nav-btn:hover { background: #2d3250; color: #dce4f8; }
.nav-btn-active {
    background: #2a3558; color: #72aef5;
    border-left: 3px solid #72aef5;
}
.sidebar-title { color: #6a7590; font-size: 11px; font-weight: 600; padding: 4px 12px; }
.sidebar-footer { color: #6a7590; font-size: 11px; padding: 8px 12px; }
.modal-body { background: #282c3e; }
"""

CSS_LIGHT = b"""
* { font-family: 'Noto Sans', sans-serif; }
window {
    background: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 0;
}
.hbar {
    background: #ffffff;
    border-bottom: 1px solid #d0d7de;
    color: #1f2328;
}
.hbar title {
    color: #1f2328;
    font-weight: bold;
}
.hbar subtitle {
    color: #3d444d;
}
headerbar button {
    color: #1f2328;
    background: transparent;
    border-radius: 0;
    min-width: 32px;
    min-height: 32px;
}
headerbar button:hover {
    background: #f3f4f6;
}
notebook { background: #f6f8fa; }
notebook > header { background: #ffffff; border-bottom: 2px solid #d0d7de; padding: 0; }
.bg { background: #f6f8fa; }
notebook > header > tabs > tab {
    background: transparent; color: #3d444d;
    padding: 10px 16px; border: none;
    border-bottom: 3px solid transparent;
    font-size: 12px; font-weight: 500; margin-bottom: -2px;
}
notebook > header > tabs > tab:checked { color: #0969da; border-bottom: 3px solid #0969da; }
notebook > header > tabs > tab:hover:not(:checked) { color: #1f2328; background: #f3f4f6; }
.pad { padding: 18px; background: #f6f8fa; }
label.h1 { color: #1f2328; font-size: 14px; font-weight: 700; }
label.h2 { color: #3d444d; font-size: 12px; }
label.path { color: #0550ae; font-size: 12px; font-family: monospace; }
label.ok   { color: #116329; font-size: 12px; }
label.err  { color: #b91c1c; font-size: 12px; }
label.warn { color: #7a4f00; font-size: 12px; }
.entry, .code-entry {
    background: #ffffff; color: #0550ae;
    caret-color: #1f2328;
    border: 1px solid #d0d7de; border-radius: 8px;
    padding: 10px 14px; font-size: 13px; font-family: monospace;
}
.entry:focus, .code-entry:focus { border-color: #0969da; }
textview.entry text { background-color: #f8fafd; color: #1f2328; caret-color: #1f2328; }
textview.code  text { background-color: #f3f6fa; color: #1f2328; caret-color: #1f2328; }
textview.entry > * { background-color: #f8fafd; }
textview.code  > * { background-color: #f3f6fa; }
.entry-search {
    background: #ffffff; color: #1f2328;
    caret-color: #1f2328;
    border: 1px solid #d0d7de; border-radius: 8px;
    padding: 9px 14px; font-size: 13px;
}
.btn-primary {
    background: #1f883d; color: #fff;
    border: 1px solid #1a7f37; border-radius: 8px;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
}
.btn-primary:hover { background: #1a7f37; }
.btn-secondary {
    background: #f6f8fa; color: #1f2328;
    border: 1px solid #b8c0cc; border-radius: 8px;
    padding: 7px 14px; font-size: 12px;
}
.btn-secondary:hover { background: #eaedf1; }
.btn-warn {
    background: #cf222e; color: #fff;
    border: 1px solid #a40e26; border-radius: 8px;
    padding: 8px 18px; font-size: 13px; font-weight: 600;
}
.btn-warn:hover { background: #a40e26; }
.infobox {
    background: #ddf4ff; border: 1px solid #54aeff;
    border-left: 4px solid #0969da; border-radius: 6px; padding: 10px 14px;
}
.infobox label { color: #0550ae; }
.warnbox {
    background: #fff8c5; border: 1px solid #c08000;
    border-left: 4px solid #7a4f00; border-radius: 6px; padding: 10px 14px;
}
.warnbox label { color: #5c3a00; }
.code {
    background: #f6f8fa; color: #1f2328;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace; font-size: 12px;
}
.terminal {
    background: #1a1d2e; color: #dce4f8;
    font-family: 'JetBrains Mono', 'Fira Mono', monospace; font-size: 12px;
}
treeview { background: #ffffff; color: #1f2328; font-size: 12px; }
treeview:selected { background: #0969da; color: #fff; }
treeview header button {
    background: #f6f8fa; color: #3d444d;
    border-bottom: 1px solid #d0d7de; padding: 5px 8px; font-size: 11px;
}
radiobutton label, checkbutton label { color: #1f2328; font-size: 12px; }
#term-lbl { color: #1f2328; font-weight: bold; font-size: 13px; }
#term-header { background: #eaeef2; border-top: 1px solid #d0d7de; padding: 2px 4px; }
checkbutton check {
    background: #f6f8fa;
    border: 2px solid #0969da;
    border-radius: 3px;
    min-width: 14px;
    min-height: 14px;
    color: #1f2328;
}
checkbutton:checked check { background: #1f883d; border-color: #1a7f37; color: #ffffff; }
checkbutton:hover check { border-color: #0550ae; background: #e8f0fc; }
separator { background: #c8d0d8; min-height: 1px; min-width: 1px; }
spinner { color: #0969da; }
.lineno { background: #edf0f5; color: #4e5c70; font-size: 11px; border-right: 1px solid #d0d7de; }
textview.lineno text { background-color: #edf0f5; color: #4e5c70; }
textview.lineno > * { background-color: #edf0f5; }
.search-bar {
    background: #edf0f5;
    border-bottom: 1px solid #d0d7de;
    padding: 4px 8px;
}
.search-bar entry {
    background: #ffffff; color: #1f2328;
    caret-color: #1f2328;
    border: 1px solid #d0d7de; border-radius: 6px;
    padding: 4px 10px; font-size: 12px;
}
.search-bar entry:focus { border-color: #0969da; caret-color: #1f2328; }
entry.entry-search {
    background: #ffffff; color: #1f2328;
    caret-color: #1f2328;
    border: 1px solid #d0d7de; border-radius: 8px;
    padding: 9px 14px; font-size: 13px;
}
entry.entry-search:focus { border-color: #0969da; caret-color: #1f2328; }
.search-count { color: #3d444d; font-size: 11px; }
dialog { background: #f6f8fa; color: #1f2328; }
dialog label { color: #1f2328; }
dialog button,
dialog .action-area button {
    background: #f6f8fa; color: #1f2328;
    border: 1px solid #b8c0cc; border-radius: 6px; padding: 6px 16px;
}
dialog button:hover,
dialog .action-area button:hover { background: #eaedf1; }
dialog .action-area { background: #f6f8fa; border-top: 1px solid #d0d7de; padding: 8px; }
filechooser { background: #f6f8fa; color: #1f2328; }
filechooser button,
filechooser .action-area button {
    background: #f6f8fa; color: #1f2328;
    border: 1px solid #b8c0cc; border-radius: 6px; padding: 6px 16px;
}
filechooser button:hover,
filechooser .action-area button:hover { background: #eaedf1; }
filechooser .action-area { background: #f6f8fa; border-top: 1px solid #d0d7de; padding: 8px; }
filechooser combobox,
filechooser combobox box { background: #ffffff; color: #1f2328; }
filechooser combobox button { background: #f6f8fa; color: #1f2328; border: 1px solid #b8c0cc; }
filechooser treeview { background: #ffffff; color: #1f2328; }
filechooser treeview:selected { background: #0969da; color: #fff; }
filechooser entry,
filechooser searchbar entry { background: #ffffff; color: #1f2328; border: 1px solid #d0d7de; }
.sidebar-panel {
    background: #edf0f5;
    border-right: 1px solid #d0d7de;
    padding: 12px 6px;
}
.content-panel { background: #f6f8fa; }
.nav-btn {
    background: transparent; color: #3d444d;
    border: none; border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 14px; font-size: 13px; font-weight: 500;
}
.nav-btn:hover { background: #e8ecf2; color: #1f2328; }
.nav-btn-active {
    background: #dce8f8; color: #0969da;
    border-left: 3px solid #0969da;
}
.sidebar-title { color: #656d76; font-size: 11px; font-weight: 600; padding: 4px 12px; }
.sidebar-footer { color: #656d76; font-size: 11px; padding: 8px 12px; }
.modal-body { background: #f6f8fa; }
"""

# Helpers

def run_pkexec(content, dest):
    for cmd in (['pkexec', 'tee', dest], ['sudo', 'tee', dest]):
        try:
            r = subprocess.run(cmd, input=content, capture_output=True, text=True)
            if r.returncode == 0: return True, None
        except FileNotFoundError: continue
        except Exception as e: return False, str(e)
    return False, "pkexec/sudo non disponibles."

def run_pkexec_script(commands):
    script = "#!/bin/bash\nset -e\n" + "\n".join(commands) + "\n"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.sh', prefix='/tmp/fray-editor-', delete=False
        ) as f:
            f.write(script); tmp = f.name
        os.chmod(tmp, 0o755)
        for cmd in (['pkexec', 'bash', tmp], ['sudo', 'bash', tmp]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0: return True, None
                return False, r.stderr or "Erreur inconnue"
            except FileNotFoundError: continue
        return False, "pkexec/sudo non disponibles."
    except Exception as e:
        return False, str(e)
    finally:
        if tmp:
            try: os.unlink(tmp)
            except OSError: pass

def read_file(path):
    try:
        r = subprocess.run(['cat', path], capture_output=True, text=True)
        return (r.stdout, None) if r.returncode == 0 else (None, r.stderr)
    except Exception as e: return None, str(e)

def get_key(line):
    s = line.strip()
    if not s or s.startswith('#'): return None
    if '=' in s: return s.split('=')[0].strip()
    return None

def last_brace(lines):
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip() == '}': return i
    return None

def apply_css(w, *cls):
    ctx = w.get_style_context()
    for c in cls: ctx.add_class(c)
    return w

def _resolve_nix_cmd(name):
    extra = [
        '/run/current-system/sw/bin',
        '/run/wrappers/bin',
        '/nix/var/nix/profiles/default/bin',
        '/usr/local/bin',
        '/usr/bin',
        '/bin',
    ]
    env_path = os.environ.get('PATH', '')
    full_path = ':'.join(extra) + ':' + env_path
    return shutil.which(name, path=full_path)

def _make_env():
    env = os.environ.copy()
    # /run/wrappers/bin DOIT être en premier : il contient les binaires setuid
    # (sudo, pkexec…). Si /run/current-system/sw/bin passe avant, nh et sudo
    # trouvent le sudo sans setuid et échouent avec "doit avoir le bit setuid mis".
    extra = '/run/wrappers/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin'
    env['PATH'] = extra + ':' + env.get('PATH', '')
    return env

_ANSI_RE = re.compile(
    r'\x1b(?:'
    r'\[[0-9;?]*[ -/]*[@-~]'                # CSI  (ex: \x1b[32m, \x1b[?25l)
    r'|\][^\x07\x1b]*(?:\x07|\x1b\\)'       # OSC  (ex: \x1b]0;titre\x07) - AVANT le catch-all
    r'|[@-Z\\^_]'                           # FE 2 chars (@..Z, \, ^, _) - exclut ] et [
    r'|\([A-Z]'                             # Désignation charset G0 (ex: \x1b(B)
    r'|\)[A-Za-z]'                          # Désignation charset G1
    r'|[PX^]'                               # DCS / SOS / PM
    r')'
)

def _strip_ansi(text):
    """Supprime tous les codes ANSI/VT100."""
    return _ANSI_RE.sub('', text)

def _try_unlink(path):
    try: os.unlink(path)
    except OSError: pass

def _make_askpass_script():
    """Crée un script askpass GUI temporaire (zenity/kdialog).
    Utilisé via SUDO_ASKPASS et NH_ASKPASS pour éviter le besoin d'un TTY."""
    for tool in ('zenity', 'kdialog', 'x11-ssh-askpass', 'ssh-askpass'):
        found = _resolve_nix_cmd(tool)
        if not found:
            continue
        try:
            if 'zenity' in tool:
                cmd_line = f'{found} --password --title="Fray" --text="Mot de passe sudo :"'
            elif 'kdialog' in tool:
                cmd_line = f'{found} --password "Mot de passe sudo :"'
            else:
                cmd_line = found
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.sh', prefix='/tmp/fray-askpass-', delete=False
            ) as f:
                f.write(f'#!/bin/sh\n{cmd_line}\n')
                path = f.name
            os.chmod(path, 0o755)
            return path
        except Exception:
            continue
    return None


def _flake_dir():
    """Chemin du flake Fray (FRAY_FLAKE / défaut tree). Jamais /etc/nixos hôte."""
    return os.environ.get("FRAY_FLAKE", "").strip() or FLAKE_DIR

def _default_fray_host():
    return os.environ.get("FRAY_HOST", "").strip() or "fray-iso"

def _is_glf_host():
    # Binaires GLF-OS hôte (noms volontaires glf-*)
    return (
        os.path.isfile("/run/current-system/sw/bin/glf-update")
        or shutil.which("glf-switch") is not None
        or shutil.which("glf-update") is not None
    )

def _refuse_glf_rebuild():
    """Même règle que fray-update : pas de rebuild sur hôte GLF."""
    if _is_glf_host():
        raise RuntimeError(
            "Rebuild hôte GLF interdit via Fray Editor Config.\n"
            "Sur l'hôte : glf-switch / glf-update. Pour Fray : VM ou système Fray."
        )

def _resolve_fray_update():
    return (
        _resolve_nix_cmd("fray-update")
        or shutil.which("fray-update")
        or "/run/current-system/sw/bin/fray-update"
    )

def _resolve_flake_hostname(flake_path=None):
    """Détecte le hostname nixosConfigurations Fray."""
    if flake_path is None:
        flake_path = _flake_dir()
    preferred = _default_fray_host()
    system_hn = socket.gethostname()
    nix = _resolve_nix_cmd('nix') or '/run/current-system/sw/bin/nix'
    try:
        r = subprocess.run(
            [nix, 'eval', f'{flake_path}#nixosConfigurations',
             '--apply', 'builtins.attrNames', '--json'],
            capture_output=True, text=True, timeout=20, env=_make_env()
        )
        if r.returncode == 0:
            names = json.loads(r.stdout.strip())
            if preferred in names:
                return preferred, names
            if system_hn in names:
                return system_hn, names
            if len(names) == 1:
                return names[0], names
            return preferred, names
    except Exception:
        pass
    return preferred, []

def _fray_os_command_plan(cmd_name):
    """Plan Fray : fray-update ou fray-update --switch."""
    flake = _flake_dir()
    hostname, _ = _resolve_flake_hostname(flake)
    fray_upd = _resolve_fray_update()

    if cmd_name == "fray-update":
        step1 = f'{fray_upd}'
        argv1 = [fray_upd]
        return {
            'hostname': hostname,
            'op_label': 'update (pas de switch)',
            'tool': f'fray-update ({fray_upd})',
            'steps': [
                (step1, 'fray-update (flake + Flatpak)', argv1, False),
            ],
            'shell_cmd': f'{step1}\n',
            'refuse_glf': False,
        }

    step1 = f'{fray_upd} --switch --host {hostname} --flake {flake}'
    argv1 = [fray_upd, '--switch', '--host', hostname, '--flake', flake]
    return {
        'hostname': hostname,
        'op_label': 'switch (à chaud)',
        'tool': f'fray-update --switch ({fray_upd})',
        'steps': [
            (step1, 'fray-update --switch', argv1, False),
        ],
        'shell_cmd': f'{step1}\n',
        'refuse_glf': True,
    }

def _nh_os_switch_plan():
    """Applique customConfig via fray-update --switch."""
    flake = _flake_dir()
    hostname, _ = _resolve_flake_hostname(flake)
    fray_upd = _resolve_fray_update()
    cmd = f'{fray_upd} --switch --host {hostname} --flake {flake}'
    argv = [fray_upd, '--switch', '--host', hostname, '--flake', flake]
    return {
        'hostname': hostname,
        'tool': f'fray-update --switch ({fray_upd})',
        'cmd': cmd,
        'argv': argv,
        'needs_sudo': False,
        'shell_cmd': cmd + '\n',
        'refuse_glf': True,
    }

# Application

class App(Gtk.Window):
    def __init__(self):
        super().__init__(title="Fray Editor Config")
        self.set_default_size(1100, 760)
        self.theme = "dark"
        self._pkg_restoring = False
        self._pkg_search_cache = _pkg_cache_load()
        self._pkg_nix_warmed = False
        self._maint_script_path = None

        icon = _find_icon_path()
        if icon and os.path.isfile(icon):
            try:
                self.set_icon_from_file(icon)
            except Exception:
                try:
                    self.set_icon_name(APP_ID)
                except Exception:
                    pass

        self._apply_gtk_theme_settings()

        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(CSS_DARK)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Fray Editor Config"
        hb.props.subtitle = "Configuration NixOS"
        apply_css(hb, "hbar")
        self.set_titlebar(hb)
        self.hb = hb

        self._app_settings = _init_settings()
        self.advanced_mode = self._app_settings.get('advanced_mode', False)

        self.mode_btn = Gtk.Button(label="🔓  Mode avancé")
        apply_css(self.mode_btn, "btn-secondary")
        self.mode_btn.connect("clicked", self._toggle_mode)
        hb.pack_end(self.mode_btn)

        self.theme_btn = Gtk.Button(label="☀  Thème clair")
        apply_css(self.theme_btn, "btn-secondary")
        self.theme_btn.connect("clicked", self._toggle_theme)
        hb.pack_end(self.theme_btn)

        shell = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(shell)

        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        apply_css(self.sidebar, "sidebar-panel")
        self.sidebar.set_size_request(210, -1)

        nav_title = Gtk.Label(label="NAVIGATION")
        apply_css(nav_title, "sidebar-title")
        nav_title.set_halign(Gtk.Align.START)
        self.sidebar.pack_start(nav_title, False, False, 8)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        apply_css(self.stack, "content-panel")

        self._nav_btns = {}
        self._current_page_id = None
        self._tab_defs = [
            ("config",    "Configuration", self.tab_config()),
            ("packages",  "Packages",      self.tab_packages()),
            ("new_nix",   "Nouveau .nix",  self.tab_new_nix()),
            ("move",      "Déplacer",      self.tab_move()),
            ("delete",    "Supprimer",     self.tab_delete()),
            ("edit",      "Éditer",        self.tab_edit()),
            ("restore",   "Restaurer",     self.tab_restore()),
            ("system",    "Système",       self.tab_system()),
        ]
        for page_id, label, page in self._tab_defs:
            self.stack.add_named(page, page_id)
            btn = Gtk.Button(label=f"  {label}")
            btn.set_halign(Gtk.Align.FILL)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            apply_css(btn, "nav-btn")
            btn.connect("clicked", self._on_nav_clicked, page_id)
            self._nav_btns[page_id] = btn
            self.sidebar.pack_start(btn, False, False, 1)

        self.sidebar_footer = Gtk.Label()
        apply_css(self.sidebar_footer, "sidebar-footer")
        self.sidebar_footer.set_halign(Gtk.Align.START)
        self.sidebar_footer.set_line_wrap(True)
        self.sidebar.pack_end(self.sidebar_footer, False, False, 8)

        shell.pack_start(self.sidebar, False, False, 0)
        shell.pack_start(self.stack, True, True, 0)

        self._sync_mode_tabs()
        self._select_page("config")
        self._restore_pkg_target_path()
        self._restore_pkg_options()
        threading.Thread(target=self._warm_nix_pkg_index, daemon=True).start()

        self.connect("realize", lambda *_: self._darken_gtk_window(self))
        self.show_all()

    # Mode Novice / Avancé
    def _sync_mode_tabs(self):
        """Mode Novice : Configuration, Packages, Restaurer et Système (simplifié)."""
        for page_id, _label, _page in self._tab_defs:
            visible = self.advanced_mode or page_id in NOVICE_PAGE_IDS
            btn = self._nav_btns[page_id]
            btn.set_no_show_all(not visible)
            if visible:
                btn.show()
            else:
                btn.hide()

        if hasattr(self, '_sys_cmd_btns'):
            for cmd_name, btn in self._sys_cmd_btns.items():
                hide = (not self.advanced_mode) and cmd_name in NOVICE_HIDDEN_SYS_CMDS
                btn.set_no_show_all(hide)
                if hide:
                    btn.hide()
                else:
                    btn.show()
            self._sync_novice_system_ui()

        current = self.stack.get_visible_child_name()
        if not self.advanced_mode:
            if current not in NOVICE_PAGE_IDS:
                self._current_page_id = None
                self._select_page("config")

        self.mode_btn.set_label(
            "🔒  Mode novice" if self.advanced_mode else "🔓  Mode avancé")
        if self.advanced_mode:
            self.hb.props.subtitle = "Mode avancé"
            self.sidebar_footer.set_text("Toutes les sections disponibles")
        else:
            self.hb.props.subtitle = "Mode novice - fray-update et redémarrage"
            self.sidebar_footer.set_text(
                "Mode novice - Configuration, Packages, Restaurer, Système\n"
                "Passez en mode avancé pour le reste")
        self.show_all()

    def _sync_novice_system_ui(self):
        """Masque maintenance / switch en mode novice (textes + boutons)."""
        novice = not self.advanced_mode
        if hasattr(self, 'sys_cmds_lbl'):
            if novice:
                self.sys_cmds_lbl.set_markup(
                    '<b>fray-update</b>  ->  flake update + Flatpak (pas de switch). '
                    'Redémarrage recommandé après.\n\n'
                    'Utilisez <b>Redémarrer</b> une fois la mise à jour terminée.')
            else:
                self.sys_cmds_lbl.set_markup(
                    '<b>fray-update</b>  ->  flake update + Flatpak (pas de switch). '
                    'Redémarrage recommandé après.\n'
                    '<b>fray-update --switch</b>  ->  Applique les modifications immédiatement sans redémarrer.\n'
                    '<b>Nix-Rebuild</b>  ->  Applique <b>uniquement</b> vos fichiers dans '
                    '<tt>customConfig</tt> (nh os switch). '
                    '<b>Ne fait pas</b> le switch - pour ça, utilisez fray-update --switch.\n\n'
                    '⚠  Certaines modifications (nouveau noyau, services bas niveau) '
                    'nécessitent un redémarrage complet même après un switch.')
        for widget in (
            getattr(self, 'sys_maint_sep', None),
            getattr(self, 'sys_maint_title', None),
            getattr(self, 'sys_maint_infobox', None),
            getattr(self, 'sys_maint_row', None),
        ):
            if widget is None:
                continue
            widget.set_no_show_all(novice)
            if novice:
                widget.hide()
            else:
                widget.show()

    def _set_nav_active(self, page_id):
        for pid, btn in self._nav_btns.items():
            ctx = btn.get_style_context()
            if pid == page_id:
                ctx.add_class("nav-btn-active")
            else:
                ctx.remove_class("nav-btn-active")

    def _select_page(self, page_id):
        if page_id not in self._nav_btns:
            return
        if not self.advanced_mode:
            if page_id not in NOVICE_PAGE_IDS:
                page_id = "config"
        if page_id == self._current_page_id:
            return
        self._current_page_id = page_id
        self._set_nav_active(page_id)
        self.stack.set_visible_child_name(page_id)
        self._on_page_shown(page_id)

    def _on_nav_clicked(self, _btn, page_id):
        self._select_page(page_id)

    def _on_page_shown(self, page_id):
        label = next(l for pid, l, _ in self._tab_defs if pid == page_id)
        self.hb.props.title = f"Fray Editor Config - {label}"
        if page_id == "edit":
            if not getattr(self, "_edit_loaded_once", False):
                self._edit_loaded_once = True
                self._edit_load(self._edit_cur)
        elif page_id == "delete":
            self._del_refresh()
        elif page_id == "move":
            self._move_refresh()
        elif page_id == "restore":
            self._backup_refresh_list()

    def _toggle_mode(self, _btn=None):
        if not self.advanced_mode:
            if not self._confirm_dialog(
                    "Passer en mode avancé ?",
                    secondary_text=(
                        "Le mode avancé débloque tous les onglets :\n"
                        "Nouveau .nix, Déplacer, Supprimer et Éditer,\n"
                        "ainsi que les commandes système avancées.\n\n"
                        "Vous pourrez revenir au mode novice à tout moment."),
                    ok_label="OK"):
                return
            self.advanced_mode = True
        else:
            self.advanced_mode = False
        settings = _load_settings()
        settings['advanced_mode'] = self.advanced_mode
        _save_settings(settings)
        self._sync_mode_tabs()

    # Thème
    def _apply_gtk_theme_settings(self):
        """Demande à GTK (et au gestionnaire de fenêtres) d'utiliser le thème sombre."""
        prefer_dark = self.theme == "dark"
        for settings in (Gtk.Settings.get_default(),):
            if settings:
                try:
                    settings.set_property('gtk-application-prefer-dark-theme', prefer_dark)
                except Exception:
                    pass
        try:
            screen = Gdk.Screen.get_default()
            if screen:
                scr_settings = Gtk.Settings.get_for_screen(screen)
                scr_settings.set_property('gtk-application-prefer-dark-theme', prefer_dark)
        except Exception:
            pass

    def _darken_gtk_window(self, widget):
        """Fond sombre sur la surface GDK (barre de titre incluse si CSD)."""
        if self.theme != "dark":
            return
        try:
            gdk_win = widget.get_window()
            if gdk_win:
                rgba = Gdk.RGBA()
                rgba.parse('#282c3e')
                gdk_win.set_background_rgba(rgba)
        except Exception:
            pass

    def _toggle_theme(self, btn):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_gtk_theme_settings()
        self.css_provider.load_from_data(CSS_LIGHT if self.theme == "light" else CSS_DARK)
        btn.set_label("🌙  Thème sombre" if self.theme == "light" else "☀  Thème clair")
        # Mise à jour des tags de syntaxe Nix dans tous les éditeurs
        self._update_nix_theme(self.theme)
        # Couleurs des CellRendererText (hardcodées, hors CSS)
        if self.theme == "light":
            pkg_blue  = "#1a5da8"   # noms de packages, bleu foncé
            src_amber = "#8a5500"   # colonne Source / Type, ambre foncé
            path_col  = "#023b82"   # chemin config onglet 1, bleu très foncé
        else:
            pkg_blue  = "#90ccff"
            src_amber = "#e8b840"
            path_col  = "#72aef5"
        if hasattr(self, 'pkg_name_renderer'):
            self.pkg_name_renderer.set_property("foreground", pkg_blue)
        if hasattr(self, 'pkg_src_renderer'):
            self.pkg_src_renderer.set_property("foreground", src_amber)
        if hasattr(self, 'del_type_renderer'):
            self.del_type_renderer.set_property("foreground", src_amber)
        if hasattr(self, 'pkg_tree'):
            self.pkg_tree.queue_draw()
        if hasattr(self, 'del_tree'):
            self.del_tree.queue_draw()
        # Label chemin onglet 1
        if hasattr(self, 'cfg_path_lbl'):
            self.cfg_path_lbl.set_markup(
                f'<span foreground="{path_col}" size="small"><tt>📂  {CONFIG_FILE}</tt></span>'
            )

    # Helpers UI
    def _h1(self, t):
        l = Gtk.Label(label=t); apply_css(l, "h1"); l.set_halign(Gtk.Align.START); return l

    def _lbl(self, markup, cls=None):
        l = Gtk.Label(); l.set_markup(markup)
        l.set_halign(Gtk.Align.START); l.set_line_wrap(True)
        if cls: apply_css(l, cls)
        return l

    def _status(self, w, msg, level="ok"):
        ctx = w.get_style_context()
        for c in ("ok","err","warn"): ctx.remove_class(c)
        ctx.add_class(level); w.set_text(msg)

    def _infobox(self, markup, style="infobox"):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        apply_css(b, style); b.pack_start(self._lbl(markup), False, False, 0); return b

    def _dialog_popup_css(self):
        """CSS injecté sur les fenêtres modales (sélecteur de fichiers, etc.)."""
        if self.theme == "light":
            return (
                b"dialog, filechooser, messagedialog { background-color: #f6f8fa; color: #1f2328; }\n"
                b"dialog label, filechooser label, messagedialog label { color: #1f2328; }\n"
                b"dialog button, filechooser button, messagedialog button {\n"
                b"  background-color: #f6f8fa; color: #1f2328;\n"
                b"  border: 1px solid #b8c0cc; border-radius: 6px; padding: 6px 16px; }\n"
                b"dialog button:hover, filechooser button:hover, messagedialog button:hover {\n"
                b"  background-color: #eaedf1; color: #1f2328; }\n"
                b"dialog .action-area, filechooser .action-area, messagedialog .action-area {\n"
                b"  background-color: #f6f8fa; border-top: 1px solid #d0d7de; padding: 8px; }\n"
                b"combobox, combobox box { background-color: #ffffff; color: #1f2328; }\n"
                b"combobox button { background-color: #f6f8fa; color: #1f2328; "
                b"border: 1px solid #b8c0cc; }\n"
                b"treeview { background-color: #ffffff; color: #1f2328; }\n"
                b"treeview:selected { background-color: #0969da; color: #ffffff; }\n"
                b"entry, searchbar, searchbar entry {\n"
                b"  background-color: #ffffff; color: #1f2328; border: 1px solid #d0d7de; }\n"
                b"scrolledwindow, viewport, box, stack { background-color: #f6f8fa; }\n"
                b"separator { background-color: #d0d7de; }\n"
            )
        return (
            b"dialog, filechooser, messagedialog { background-color: #282c3e; color: #dce4f8; }\n"
            b"dialog label, filechooser label { color: #dce4f8; }\n"
            b"dialog button, filechooser button {\n"
            b"  background-color: #3a3f58; color: #e8ecff;\n"
            b"  border: 1px solid #474f70; border-radius: 6px;\n"
            b"  padding: 8px 16px; font-size: 13px; font-weight: 600;\n"
            b"  text-shadow: none; }\n"
            b"dialog button:hover, filechooser button:hover { background-color: #474f70; color: #ffffff; }\n"
            b"dialog .action-area, filechooser .action-area { background-color: #282c3e; "
            b"border-top: 1px solid #474f70; padding: 8px; }\n"
            b"headerbar, filechooser headerbar { background-color: #313650; color: #e0e8ff; "
            b"border-bottom: 1px solid #474f70; }\n"
            b"headerbar button, filechooser headerbar button { text-shadow: none; font-weight: 600; }\n"
        )

    def _dialog_screen_css(self):
        """CSS écran : decoration CSD + barre de chemin (non héritée du dialog)."""
        if self.theme != "dark":
            return b""
        return (
            b"decoration, .solid-csd decoration, window decoration {\n"
            b"  background-color: #282c3e; box-shadow: none; border: none; }\n"
            b"filechooser toolbar, filechooser toolbar .background,\n"
            b"filechooser .path-bar-box, filechooser .path-bar-box .background,\n"
            b"filechooser .path-bar-box box, .path-bar-box, .path-bar-box .background,\n"
            b".path-bar-box box {\n"
            b"  background-color: #313650; background-image: none; color: #dce4f8; }\n"
        )

    def _theme_dialog_widgets(self, dlg):
        """Applique les classes btn-* sur les boutons d'une fenêtre modale."""
        primary_labels = {
            "Choisir", "OK", "Ouvrir", "Appliquer", "Sauvegarder",
            "Enregistrer", "Supprimer", "Exécuter", "Valider",
        }

        def style_btn(btn):
            label = (btn.get_label() or "").strip()
            ctx = btn.get_style_context()
            for cls in ("btn-primary", "btn-secondary", "btn-warn",
                        "suggested-action", "destructive-action"):
                ctx.remove_class(cls)
            apply_css(btn, "btn-primary" if label in primary_labels else "btn-secondary")

        def walk(widget):
            if isinstance(widget, Gtk.HeaderBar):
                apply_css(widget, "hbar")
            elif isinstance(widget, Gtk.Toolbar):
                apply_css(widget, "hbar")
            elif isinstance(widget, Gtk.Button):
                style_btn(widget)
            elif isinstance(widget, Gtk.Entry):
                apply_css(widget, "entry-search")
            if hasattr(widget, "get_children"):
                for child in widget.get_children():
                    walk(child)

        walk(dlg)

    def _add_dialog_buttons(self, dlg, buttons):
        """Boutons dans la zone d'action GTK (fiable sur KDE, GNOME, etc.)."""
        added = []
        for label, resp_id, style in buttons:
            btn = dlg.add_button(label, resp_id)
            apply_css(btn, f"btn-{style}")
            added.append((btn, resp_id, style))
        primary = next(
            (r for _b, r, s in added if s in ("primary", "warn")),
            Gtk.ResponseType.OK)
        dlg.set_default_response(primary)
        return added

    def _style_dialog_csd(self, dlg, title):
        """Barre de titre sombre (HeaderBar seul, boutons en bas - compatible KDE)."""
        hb = Gtk.HeaderBar()
        hb.set_title(title)
        hb.set_show_close_button(True)
        apply_css(hb, "hbar")
        dlg.set_titlebar(hb)
        dlg.set_decorated(False)
        dlg.connect("delete-event", lambda w, *_: (w.response(Gtk.ResponseType.CANCEL), True))
        dlg.connect("map", lambda *_: self._darken_gtk_window(hb))

    def _persist_setting(self, key, value):
        settings = _load_settings()
        settings[key] = value
        _save_settings(settings)
        self._app_settings = settings

    def _restore_pkg_target_path(self):
        if not hasattr(self, 'pkg_target_entry'):
            return
        saved = _load_settings().get('pkg_target_path', '').strip()
        if not saved:
            return
        self._pkg_restoring = True
        try:
            self.pkg_target_entry.set_text(saved)
            self._pkg_target_upd()
        finally:
            self._pkg_restoring = False

    def _restore_pkg_options(self):
        if not hasattr(self, 'pkg_both_cb'):
            return
        settings = _load_settings()
        self._pkg_restoring = True
        try:
            self.pkg_both_cb.set_active(
                settings.get('pkg_search_unstable', True))
            self.pkg_no_prefix_cb.set_active(
                settings.get('pkg_no_prefix', False))
        finally:
            self._pkg_restoring = False

    def _pkg_options_persist(self, *_):
        if getattr(self, '_pkg_restoring', False):
            return
        if not hasattr(self, 'pkg_both_cb'):
            return
        self._persist_setting('pkg_search_unstable', self.pkg_both_cb.get_active())
        self._persist_setting('pkg_no_prefix', self.pkg_no_prefix_cb.get_active())

    def _pkg_target_persist(self, *_):
        if getattr(self, '_pkg_restoring', False):
            return
        if not hasattr(self, 'pkg_target_entry'):
            return
        path = self.pkg_target_entry.get_text().strip()
        if path:
            self._persist_setting('pkg_target_path', path)

    def _question_dialog(self, title, body_markup=None, body_text=None, buttons=None):
        """Dialogue modal standard (compatible tous bureaux, pas de CSD custom)."""
        if buttons is None:
            buttons = [
                ("Annuler", Gtk.ResponseType.CANCEL, "secondary"),
                ("OK", Gtk.ResponseType.OK, "primary"),
            ]
        dlg = Gtk.Dialog(
            title="",
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
        )
        self._style_dialog_csd(dlg, title)
        dlg.set_default_size(480, -1)
        dlg.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self._add_dialog_buttons(dlg, buttons)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_start(20)
        outer.set_margin_end(20)
        outer.set_margin_top(16)
        outer.set_margin_bottom(8)
        apply_css(outer, "modal-body")

        title_lbl = Gtk.Label()
        title_lbl.set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")
        title_lbl.set_line_wrap(True)
        title_lbl.set_xalign(0)
        title_lbl.set_halign(Gtk.Align.START)
        outer.pack_start(title_lbl, False, False, 0)

        if body_markup:
            lbl = Gtk.Label()
            lbl.set_markup(body_markup)
            lbl.set_line_wrap(True)
            lbl.set_xalign(0)
            lbl.set_halign(Gtk.Align.START)
            outer.pack_start(lbl, False, False, 0)
        elif body_text:
            lbl = Gtk.Label(label=body_text)
            lbl.set_line_wrap(True)
            lbl.set_xalign(0)
            lbl.set_halign(Gtk.Align.START)
            apply_css(lbl, "h2")
            outer.pack_start(lbl, False, False, 0)

        area = dlg.get_content_area()
        area.set_border_width(0)
        area.pack_start(outer, True, True, 0)
        self._apply_dialog_theme(dlg)
        resp = dlg.run()
        dlg.destroy()
        return resp

    def _open_nix_file_chooser(self, title, start_folder, ok_label="Choisir"):
        """Sélecteur de fichiers .nix - layout GTK classique (sans header bar)."""
        dlg = Gtk.FileChooserDialog(
            title=title,
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dlg.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dlg.add_button(ok_label, Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        try:
            dlg.set_use_header_bar(False)
        except Exception:
            pass
        if start_folder and os.path.isdir(start_folder):
            dlg.set_current_folder(start_folder)
        nf = Gtk.FileFilter()
        nf.set_name("Fichiers NixOS (*.nix)")
        nf.add_pattern("*.nix")
        dlg.add_filter(nf)
        self._apply_dialog_theme(dlg)
        return dlg

    def _confirm_dialog(self, title, secondary_markup=None, secondary_text=None,
                        message_type=Gtk.MessageType.QUESTION,
                        ok_label="OK", warn=False):
        """Boîte de dialogue confirmée, harmonisée au thème."""
        style = "warn" if warn else "primary"
        resp = self._question_dialog(
            title,
            body_markup=secondary_markup,
            body_text=secondary_text,
            buttons=[
                ("Annuler", Gtk.ResponseType.CANCEL, "secondary"),
                (ok_label, Gtk.ResponseType.OK, style),
            ])
        return resp == Gtk.ResponseType.OK

    def _write_maintenance_script(self):
        """Écrit le script de maintenance intégré (ex fray-cleanup)."""
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.sh', prefix='/tmp/fray-maint-',
                delete=False) as f:
            f.write(FRAY_MAINTENANCE_SCRIPT)
            path = f.name
        os.chmod(path, 0o755)
        if self._maint_script_path and self._maint_script_path != path:
            _try_unlink(self._maint_script_path)
        self._maint_script_path = path
        return self._maint_script_path

    # Sauvegardes automatiques
    def _backup_snapshot(self, action, description, paths, include_default=False):
        """Copie locale des fichiers avant modification (dossier utilisateur)."""
        paths = list(dict.fromkeys(p for p in paths if p))
        if include_default and CONFIG_FILE not in paths:
            paths.append(CONFIG_FILE)
        entries = []
        path_contents = {}
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_sub = os.path.join(BACKUP_DIR, backup_id)
        try:
            os.makedirs(backup_sub, exist_ok=True)
        except Exception:
            return None

        for path in paths:
            content, err = read_file(path)
            if content is None:
                continue
            path_contents[path] = content
            safe = re.sub(r'[^\w.-]+', '_', path.strip('/'))
            storage = f"{backup_id}/{safe}.nix"
            storage_abs = os.path.join(BACKUP_DIR, storage)
            try:
                with open(storage_abs, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception:
                continue
            imports = []
            for fpath, lineno, text in self._find_import_references(path):
                imports.append({'file': fpath, 'line': lineno, 'text': text})
            for fpath, lineno, text in self._find_import_in_default_nix(path):
                imp = {'file': fpath, 'line': lineno, 'text': text}
                if imp not in imports:
                    imports.append(imp)
            try:
                rel_path = os.path.relpath(path, CUSTOM_DIR)
            except Exception:
                rel_path = path
            entries.append({
                'path': path,
                'rel_path': rel_path,
                'basename': os.path.basename(path),
                'storage': storage,
                'imports': imports,
                'existed': os.path.isfile(path),
            })

        if not entries:
            try:
                os.rmdir(backup_sub)
            except OSError:
                pass
            return None

        index = _backup_load_index()
        rev_map = _backup_revision_map()
        for entry in entries:
            path = entry['path']
            prev = max((v for (_bid, p), v in rev_map.items() if p == path), default=0)
            entry['revision'] = prev + 1

        record = {
            'id': backup_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': action,
            'description': description,
            'files': entries,
        }
        index = _backup_load_index()
        index.setdefault('backups', []).insert(0, record)
        for nfile in record.get('files', []):
            npath = nfile.get('path', '')
            after_content = path_contents.get(npath)
            new_rev = nfile.get('revision', 0)
            if after_content is None or not new_rev:
                continue
            for prev_rec in index.get('backups', [])[1:]:
                for prev_f in prev_rec.get('files', []):
                    if prev_f.get('path') != npath:
                        continue
                    if prev_f.get('revision') != new_rev - 1:
                        continue
                    after_storage = _backup_save_after_snapshot(
                        prev_rec['id'], npath, after_content)
                    if after_storage:
                        prev_f['after_storage'] = after_storage
                    break
                else:
                    continue
                break
        _backup_save_index(index)
        if hasattr(self, 'backup_store'):
            GLib.idle_add(self._backup_refresh_list)
        return backup_id

    def _backup_refresh_list(self):
        if not hasattr(self, 'backup_store'):
            return
        _backup_purge_pre_restore()
        _backup_maintain_after_links()
        self.backup_store.clear()
        rev_map = _backup_revision_map()
        for rec in _backup_load_index().get('backups', []):
            rev_parts = []
            for finfo in rec.get('files', []):
                path = finfo.get('path', '')
                rel = finfo.get('rel_path', finfo.get('basename', '?'))
                rev = finfo.get('revision') or rev_map.get((rec['id'], path), 0)
                if rev:
                    rev_parts.append(f"{rel} #{rev}")
                else:
                    rev_parts.append(rel)
            files_lbl = ', '.join(rev_parts[:3])
            if len(rev_parts) > 3:
                files_lbl += f'… (+{len(rev_parts) - 3})'
            self.backup_store.append([
                False,
                rec['id'],
                rec.get('timestamp', ''),
                _backup_action_label(rec.get('action', '')),
                rec.get('description', ''),
                files_lbl,
            ])
        self._backup_update_delete_label()
        self._backup_on_selection_changed()

    def _backup_toggle(self, widget, path):
        self.backup_store[path][0] = not self.backup_store[path][0]
        self._backup_update_delete_label()

    def _backup_update_delete_label(self):
        if not hasattr(self, 'backup_del_btn'):
            return
        n = len(self._backup_checked_ids())
        if n:
            self.backup_del_btn.set_label(f"  🗑  Supprimer ({n})")
        else:
            self.backup_del_btn.set_label("  🗑  Supprimer")

    def _backup_checked_ids(self):
        if not hasattr(self, 'backup_store'):
            return []
        return [row[1] for row in self.backup_store if row[0]]

    def _backup_record_for_id(self, backup_id):
        if not backup_id:
            return None
        return next((b for b in _backup_load_index().get('backups', [])
                     if b['id'] == backup_id), None)

    def _backup_on_selection_changed(self, *_):
        if not hasattr(self, 'backup_details_buf'):
            return
        backup_id = self._backup_selected_id()
        record = self._backup_record_for_id(backup_id)
        buf = self.backup_details_buf
        buf.set_text('')
        if not record:
            buf.set_text("Sélectionnez une sauvegarde pour voir son contenu.")
            return

        rev_map = _backup_revision_map()
        lines = [
            f"Sauvegarde du {record.get('timestamp', '')}",
            f"Action : {_backup_action_label(record.get('action', ''))}",
            f"Description : {record.get('description', '')}",
            "",
            "Modification enregistrée (état avant -> état après l'action) :",
            "",
        ]
        paths = []
        for finfo in record.get('files', []):
            path = finfo.get('path', '')
            rel = finfo.get('rel_path', finfo.get('basename', '?'))
            paths.append(path)
            rev = finfo.get('revision') or rev_map.get((backup_id, path), 0)
            rev_lbl = f"#{rev}" if rev else "?"
            lines.append(f"-- {rel}  (version {rev_lbl}) --")

            before = _backup_read_storage(finfo)
            after = _backup_after_content(path, backup_id, finfo)
            analysis = _backup_analyze_change(before, after)
            lines.extend(_backup_format_change_lines(analysis))

            hist = _backup_file_history_lines(path, backup_id)
            if len(hist) > 1:
                lines.append("   Historique du fichier :")
                lines.extend(hist)
            lines.append("")

        lines.extend([
            "Annulation sélective (uniquement ce changement, le reste conservé) :",
            "",
        ])
        for finfo in record.get('files', []):
            path = finfo.get('path', '')
            rel = finfo.get('rel_path', finfo.get('basename', '?'))
            backup_content = _backup_read_storage(finfo)
            effect, kind = _backup_restore_effect_label(
                backup_content, path, backup_id, finfo)
            prefix = {'add': '➕', 'mod': '✏️', 'same': '✓', 'err': '❌', 'warn': '⚠'}.get(kind, '•')
            lines.append(f"{prefix}  {rel} - {effect}")
            before = backup_content or ''
            after = _backup_after_content(path, backup_id, finfo) or ''
            current, _ = read_file(path)
            _, detail_notes = _backup_revert_selective(current or '', before, after)
            for note in detail_notes[:8]:
                lines.append(f"      -> {note}")
            if len(detail_notes) > 8:
                lines.append(f"      … +{len(detail_notes) - 8}")

        lines.extend([
            "",
            "ℹ  Les modifications plus récentes non concernées seront conservées.",
            "La sauvegarde restaurée sera retirée de l'historique.",
        ])

        buf.set_text('\n'.join(lines))

    def _backup_selected_id(self):
        sel = self.backup_tree.get_selection()
        model, tree_iter = sel.get_selected()
        return model[tree_iter][1] if tree_iter else None

    def _backup_restore_selected(self, *_):
        backup_id = self._backup_selected_id()
        if not backup_id:
            return self._status(self.backup_status,
                                "⚠  Sélectionnez une sauvegarde.", "warn")
        record = self._backup_record_for_id(backup_id)
        if not record:
            return self._status(self.backup_status, "❌  Sauvegarde introuvable.", "err")

        names = ', '.join(f.get('basename', '?') for f in record.get('files', [])[:4])
        secondary = (
            f"<b>{GLib.markup_escape_text(record.get('description', ''))}</b>\n"
            f"<tt>{GLib.markup_escape_text(names)}</tt>\n\n"
            "Seul le changement de cette sauvegarde sera annulé "
            "(lignes ajoutées retirées, supprimées rétablies, modifiées inversées).\n"
            "Les autres modifications du fichier seront conservées.\n"
            "La sauvegarde sera retirée de l'historique après restauration.")

        if not self._confirm_dialog(
                "Restaurer cette sauvegarde ?",
                secondary_markup=secondary,
                ok_label="Restaurer"):
            return

        ok, err, changed = self._backup_restore_record(record)
        if ok:
            if not changed:
                self._status(self.backup_status,
                             "ℹ  Aucun changement nécessaire - sauvegarde retirée.", "warn")
            else:
                self._status(self.backup_status,
                             f"✅  Sauvegarde {backup_id} restaurée et retirée.", "ok")
            _backup_remove_by_ids([backup_id])
            self._backup_refresh_list()
            if hasattr(self, '_del_refresh'):
                self._del_refresh()
        else:
            self._status(self.backup_status, f"❌  {err}", "err")

    def _backup_restore_record(self, record):
        backup_id = record['id']
        tmp_files = []
        cmds = []
        changed = False
        try:
            for finfo in record.get('files', []):
                path = finfo.get('path', '')
                before = _backup_read_storage(finfo)
                if before is None:
                    continue
                current, _ = read_file(path)
                if current is None:
                    current = ''
                after = _backup_after_content(path, backup_id, finfo)
                if after is None:
                    return False, (
                        "Historique incomplet pour cette sauvegarde "
                        f"(révision #{finfo.get('revision', '?')}). "
                        "Restaurez d'abord les versions plus récentes, "
                        "ou supprimez les entrées obsolètes."
                    ), False
                if before == after:
                    continue
                new_content, notes = _backup_revert_selective(current, before, after)
                if new_content == current:
                    continue
                changed = True
                with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.nix', prefix='/tmp/fray-bak-',
                        delete=False, encoding='utf-8') as tf:
                    tf.write(new_content)
                    tmp_files.append((tf.name, path))
            for tmp, dest in tmp_files:
                cmds.append(f'mkdir -p "{os.path.dirname(dest)}"')
                cmds.append(f'cp "{tmp}" "{dest}"')
                cmds.append(f'chmod 644 "{dest}"')
            if not cmds:
                return True, None, changed
            ok, err = run_pkexec_script(cmds)
            if not ok:
                return False, err, False

            cfg_content, _ = read_file(CONFIG_FILE)
            if cfg_content is None:
                return True, None, changed
            cfg_lines = cfg_content.splitlines()
            cfg_modified = False
            for finfo in record.get('files', []):
                if finfo.get('path') == CONFIG_FILE:
                    continue
                try:
                    rel = './' + os.path.relpath(
                        finfo['path'], os.path.dirname(CONFIG_FILE))
                except Exception:
                    continue
                rel_norm = os.path.normpath(rel)
                present = False
                for line in cfg_lines:
                    s = line.strip()
                    if s.startswith('#'):
                        continue
                    m = self._RE_IMPORT_ENTRY.match(s)
                    if m and os.path.normpath(m.group(1)) == rel_norm:
                        present = True
                        break
                if not present:
                    new_lines, found = self._insert_import_grouped(cfg_lines, rel)
                    if found and new_lines != cfg_lines:
                        cfg_lines = new_lines
                        cfg_modified = True
            if cfg_modified:
                ok2, err2 = run_pkexec('\n'.join(cfg_lines) + '\n', CONFIG_FILE)
                if not ok2:
                    return False, err2, False
            return True, None, changed
        finally:
            for tmp, _ in tmp_files:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def _backup_delete_selected(self, *_):
        ids = self._backup_checked_ids()
        if not ids:
            backup_id = self._backup_selected_id()
            if backup_id:
                ids = [backup_id]
        if not ids:
            return self._status(self.backup_status,
                                "⚠  Cochez une ou plusieurs sauvegardes.", "warn")
        n = len(ids)
        title = f"Supprimer {n} sauvegarde{'s' if n > 1 else ''} ?"
        if not self._confirm_dialog(
                title,
                secondary_text="Cette action est irréversible.",
                message_type=Gtk.MessageType.WARNING,
                ok_label="Supprimer", warn=True):
            return
        removed = _backup_remove_by_ids(ids)
        self._backup_refresh_list()
        self._status(self.backup_status,
                     f"✅  {removed} sauvegarde{'s' if removed > 1 else ''} supprimée(s).",
                     "ok")

    def _backup_open_folder(self, *_):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
        except Exception:
            pass
        for cmd in (['xdg-open', BACKUP_DIR], ['nautilus', BACKUP_DIR],
                    ['dolphin', BACKUP_DIR], ['thunar', BACKUP_DIR]):
            try:
                subprocess.Popen(cmd, env=_make_env())
                return
            except FileNotFoundError:
                continue
        self._status(self.backup_status, f"ℹ  Dossier : {BACKUP_DIR_DISPLAY}", "info")

    def _apply_dialog_theme(self, dlg, show_now=True):
        """Thème pour dialogues et sélecteur de fichiers."""
        if self.theme == "dark":
            self._apply_gtk_theme_settings()
        provider = Gtk.CssProvider()
        provider.load_from_data(self._dialog_popup_css())
        ctx = dlg.get_style_context()
        ctx.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        dlg.connect("destroy", lambda *_: ctx.remove_provider(provider))
        screen = Gdk.Screen.get_default()
        screen_css = self._dialog_screen_css()
        if screen and screen_css:
            screen_provider = Gtk.CssProvider()
            screen_provider.load_from_data(screen_css)
            Gtk.StyleContext.add_provider_for_screen(
                screen, screen_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER + 300)
            dlg.connect("destroy", lambda *_:
                        Gtk.StyleContext.remove_provider_for_screen(
                            screen, screen_provider))

        def _darken_dialog(d):
            self._darken_gtk_window(d)
            tb = d.get_titlebar()
            if tb:
                self._darken_gtk_window(tb)

        dlg.connect("realize", lambda d, *_: _darken_dialog(d))
        dlg.connect("map", lambda d, *_: _darken_dialog(d))
        self._theme_dialog_widgets(dlg)
        dlg.connect("map", lambda d, *_: self._theme_dialog_widgets(d))
        if show_now:
            dlg.show_all()
            self._theme_dialog_widgets(dlg)
            _darken_dialog(dlg)

    # ---
    # ONGLET 1 - Config
    # ---
    def tab_config(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apply_css(box, "pad")

        box.pack_start(self._h1("Ajouter une ligne de configuration"), False, False, 0)

        box.pack_start(self._infobox(
            '<b>ℹ️  Options de configuration Fray</b> - ex : <tt>services.openssh.enable = true;</tt>\n'
            'Supporte les blocs multi-lignes et les commentaires <tt>#</tt>.\n'
            '<b>📦  Pour les packages</b> (<tt>pkgs.</tt>), utilisez l\'<b>onglet Packages</b>.'
        ), False, False, 0)

        box.pack_start(self._lbl(
            '<span foreground="#9aa8c0" size="small">Ligne(s) à ajouter - '
            'blocs <tt>{ }</tt> et commentaires <tt>#</tt> acceptés :</span>'
        ), False, False, 0)

        sw_entry = Gtk.ScrolledWindow()
        sw_entry.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_entry.set_min_content_height(280)
        sw_entry.set_max_content_height(460)

        self.cfg_tv = Gtk.TextView()
        self.cfg_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.cfg_tv.set_monospace(True)
        self.cfg_tv.set_left_margin(14); self.cfg_tv.set_right_margin(14)
        self.cfg_tv.set_top_margin(10);  self.cfg_tv.set_bottom_margin(10)
        apply_css(self.cfg_tv, "entry")
        self._add_nix_tags(self.cfg_tv.get_buffer(), "_hl_handler_cfg")

        self._buf_set_text(
            self.cfg_tv.get_buffer(), "_hl_handler_cfg",
            '# ------------------------------------------------------------------\n'
            '# Exemple : Steam avec ouverture de port réseau\n'
            '# ------------------------------------------------------------------\n'
            'programs.steam = {\n'
            '  enable = true;\n'
            '  localNetworkGameTransfers.openFirewall = true;\n'
            '};'
        )
        sw_entry.add(self.cfg_tv)
        self._attach_undo(self.cfg_tv, "_hl_handler_cfg")
        box.pack_start(sw_entry, False, False, 0)

        row = Gtk.Box(spacing=8)
        btn = Gtk.Button(label="  ➕  Ajouter dans default.nix")
        apply_css(btn, "btn-primary")
        btn.connect("clicked", self._cfg_add)
        row.pack_start(btn, False, False, 0)
        btn_c = Gtk.Button(label="Effacer")
        apply_css(btn_c, "btn-secondary")
        btn_c.connect("clicked", lambda *_: self.cfg_tv.get_buffer().set_text(""))
        row.pack_start(btn_c, False, False, 0)
        box.pack_start(row, False, False, 0)

        self.cfg_status = Gtk.Label(label="")
        self.cfg_status.set_halign(Gtk.Align.START)
        box.pack_start(self.cfg_status, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)
        self.cfg_path_lbl = Gtk.Label()
        self.cfg_path_lbl.set_markup(
            f'<span foreground="#72aef5" size="small"><tt>📂  {CONFIG_FILE}</tt></span>'
        )
        self.cfg_path_lbl.set_halign(Gtk.Align.START)
        box.pack_start(self.cfg_path_lbl, False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(box); return sw

    def _parse_input_segments(self, text):
        segments = []
        lines = text.splitlines()
        pending_comments = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                if pending_comments:
                    pending_comments.append(line)
                i += 1
                continue

            if stripped.startswith('#'):
                pending_comments.append(line)
                i += 1
                continue

            depth = stripped.count('{') - stripped.count('}')
            seg_lines = list(pending_comments) + [line]
            pending_comments = []

            if depth > 0:
                i += 1
                while i < len(lines) and depth > 0:
                    seg_lines.append(lines[i])
                    depth += lines[i].count('{') - lines[i].count('}')
                    i += 1
            else:
                i += 1

            first_code = next(
                (l.strip() for l in seg_lines if l.strip() and not l.strip().startswith('#')),
                ''
            )
            top_key = get_key(first_code) if first_code else None
            segments.append((seg_lines, top_key))

        if pending_comments:
            segments.append((pending_comments, None))

        return segments

    def _find_entry_extent(self, lines, key_idx):
        stripped = lines[key_idx].strip()
        depth = stripped.count('{') - stripped.count('}')
        if depth <= 0:
            return (key_idx, key_idx)
        i = key_idx + 1
        while i < len(lines) and depth > 0:
            depth += lines[i].count('{') - lines[i].count('}')
            i += 1
        return (key_idx, i - 1)

    def _cfg_add(self, *_):
        buf  = self.cfg_tv.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True).strip()
        if not text:
            return self._status(self.cfg_status, "⚠  Entrez au moins une ligne.", "warn")

        segments = self._parse_input_segments(text)
        if not segments:
            return self._status(self.cfg_status, "⚠  Aucun contenu valide.", "warn")

        content, err = read_file(CONFIG_FILE)
        if content is None:
            return self._status(self.cfg_status, f"❌  {err}", "err")

        lines = content.splitlines()
        added, replaced, skipped_list = [], [], []

        for seg_lines, top_key in segments:
            normalized = []
            for l in seg_lines:
                s = l.strip()
                is_code = s and not s.startswith('#')
                if (is_code and '=' in s and '{' not in s
                        and not s.endswith(';') and not s.endswith(',')
                        and not s.endswith('{')):
                    l = l.rstrip() + ';'
                normalized.append(l)
            seg_lines = normalized

            eidx = None
            if top_key:
                for i, fl in enumerate(lines):
                    indent_len = len(fl) - len(fl.lstrip())
                    if indent_len <= 2 and get_key(fl.strip()) == top_key:
                        eidx = i; break

            if eidx is not None:
                start, end = self._find_entry_extent(lines, eidx)
                resp = self._question_dialog(
                    "Option déjà présente",
                    body_markup=(
                        f"Clé <tt><b>{GLib.markup_escape_text(top_key)}</b></tt> déjà présente "
                        f"(lignes {start+1}–{end+1}).\n\nRemplacer le bloc existant ?"),
                    buttons=[
                        ("Annuler", Gtk.ResponseType.CANCEL, "secondary"),
                        ("Ignorer", Gtk.ResponseType.NO, "secondary"),
                        ("Remplacer", Gtk.ResponseType.YES, "primary"),
                    ])

                if resp == Gtk.ResponseType.CANCEL:
                    return self._status(self.cfg_status, "⏹  Opération annulée.", "warn")
                elif resp == Gtk.ResponseType.YES:
                    indent = self._RE_INDENT.match(lines[start]).group(1)
                    new_block = [indent + l for l in seg_lines]
                    lines[start:end+1] = new_block
                    replaced.append(top_key)
                else:
                    skipped_list.append(top_key)
            else:
                idx = last_brace(lines)
                if idx is None:
                    return self._status(self.cfg_status, "❌  Dernier '}' introuvable.", "err")

                if idx > 0 and lines[idx - 1].strip():
                    lines.insert(idx, ''); idx += 1

                for sl in seg_lines:
                    lines.insert(idx, '  ' + sl); idx += 1

                lines.insert(idx, '')

                label = top_key or (seg_lines[0].strip()[:30] if seg_lines else "?")
                added.append(label)

        bid = self._backup_snapshot(
            'config',
            f"Configuration default.nix ({len(added)} ajout(s), "
            f"{len(replaced)} remplacement(s))",
            [CONFIG_FILE])
        ok, err = run_pkexec('\n'.join(lines) + '\n', CONFIG_FILE)
        if ok:
            _backup_commit_after(bid, [CONFIG_FILE])
            parts = []
            if added:        parts.append(f"✅  {len(added)} ajoutée(s)")
            if replaced:     parts.append(f"🔄  {len(replaced)} remplacée(s)")
            if skipped_list: parts.append(f"⏭  {len(skipped_list)} ignorée(s)")
            self._status(self.cfg_status, "   ".join(parts) or "ℹ  Rien changé.", "ok")
            buf.set_text("")
        else:
            self._status(self.cfg_status, f"❌  {err}", "err")

    # ---
    # ONGLET 2 - Packages
    # ---
    def tab_packages(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        apply_css(vbox, "bg")

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apply_css(top, "pad")
        top.pack_start(self._h1("Chercher et ajouter des packages NixOS"), False, False, 0)

        self.pkg_both_cb = Gtk.CheckButton(
            label="🔍  Chercher aussi dans nixpkgs-unstable (affiche les versions différentes)")
        apply_css(self.pkg_both_cb, "h2")
        self.pkg_both_cb.set_active(True)
        self.pkg_both_cb.connect("toggled", self._pkg_options_persist)
        top.pack_start(self.pkg_both_cb, False, False, 0)

        self.pkg_no_prefix_cb = Gtk.CheckButton(
            label="✂️  Ajouter sans préfixe (sans pkgs. / pkgs-unstable.)")
        apply_css(self.pkg_no_prefix_cb, "h2")
        self.pkg_no_prefix_cb.set_active(False)
        self.pkg_no_prefix_cb.connect("toggled", self._pkg_options_persist)
        top.pack_start(self.pkg_no_prefix_cb, False, False, 0)

        top.pack_start(self._infobox(
            "Par défaut, les packages sont ajoutés dans <tt>default.nix</tt>. "
            "Vous pouvez indiquer un autre fichier <tt>.nix</tt> ci-dessous (existant ou "
            "à créer) : l'import correspondant sera vérifié et ajouté automatiquement "
            "dans <tt>default.nix</tt> si besoin, en respectant le regroupement par dossier.\n"
            "Avant l'ajout, le programme vérifie que le package n'existe pas déjà dans "
            "<tt>default.nix</tt>, un sous-dossier de <tt>customConfig</tt>, "
            "ou un fichier <tt>packages.nix</tt>.\n\n"
            "<b>Recherche :</b> interroge le dépôt <tt>nixpkgs</tt> via la commande "
            "<tt>nix search</tt>. "
            "La <b>première</b> recherche peut prendre 1 à 2 minutes ; "
            "les suivantes sont quasi instantanées."
        ), False, False, 0)

        tgt_row = Gtk.Box(spacing=8)
        tgt_row.pack_start(self._lbl(
            '<span foreground="#9aa8c0" size="small">Fichier cible :</span>'
        ), False, False, 0)
        self.pkg_target_entry = Gtk.Entry()
        self.pkg_target_entry.set_text(CONFIG_FILE)
        self.pkg_target_entry.set_width_chars(40)
        apply_css(self.pkg_target_entry, "entry-search")
        self.pkg_target_entry.connect("changed", self._pkg_target_upd)
        self.pkg_target_entry.connect("changed", self._pkg_target_persist)
        tgt_row.pack_start(self.pkg_target_entry, True, True, 0)
        btn_pkg_browse = Gtk.Button(label="  📁  Parcourir…")
        apply_css(btn_pkg_browse, "btn-secondary")
        btn_pkg_browse.connect("clicked", self._pkg_target_browse)
        tgt_row.pack_start(btn_pkg_browse, False, False, 0)
        top.pack_start(tgt_row, False, False, 0)

        self.pkg_target_lbl = Gtk.Label(label="")
        apply_css(self.pkg_target_lbl, "path")
        self.pkg_target_lbl.set_halign(Gtk.Align.START)
        top.pack_start(self.pkg_target_lbl, False, False, 0)
        self._pkg_target_upd()

        search_row = Gtk.Box(spacing=8)
        self.pkg_entry = Gtk.Entry()
        self.pkg_entry.set_placeholder_text("Chercher un package… ex: firefox, vlc, openrgb")
        apply_css(self.pkg_entry, "entry-search")
        self.pkg_entry.connect("activate", self._pkg_search)
        search_row.pack_start(self.pkg_entry, True, True, 0)
        self.pkg_search_btn = Gtk.Button(label="  🔍  Chercher")
        apply_css(self.pkg_search_btn, "btn-primary")
        self.pkg_search_btn.connect("clicked", self._pkg_search)
        search_row.pack_start(self.pkg_search_btn, False, False, 0)
        top.pack_start(search_row, False, False, 0)

        sr = Gtk.Box(spacing=8)
        self.pkg_spinner = Gtk.Spinner(); self.pkg_spinner.set_size_request(20, 20)
        sr.pack_start(self.pkg_spinner, False, False, 0)
        self.pkg_status = Gtk.Label(label=""); self.pkg_status.set_halign(Gtk.Align.START)
        sr.pack_start(self.pkg_status, True, True, 0)
        top.pack_start(sr, False, False, 0)
        vbox.pack_start(top, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.pkg_store = Gtk.ListStore(bool, str, str, str, str)
        self.pkg_tree  = Gtk.TreeView(model=self.pkg_store)
        self.pkg_tree.set_headers_visible(True)

        rt = Gtk.CellRendererToggle(); rt.connect("toggled", self._pkg_toggle)
        c0 = Gtk.TreeViewColumn("", rt, active=0); c0.set_fixed_width(36)
        self.pkg_tree.append_column(c0)

        for title, col_idx, stretch in [
            ("Package",     1, True),
            ("Version",     2, False),
            ("Description", 3, True),
            ("Source",      4, False),
        ]:
            r = Gtk.CellRendererText(); r.set_property("ellipsize", Pango.EllipsizeMode.END)
            if title == "Package":
                r.set_property("foreground", "#90ccff")
                r.set_property("font", "monospace 11")
                self.pkg_name_renderer = r
            if title == "Source":
                r.set_property("foreground", "#e8b840")
                self.pkg_src_renderer = r
            col = Gtk.TreeViewColumn(title, r, text=col_idx)
            col.set_resizable(True); col.set_expand(stretch)
            if not stretch: col.set_fixed_width(90)
            self.pkg_tree.append_column(col)

        scroll.add(self.pkg_tree)
        vbox.pack_start(scroll, True, True, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        bot = Gtk.Box(spacing=8); bot.set_border_width(10)
        apply_css(bot, "pad")
        self.pkg_sel_lbl = Gtk.Label(label="Aucun package sélectionné")
        apply_css(self.pkg_sel_lbl, "h2")
        bot.pack_start(self.pkg_sel_lbl, True, True, 0)
        btn_add = Gtk.Button(label="  ➕  Ajouter à systemPackages")
        apply_css(btn_add, "btn-primary")
        btn_add.connect("clicked", self._pkg_add_selected)
        bot.pack_start(btn_add, False, False, 0)
        vbox.pack_start(bot, False, False, 0)
        return vbox

    # Fichier cible (import auto)
    def _pkg_target_path(self):
        """Résout le chemin absolu du fichier cible depuis le champ de saisie.
        Chemin relatif -> résolu depuis CUSTOM_DIR. Ajoute .nix si absent."""
        txt = self.pkg_target_entry.get_text().strip() if hasattr(self, 'pkg_target_entry') else ''
        if not txt:
            return CONFIG_FILE
        if not txt.endswith('.nix'):
            txt += '.nix'
        path = txt if os.path.isabs(txt) else os.path.join(CUSTOM_DIR, txt)
        return os.path.normpath(path)

    def _pkg_target_upd(self, *_):
        target = self._pkg_target_path()
        is_root = os.path.normpath(target) == os.path.normpath(CONFIG_FILE)
        if is_root:
            self.pkg_target_lbl.set_text(f"📂  {target}  (fichier principal)")
        else:
            state = "existant" if os.path.isfile(target) else "sera créé"
            self.pkg_target_lbl.set_text(f"📂  {target}  ({state})")

    def _pkg_target_browse(self, *_):
        dlg = self._open_nix_file_chooser(
            "Choisir un fichier .nix cible", CUSTOM_DIR)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            if path:
                self.pkg_target_entry.set_text(path)
                self._pkg_target_persist()
        dlg.destroy()

    def _pkg_search(self, *_):
        query = self.pkg_entry.get_text().strip()
        if not query: return
        self.pkg_store.clear(); self.pkg_search_btn.set_sensitive(False)
        self.pkg_spinner.start()
        search_both = self.pkg_both_cb.get_active()
        if not getattr(self, '_pkg_nix_warmed', False):
            self._status(self.pkg_status,
                f"⏳  Première recherche « {query} » : index nixpkgs en cours "
                "- 1 à 2 min possibles…", "warn")
        else:
            self._status(self.pkg_status, f"🔍  Recherche de « {query} »…", "warn")
        threading.Thread(
            target=self._do_search, args=(query, search_both), daemon=True).start()

    def _warm_nix_pkg_index(self):
        """Pré-charge l'index nixpkgs en arrière-plan (accélère la 1re recherche)."""
        nix = _resolve_nix_cmd('nix') or '/run/current-system/sw/bin/nix'
        if not os.path.isfile(nix) and not shutil.which(nix):
            return
        env = _make_env()
        for ref in ('nixpkgs', 'nixpkgs-unstable'):
            try:
                subprocess.run(
                    [nix, 'search', ref, 'hello', '--json', '--limit', '1', '--quiet'],
                    capture_output=True, text=True, timeout=180, env=env)
                self._pkg_nix_warmed = True
                return
            except Exception:
                continue

    def _do_search(self, query, search_both):
        cache_key = (query.lower(), search_both)
        cached = getattr(self, '_pkg_search_cache', {}).get(cache_key)
        if cached is not None:
            GLib.idle_add(self._show_pkg_results, cached)
            return

        nix = _resolve_nix_cmd('nix') or 'nix'

        def _search_repo(nix_ref, label):
            found = []
            env = _make_env()
            for cmd in (
                [nix, 'search', nix_ref, query, '--json', '--limit', '120', '--quiet'],
                [nix, 'search', nix_ref, query, '--json', '--limit', '120'],
                [nix, 'search', nix_ref, query, '--json', '--quiet'],
                [nix, 'search', nix_ref, query, '--json'],
            ):
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       timeout=120, env=env)
                    if r.returncode == 0 and r.stdout.strip():
                        data = json.loads(r.stdout)
                        for k, v in data.items():
                            found.append((
                                k.split('.')[-1],
                                v.get('version', ''),
                                v.get('description', ''),
                                label
                            ))
                        break
                except Exception:
                    pass
            return found

        results = []
        stable_results = []
        unstable_results = []

        if search_both:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                f_stable = pool.submit(_search_repo, 'nixpkgs', 'stable')
                f_unstable = pool.submit(_search_repo, 'nixpkgs-unstable', 'unstable')
                stable_results = f_stable.result()
                unstable_results = f_unstable.result()
                if not unstable_results:
                    for ref in (
                        'github:NixOS/nixpkgs/nixos-unstable',
                        'github:NixOS/nixpkgs/nixpkgs-unstable',
                    ):
                        unstable_results = _search_repo(ref, 'unstable')
                        if unstable_results:
                            break
        else:
            stable_results = _search_repo('nixpkgs', 'stable')

        results.extend(stable_results)
        stable_by_name = {r[0]: r[1] for r in stable_results}

        if search_both:
            for pkg in unstable_results:
                name, ver = pkg[0], pkg[1]
                stable_ver = stable_by_name.get(name)
                if stable_ver is None or stable_ver != ver:
                    results.append(pkg)

        if not results:
            try:
                env = _make_env()
                r = subprocess.run(
                    ['nix-env', '-qaP', f'.*{query}.*', '--description'],
                    capture_output=True, text=True, timeout=45, env=env)
                for line in r.stdout.splitlines()[:120]:
                    parts = line.split(None, 1)
                    if parts:
                        attr = parts[0].split('.')[-1]
                        rest = parts[1] if len(parts) > 1 else ''
                        m = self._RE_PKG_VER.match(rest)
                        ver, desc = ('', rest)
                        if m: ver, desc = m.group(1), m.group(2).strip()
                        results.append((attr, ver, desc, 'stable'))
            except Exception:
                pass

        self._pkg_search_cache[cache_key] = results
        _pkg_cache_save(self._pkg_search_cache)
        self._pkg_nix_warmed = True
        GLib.idle_add(self._show_pkg_results, results)

    def _show_pkg_results(self, results):
        self.pkg_store.clear(); self.pkg_spinner.stop()
        self.pkg_search_btn.set_sensitive(True)
        if not results:
            self._status(self.pkg_status,
                "ℹ  Aucun résultat (flakes/nix-command activés ?)", "warn")
        else:
            self._status(self.pkg_status, f"✅  {len(results)} résultat(s)", "ok")
            for name, ver, desc, src in results[:300]:
                self.pkg_store.append([False, name, ver, desc, src])
        self._upd_pkg_lbl()

    def _pkg_toggle(self, w, path):
        self.pkg_store[path][0] = not self.pkg_store[path][0]
        self._upd_pkg_lbl()

    def _upd_pkg_lbl(self):
        sel = [r[1] for r in self.pkg_store if r[0]]
        self.pkg_sel_lbl.set_text(
            f"{len(sel)} sélectionné(s) : {', '.join(sel[:4])}{'…' if len(sel)>4 else ''}"
            if sel else "Aucun package sélectionné")

    def _pkg_add_selected(self, *_):
        selected = [(row[1], row[4]) for row in self.pkg_store if row[0]]
        if not selected:
            return self._status(self.pkg_status, "⚠  Cochez d'abord des packages.", "warn")

        target  = self._pkg_target_path()
        is_root = os.path.normpath(target) == os.path.normpath(CONFIG_FILE)

        if not is_root:
            try:
                real_custom = os.path.realpath(CUSTOM_DIR)
                if not os.path.normpath(target).startswith(real_custom + os.sep):
                    return self._status(self.pkg_status,
                        f"❌  Interdit hors de {CUSTOM_DIR}.", "err")
            except Exception:
                pass

        exists = os.path.isfile(target)
        if exists:
            content, err = read_file(target)
            if content is None:
                return self._status(self.pkg_status, f"❌  {err}", "err")
        else:
            content = "{ config, pkgs, lib, ... }:\n{\n\n}\n"

        lines = content.splitlines()
        new_stable, new_unstable, skipped = [], [], []

        no_prefix = self.pkg_no_prefix_cb.get_active()
        for pkg, source in selected:
            prefix = "pkgs-unstable." if source == 'unstable' else "pkgs."
            full   = pkg if no_prefix else prefix + pkg
            refs = self._find_package_references(pkg, no_prefix)
            if refs:
                skipped.append((pkg, refs))
            elif (not no_prefix) and prefix == "pkgs-unstable.":
                new_unstable.append(full)
            else:
                new_stable.append(full)

        if skipped:
            lines = []
            for item in skipped:
                pkg, refs = item
                locs = ', '.join(
                    f"{os.path.relpath(f, CUSTOM_DIR)}:{ln}" for f, ln, _ in refs[:4])
                extra = '…' if len(refs) > 4 else ''
                lines.append(f"• {pkg} -> {locs}{extra}")
            self._question_dialog(
                "Packages déjà présents",
                body_text="Ignorés (déjà déclarés dans la configuration) :\n\n"
                          + '\n'.join(lines),
                buttons=[("OK", Gtk.ResponseType.OK, "primary")])

        if not new_stable and not new_unstable:
            return self._status(self.pkg_status, "ℹ  Tous déjà présents.", "warn")

        result = self._insert_packages_into(lines, new_stable, new_unstable)
        if result is None:
            return self._status(self.pkg_status,
                "❌  Bloc systemPackages introuvable ou impossible à créer.", "err")

        new_target_content = '\n'.join(result) + '\n'

        # Cas simple : fichier cible = default.nix (comportement historique)
        if is_root:
            bid = self._backup_snapshot(
                'packages',
                f"Packages default.nix : {', '.join(new_stable + new_unstable)}",
                [CONFIG_FILE])
            ok, err = run_pkexec(new_target_content, CONFIG_FILE)
            if ok:
                _backup_commit_after(bid, [CONFIG_FILE])
                for r in self.pkg_store: r[0] = False
                self._upd_pkg_lbl()
                self._status(self.pkg_status,
                    f"✅  Ajouté : {', '.join(new_stable + new_unstable)}", "ok")
            else:
                self._status(self.pkg_status, f"❌  {err}", "err")
            return

        # Fichier cible ≠ default.nix : vérifier/ajouter l'import associé
        import_msg = ""
        cfg_new_content = None
        refs = self._find_import_references(target)
        if refs:
            f, ln, _ = refs[0]
            import_msg = f" (déjà importé via {os.path.relpath(f, CUSTOM_DIR)}:{ln})"
        else:
            cfg, cerr = read_file(CONFIG_FILE)
            if cfg is None:
                return self._status(self.pkg_status, f"❌  default.nix : {cerr}", "err")
            cfg_lines = cfg.splitlines()
            try:
                rel_import = './' + os.path.relpath(target, os.path.dirname(CONFIG_FILE))
            except Exception:
                return self._status(self.pkg_status, "❌  Chemin relatif invalide.", "err")

            new_cfg_lines, found_block = self._insert_import_grouped(cfg_lines, rel_import)
            if not found_block:
                idx = last_brace(cfg_lines)
                if idx is None:
                    return self._status(self.pkg_status,
                        "❌  Bloc imports introuvable dans default.nix.", "err")
                group = self._group_key(rel_import)
                title = self._GROUP_TITLES.get((group or '').lower(),
                                                (group or '').capitalize())
                block = ['  imports = [']
                if group:
                    block.append(f'    # {title}')
                block.append(f'    {rel_import}')
                block.append('  ];')
                new_cfg_lines = cfg_lines[:idx] + block + cfg_lines[idx:]
            cfg_new_content = '\n'.join(new_cfg_lines) + '\n'
            import_msg = " + import ajouté dans default.nix"

        bpaths = [target] if exists else []
        if cfg_new_content is not None:
            bpaths.append(CONFIG_FILE)
        bid = self._backup_snapshot(
            'packages',
            f"Packages {os.path.basename(target)} : "
            f"{', '.join(new_stable + new_unstable)}",
            bpaths)

        tmp_target = tmp_cfg = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                    prefix='/tmp/fray-pkgtgt-', delete=False) as f:
                f.write(new_target_content); tmp_target = f.name
            if cfg_new_content is not None:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                        prefix='/tmp/fray-cfg-', delete=False) as f:
                    f.write(cfg_new_content); tmp_cfg = f.name
        except Exception as e:
            return self._status(self.pkg_status, f"❌  Erreur tmp : {e}", "err")

        cmds = [f'mkdir -p "{os.path.dirname(target)}"',
                f'cp "{tmp_target}" "{target}"', f'chmod 644 "{target}"']
        if tmp_cfg:
            cmds.append(f'cp "{tmp_cfg}" "{CONFIG_FILE}"')

        ok, err = run_pkexec_script(cmds)
        for t in (tmp_target, tmp_cfg):
            try:
                if t: os.unlink(t)
            except Exception:
                pass

        if ok:
            _backup_commit_after(bid, bpaths)
            for r in self.pkg_store: r[0] = False
            self._upd_pkg_lbl()
            self._pkg_target_upd()
            self._status(self.pkg_status,
                f"✅  Ajouté dans {os.path.relpath(target, CUSTOM_DIR)} : "
                f"{', '.join(new_stable + new_unstable)}{import_msg}", "ok")
        else:
            self._status(self.pkg_status, f"❌  {err}", "err")

    def _insert_packages(self, lines, pkgs, is_unstable):
        stable_marker = "# Add your stable apps here"
        unstable_marker = "# Add your unstable apps here"
        target = unstable_marker if is_unstable else stable_marker
        in_block = False

        for i, line in enumerate(lines):
            s = line.strip()
            if self._RE_SYSPKGS.search(s):
                in_block = True
            if in_block:
                if target in s:
                    indent = self._RE_INDENT.match(line).group(1) + '  '
                    return lines[:i+1] + [indent + p for p in pkgs] + lines[i+1:]
                if s in ('];', '] ;'):
                    indent = self._RE_INDENT.match(line).group(1) + '  '
                    return lines[:i] + [indent + p for p in pkgs] + lines[i:]
                if '];' in s and s.index('];') > 0:
                    pre = line[:line.index('];')]
                    suf = line[line.index('];'):]
                    ind = self._RE_INDENT.match(line).group(1)
                    return (lines[:i] + [pre] +
                            [ind + '  ' + p for p in pkgs] +
                            [ind + suf] + lines[i+1:])
        return None

    def _insert_packages_into(self, lines, new_stable, new_unstable):
        """Généralisation de _insert_packages pour un fichier .nix quelconque :
        insère dans le bloc environment.systemPackages existant (avec ou sans
        marqueurs de commentaire), ou crée ce bloc s'il n'existe pas du tout.
        Retourne les nouvelles lignes, ou None si impossible (bloc malformé ou
        pas de '}' racine trouvable)."""
        result = list(lines)
        block_exists = bool(self._RE_SYSPKGS.search('\n'.join(lines)))

        if new_stable:
            r = self._insert_packages(result, new_stable, is_unstable=False)
            if r is not None:
                result = r
            elif block_exists:
                return None  # bloc présent mais impossible à parser
        if new_unstable:
            r = self._insert_packages(result, new_unstable, is_unstable=True)
            if r is not None:
                result = r
            elif block_exists:
                return None

        if not block_exists:
            idx = last_brace(result)
            if idx is None:
                return None
            pkgs_all = new_stable + new_unstable
            block = (['  environment.systemPackages = with pkgs; ['] +
                      [f'    {p}' for p in pkgs_all] + ['  ];'])
            result = result[:idx] + block + result[idx:]
        return result

    # ---
    # GESTION DES IMPORTS - regroupement par dossier (onglets Packages/Déplacer)
    # ---
    _GROUP_TITLES = {
        "system":   "Système",
        "gaming":   "Gaming",
        "hardware": "Hardware",
        "apps":     "Apps",
        "modules":  "Modules",
        "services": "Services",
    }
    _RE_IMPORT_ENTRY = re.compile(r'^(\.{1,2}/[\w\-./]+\.nix)\s*;?\s*$')
    _RE_NIX_REF       = re.compile(r'\.{1,2}/[\w\-./]+\.nix')

    def _group_key(self, rel_path):
        """Retourne le nom du sous-dossier immédiat d'un chemin d'import relatif
        (ex: './system/foo.nix' -> 'system'), ou None pour un fichier à la racine."""
        p = rel_path[2:] if rel_path.startswith('./') else rel_path
        parts = p.split('/')
        return parts[0].lower() if len(parts) > 1 else None

    def _group_title(self, group_key):
        if not group_key:
            return None
        return self._GROUP_TITLES.get(group_key.lower(), group_key.capitalize())

    def _matches_group_header(self, line, group_key):
        """Vrai si la ligne est un commentaire d'en-tête du groupe (ex: # Modules)."""
        if not group_key:
            return False
        s = line.strip()
        if not s.startswith('#'):
            return False
        comment = s[1:].strip().lower()
        title = (self._group_title(group_key) or group_key).lower()
        return comment == title or comment == group_key.lower()

    def _find_package_references(self, pkg_name, no_prefix=False):
        """Cherche un package dans tous les .nix de CUSTOM_DIR (default.nix,
        sous-dossiers, packages.nix, import.nix, etc.)."""
        refs = []
        patterns = [re.compile(rf'\b{re.escape(pkg_name)}\b')]
        if not no_prefix:
            patterns = [
                re.compile(rf'\bpkgs\.{re.escape(pkg_name)}\b'),
                re.compile(rf'\bpkgs-unstable\.{re.escape(pkg_name)}\b'),
            ] + patterns
        for root, dirs, files in os.walk(CUSTOM_DIR):
            dirs.sort()
            for fname in sorted(files):
                if not fname.endswith('.nix'):
                    continue
                fpath = os.path.join(root, fname)
                content, err = read_file(fpath)
                if content is None:
                    continue
                for lineno, line in enumerate(content.splitlines(), 1):
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    if any(p.search(line) for p in patterns):
                        refs.append((fpath, lineno, s))
                        break
        return refs

    def _abs_to_rel_import(self, abs_path):
        return './' + os.path.relpath(abs_path, os.path.dirname(CONFIG_FILE))

    def _imports_block_bounds(self, lines):
        start = end = None
        for i, line in enumerate(lines):
            if self._RE_IMPORTS.match(line):
                start = i
            elif start is not None and line.strip() in ('];', '] ;'):
                end = i
                break
        return start, end

    def _find_import_in_default_nix(self, target_abs_path):
        """Cherche un import uniquement dans default.nix (racine customConfig)."""
        refs = []
        target_norm = os.path.normpath(target_abs_path)
        content, err = read_file(CONFIG_FILE)
        if content is None:
            return refs
        cfg_dir = os.path.dirname(CONFIG_FILE)
        for lineno, line in enumerate(content.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            for m in self._RE_NIX_REF.finditer(line):
                candidate = os.path.normpath(os.path.join(cfg_dir, m.group(0)))
                if candidate == target_norm:
                    refs.append((CONFIG_FILE, lineno, s))
        return refs

    def _find_import_references(self, target_abs_path):
        """Cherche dans tous les .nix de CUSTOM_DIR une ligne qui importe déjà
        (de façon active, non commentée) target_abs_path.
        Retourne une liste de (fichier, num_ligne, texte_ligne)."""
        refs = []
        target_norm = os.path.normpath(target_abs_path)
        for root, dirs, files in os.walk(CUSTOM_DIR):
            dirs.sort()
            for fname in sorted(files):
                if not fname.endswith('.nix'):
                    continue
                fpath = os.path.join(root, fname)
                if os.path.normpath(fpath) == target_norm:
                    continue
                content, err = read_file(fpath)
                if content is None:
                    continue
                for lineno, line in enumerate(content.splitlines(), 1):
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    for m in self._RE_NIX_REF.finditer(line):
                        candidate = os.path.normpath(
                            os.path.join(os.path.dirname(fpath), m.group(0)))
                        if candidate == target_norm:
                            refs.append((fpath, lineno, s))
        return refs

    def _insert_import_grouped(self, cfg_lines, rel_import_path):
        """Insère `rel_import_path` (ex: './system/packages.nix') dans le premier
        bloc `imports = [ ... ];` de cfg_lines, en respectant le regroupement par
        sous-dossier (commentaire d'en-tête + entrées groupées), comme dans
        default.nix. Retourne (nouvelles_lignes, True) si un bloc imports a été
        trouvé (et modifié, ou déjà à jour), ou (cfg_lines, False) si aucun bloc
        imports n'existe (l'appelant doit alors en créer un)."""
        start = None
        for i, line in enumerate(cfg_lines):
            if self._RE_IMPORTS.match(line):
                start = i
                break
        if start is None:
            return cfg_lines, False

        end = None
        for j in range(start, len(cfg_lines)):
            if cfg_lines[j].strip() in ('];', '] ;'):
                end = j
                break
        if end is None:
            return cfg_lines, False

        rel_norm = os.path.normpath(rel_import_path)

        # Déjà présent (import actif, non commenté) ?
        for line in cfg_lines[start:end]:
            m = self._RE_IMPORT_ENTRY.match(line.strip())
            if m and os.path.normpath(m.group(1)) == rel_norm:
                return cfg_lines, True

        target_group = self._group_key(rel_import_path)
        indent = "    "
        last_idx_for_group = None
        group_header_idx = None

        for k in range(start + 1, end):
            s = cfg_lines[k].strip()
            if target_group and self._matches_group_header(cfg_lines[k], target_group):
                if group_header_idx is None:
                    group_header_idx = k
                indent = self._RE_INDENT.match(cfg_lines[k]).group(1)
            m = self._RE_IMPORT_ENTRY.match(s)
            if m:
                indent = self._RE_INDENT.match(cfg_lines[k]).group(1)
                if self._group_key(m.group(1)) == target_group:
                    last_idx_for_group = k

        new_lines = list(cfg_lines)
        if last_idx_for_group is not None:
            new_lines.insert(last_idx_for_group + 1, f"{indent}{rel_import_path}")
        elif group_header_idx is not None:
            new_lines.insert(group_header_idx + 1, f"{indent}{rel_import_path}")
        else:
            has_entries = any(cfg_lines[k].strip() for k in range(start + 1, end))
            block = [""] if has_entries else []
            if target_group:
                title = self._group_title(target_group)
                block.append(f"{indent}# {title}")
            block.append(f"{indent}{rel_import_path}")
            new_lines[end:end] = block
        return new_lines, True

    def _prune_empty_import_groups(self, lines):
        """Supprime les en-têtes de groupe (# Système…) sans import en dessous."""
        start, end = self._imports_block_bounds(lines)
        if start is None or end is None:
            return lines, False

        block = lines[start + 1:end]
        new_block = []
        changed = False
        i = 0
        while i < len(block):
            s = block[i].strip()
            if s.startswith('#'):
                j = i + 1
                has_import = False
                while j < len(block):
                    sj = block[j].strip()
                    if sj.startswith('#'):
                        break
                    if sj and self._RE_IMPORT_ENTRY.match(sj):
                        has_import = True
                        break
                    if sj:
                        break
                    j += 1
                if has_import:
                    new_block.append(block[i])
                else:
                    changed = True
                i += 1
            else:
                if s:
                    new_block.append(block[i])
                i += 1

        if not changed:
            return lines, False
        return lines[:start + 1] + new_block + lines[end:], True

    def _remove_folder_from_imports(self, lines, folder_abs):
        """Retire les imports d'un dossier supprimé puis nettoie les groupes vides."""
        folder_norm = os.path.normpath(folder_abs)
        cfg_dir = os.path.dirname(CONFIG_FILE)
        new_lines = []
        changed = False
        for line in lines:
            s = line.strip()
            m = self._RE_IMPORT_ENTRY.match(s) if s and not s.startswith('#') else None
            if m:
                candidate = os.path.normpath(os.path.join(cfg_dir, m.group(1)))
                cand_dir = os.path.dirname(candidate)
                if (cand_dir == folder_norm or
                        candidate.startswith(folder_norm + os.sep)):
                    changed = True
                    continue
            new_lines.append(line)
        if changed:
            new_lines, ch2 = self._prune_empty_import_groups(new_lines)
            changed = changed or ch2
        return new_lines, changed

    def _rewrite_import_in_default(self, old_abs, new_abs):
        """Met à jour un import uniquement dans default.nix."""
        cfg, err = read_file(CONFIG_FILE)
        if cfg is None:
            return []
        lines = cfg.splitlines()
        lines, _ = self._remove_import_line(lines, old_abs)
        lines, _ = self._prune_empty_import_groups(lines)
        try:
            rel_new = self._abs_to_rel_import(new_abs)
        except Exception:
            return []
        new_lines, _ = self._insert_import_grouped(lines, rel_new)
        return [(CONFIG_FILE, '\n'.join(new_lines) + '\n')]

    # Helper coloration syntaxique Nix - mutualisé
    _NIX_TAGS_DEF = [
        # Ordre = priorité GTK (le PREMIER = priorité la plus BASSE)
        # nix-comment doit être le plus bas : les strings le surchargent
        # nix-mlstring doit être le plus haut : il efface tout ce qui est dedans
        ("nix-comment",  {"foreground": "#7f848e", "style": Pango.Style.ITALIC}),             # gris        # commentaire
        ("nix-bracket",  {"foreground": "#abb2bf"}),                                          # gris clair  { } [ ] ( ) ;
        ("nix-operator", {"foreground": "#56b6c2"}),                                          # cyan        ++ // ? @ ...
        ("nix-number",   {"foreground": "#d19a66"}),                                          # orange      42  3.14
        ("nix-bool",     {"foreground": "#d19a66"}),                                          # orange      true false null
        ("nix-path",     {"foreground": "#56b6c2"}),                                          # cyan        ./modules/foo.nix
        ("nix-abspath",  {"foreground": "#56b6c2"}),                                          # cyan        ${FRAY_FLAKE}
        ("nix-angle",    {"foreground": "#56b6c2"}),                                          # cyan        <nixpkgs>
        ("nix-funcarg",  {"foreground": "#56b6c2"}),                                          # cyan        { lib, pkgs, ... }:
        ("nix-attrkey",  {"foreground": "#61afef"}),                                          # bleu clair  config.enable =
        ("nix-builtin",  {"foreground": "#e06c75", "weight": Pango.Weight.BOLD}),             # rouge       lib pkgs config
        ("nix-keyword",  {"foreground": "#c678dd", "weight": Pango.Weight.BOLD}),             # violet      let in with rec import
        ("nix-string",   {"foreground": "#98c379"}),                                          # vert        "hello"
        ("nix-mlstring", {"foreground": "#98c379"}),                                          # vert (max)  ''multiline''
    ]

    # Variantes thème clair : couleurs assombries pour lisibilité sur fond blanc
    _NIX_TAGS_DEF_LIGHT = [
        ("nix-comment",  {"foreground": "#4a5260", "style": Pango.Style.ITALIC}),             # gris sombre      # commentaire
        ("nix-bracket",  {"foreground": "#3d4451"}),                                          # gris foncé       { } [ ] ( ) ;
        ("nix-operator", {"foreground": "#0e6a7e"}),                                          # teal foncé       ++ // ? @ ...
        ("nix-number",   {"foreground": "#7a3900"}),                                          # brun-orange      42  3.14
        ("nix-bool",     {"foreground": "#7a3900"}),                                          # brun-orange      true false null
        ("nix-path",     {"foreground": "#0e5c80"}),                                          # bleu-teal foncé  ./modules/foo.nix
        ("nix-abspath",  {"foreground": "#0e5c80"}),                                          # bleu-teal foncé  ${FRAY_FLAKE}
        ("nix-angle",    {"foreground": "#0e5c80"}),                                          # bleu-teal foncé  <nixpkgs>
        ("nix-funcarg",  {"foreground": "#0e5c80"}),                                          # bleu-teal foncé  { lib, pkgs, ... }:
        ("nix-attrkey",  {"foreground": "#0550ae"}),                                          # bleu foncé       environment.systemPackages =
        ("nix-builtin",  {"foreground": "#a01010", "weight": Pango.Weight.BOLD}),             # rouge foncé      lib pkgs config
        ("nix-keyword",  {"foreground": "#6b21a8", "weight": Pango.Weight.BOLD}),             # violet foncé     let in with rec import
        ("nix-string",   {"foreground": "#166534"}),                                          # vert foncé       "hello"
        ("nix-mlstring", {"foreground": "#166534"}),                                          # vert foncé       ''multiline''
    ]

    def _update_nix_theme(self, theme):
        """Met à jour les couleurs des tags Nix dans tous les buffers enregistrés."""
        tags = self._NIX_TAGS_DEF_LIGHT if theme == "light" else self._NIX_TAGS_DEF
        for buf in getattr(self, '_nix_buffers', []):
            try:
                tt = buf.get_tag_table()
                for name, props in tags:
                    tag = tt.lookup(name)
                    if tag is None:
                        continue
                    if "foreground" in props:
                        tag.set_property("foreground", props["foreground"])
            except Exception:
                pass

    def _add_nix_tags(self, buf, handler_attr):
        """Crée les tags Nix + connecte le handler debounce sur le buffer."""
        # Démarre avec les couleurs du thème actif
        tags_def = (self._NIX_TAGS_DEF_LIGHT if getattr(self, 'theme', 'dark') == 'light'
                    else self._NIX_TAGS_DEF)
        for name, props in tags_def:
            buf.create_tag(name, **props)
        # Enregistre le buffer pour les mises à jour de thème ultérieures
        if not hasattr(self, '_nix_buffers'):
            self._nix_buffers = []
        self._nix_buffers.append(buf)
        hid = buf.connect(
            "changed",
            lambda b, *_: self._nix_highlight_safe(b, handler_attr)
        )
        setattr(self, handler_attr, hid)

    def _buf_set_text(self, buf, handler_attr, text):
        """Remplace le texte du buffer sans flash blanc ni déclenchement du debounce.
        Bloque le signal changed, supprime le timer de debounce, applique set_text
        et recolore immédiatement."""
        # Annule le timer debounce en attente
        timer_attr = handler_attr + '_timer'
        existing = getattr(self, timer_attr, 0)
        if existing:
            try: GLib.source_remove(existing)
            except Exception: pass
            setattr(self, timer_attr, 0)
        # Bloque le signal changed le temps du set_text
        handler_id = getattr(self, handler_attr, None)
        if handler_id:
            try: buf.handler_block(handler_id)
            except Exception: pass
        buf.set_text(text)
        # Coloration immédiate
        try:
            self._nix_highlight(buf)
        except Exception:
            pass
        # Débloque le signal changed
        if handler_id:
            try: buf.handler_unblock(handler_id)
            except Exception: pass

    # ---
    # RECHERCHE Ctrl+F - barre de recherche pour les éditeurs (onglets 3 et 5)
    # ---
    def _attach_search(self, tv):
        """Crée une barre de recherche Ctrl+F pour un TextView.
        Retourne un Gtk.Revealer à insérer AU-DESSUS de l'éditeur.
        Le raccourci Ctrl+F (et Échap pour fermer) est branché sur tv."""
        buf = tv.get_buffer()

        # Tags de surbrillance
        tt = buf.get_tag_table()
        if tt.lookup("search-hl") is None:
            buf.create_tag("search-hl",  background="#e8b840", foreground="#1a1e2e")
        if tt.lookup("search-cur") is None:
            buf.create_tag("search-cur", background="#72aef5", foreground="#1a1e2e")

        # Widgets de la barre
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.set_border_width(4)
        apply_css(bar, "search-bar")

        entry = Gtk.Entry()
        entry.set_placeholder_text("Rechercher…")
        entry.set_width_chars(26)
        apply_css(entry, "entry-search")

        lbl_count = Gtk.Label(label="")
        apply_css(lbl_count, "search-count")

        btn_prev  = Gtk.Button(label=" ▲ ")
        btn_next  = Gtk.Button(label=" ▼ ")
        btn_close = Gtk.Button(label=" ✕ ")
        for b in (btn_prev, btn_next, btn_close):
            apply_css(b, "btn-secondary")

        bar.pack_start(entry,     False, False, 0)
        bar.pack_start(btn_prev,  False, False, 0)
        bar.pack_start(btn_next,  False, False, 0)
        bar.pack_start(lbl_count, False, False, 4)
        bar.pack_end(btn_close,   False, False, 0)

        rev = Gtk.Revealer()
        rev.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        rev.set_transition_duration(150)
        rev.add(bar)

        # Logique de recherche
        def _clear_hl():
            s, e = buf.get_bounds()
            buf.remove_tag_by_name("search-hl",  s, e)
            buf.remove_tag_by_name("search-cur", s, e)

        # Index de la correspondance courante (persistant entre appels)
        _state = {"matches": [], "cur": 0}

        def _rebuild_matches(text):
            """Trouve toutes les occurrences et surligne en jaune."""
            _clear_hl()
            _state["matches"] = []
            if not text:
                lbl_count.set_text(""); return
            it = buf.get_start_iter()
            while True:
                res = it.forward_search(
                    text, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
                if res is None: break
                ms, me = res
                _state["matches"].append((ms.get_offset(), me.get_offset()))
                buf.apply_tag_by_name("search-hl", ms, me)
                it = me

        def _highlight_cur():
            """Colore la correspondance courante en bleu et scrolle vers elle."""
            matches = _state["matches"]
            if not matches:
                lbl_count.set_text("0 résultat"); return
            idx = _state["cur"] % len(matches)
            _state["cur"] = idx
            s_off, e_off = matches[idx]
            cur_s = buf.get_iter_at_offset(s_off)
            cur_e = buf.get_iter_at_offset(e_off)
            # Repasser en jaune toutes, puis bleue la courante
            for so, eo in matches:
                ts = buf.get_iter_at_offset(so)
                te = buf.get_iter_at_offset(eo)
                buf.remove_tag_by_name("search-cur", ts, te)
                buf.apply_tag_by_name("search-hl",  ts, te)
            buf.remove_tag_by_name("search-hl",  cur_s, cur_e)
            buf.apply_tag_by_name("search-cur", cur_s, cur_e)
            buf.place_cursor(cur_s)
            tv.scroll_to_mark(buf.get_insert(), 0.08, True, 0.5, 0.4)
            lbl_count.set_text(f"{idx + 1} / {len(matches)}")

        def _search_from_cursor(forward=True):
            matches = _state["matches"]
            if not matches: return
            cur_off = buf.get_iter_at_mark(buf.get_insert()).get_offset()
            if forward:
                idx = next(
                    (i for i, (s, _) in enumerate(matches) if s > cur_off),
                    0)
            else:
                idx = next(
                    (i for i, (s, _) in reversed(list(enumerate(matches)))
                     if s < cur_off),
                    len(matches) - 1)
            _state["cur"] = idx
            _highlight_cur()

        def _on_entry_changed(*_):
            _rebuild_matches(entry.get_text())
            _state["cur"] = 0
            _highlight_cur()

        def _on_next(*_): _search_from_cursor(forward=True)
        def _on_prev(*_): _search_from_cursor(forward=False)

        def _close(*_):
            rev.set_reveal_child(False)
            _clear_hl()
            lbl_count.set_text("")
            tv.grab_focus()

        def _on_entry_key(w, event):
            if event.keyval == Gdk.KEY_Return:
                _on_next(); return True
            if event.keyval == Gdk.KEY_Escape:
                _close();   return True
            return False

        def _on_tv_key(w, event):
            ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
            if ctrl and event.keyval in (ord('f'), ord('F')):
                rev.set_reveal_child(True)
                entry.grab_focus()
                sel = buf.get_selection_bounds()
                if sel:
                    entry.set_text(buf.get_text(sel[0], sel[1], False))
                    entry.select_region(0, -1)
                return True
            if event.keyval == Gdk.KEY_Escape and rev.get_reveal_child():
                _close(); return True
            return False

        entry.connect("changed",       _on_entry_changed)
        entry.connect("key-press-event", _on_entry_key)
        btn_next.connect("clicked",   _on_next)
        btn_prev.connect("clicked",   _on_prev)
        btn_close.connect("clicked",  _close)
        tv.connect("key-press-event", _on_tv_key)

        return rev

    # ---
    # UNDO / REDO Ctrl+Z / Ctrl+Shift+Z - onglets 1, 3 et 5
    # ---
    def _attach_undo(self, tv, handler_attr=None):
        """Branche Ctrl+Z (undo) et Ctrl+Shift+Z (redo) sur un Gtk.TextView.
        Retourne une fonction reset() à appeler lors du chargement d'un nouveau fichier."""
        buf         = tv.get_buffer()
        stack_undo  = []
        stack_redo  = []
        _applying   = [False]

        def _snap():
            text   = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
            cursor = buf.get_iter_at_mark(buf.get_insert()).get_offset()
            return (text, cursor)

        def _restore(snap):
            _applying[0] = True
            if handler_attr:
                self._buf_set_text(buf, handler_attr, snap[0])
            else:
                buf.set_text(snap[0])
            buf.place_cursor(buf.get_iter_at_offset(
                min(snap[1], buf.get_char_count())))
            _applying[0] = False

        def _on_changed(*_):
            if _applying[0]: return
            snap = _snap()
            if stack_undo and stack_undo[-1][0] == snap[0]: return
            stack_undo.append(snap)
            stack_redo.clear()
            if len(stack_undo) > 200:
                stack_undo.pop(0)

        def _on_key(w, event):
            ctrl  = event.state & Gdk.ModifierType.CONTROL_MASK
            shift = event.state & Gdk.ModifierType.SHIFT_MASK
            if ctrl and not shift and event.keyval in (ord('z'), ord('Z')):
                if len(stack_undo) > 1:
                    stack_redo.append(stack_undo.pop())
                    _restore(stack_undo[-1])
                return True
            if ctrl and shift and event.keyval in (ord('z'), ord('Z')):
                if stack_redo:
                    snap = stack_redo.pop()
                    stack_undo.append(snap)
                    _restore(snap)
                return True
            return False

        def reset():
            stack_undo.clear()
            stack_redo.clear()
            stack_undo.append(_snap())

        stack_undo.append(_snap())        # état initial
        buf.connect("changed", _on_changed)
        tv.connect("key-press-event", _on_key)
        return reset

    # ---
    # ONGLET 3 - Nouveau .nix
    # ---
    def tab_new_nix(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        apply_css(top, "pad")
        top.pack_start(self._h1("Créer un nouveau fichier .nix"), False, False, 0)

        top.pack_start(self._infobox(
            '<b>Module NixOS</b> - sera importé automatiquement dans '
            f'<tt>{CONFIG_FILE}</tt> uniquement '
            '(regroupement par dossier : Système, Gaming, Apps…). '
            f'Limité à <tt>{CUSTOM_DIR}/</tt> et ses sous-dossiers.\n'
            'Seul <tt>default.nix</tt> à la racine de <tt>customConfig</tt> '
            'est consulté et modifié pour les imports.'
        ), False, False, 0)

        r1 = Gtk.Box(spacing=8)
        r1.pack_start(self._lbl(
            '<span foreground="#9aa8c0" size="small">Nom du fichier :</span>'
        ), False, False, 0)
        self.nix_name = Gtk.Entry()
        self.nix_name.set_placeholder_text("mes-packages.nix")
        self.nix_name.set_width_chars(28); apply_css(self.nix_name, "entry")
        self.nix_name.connect("changed", self._nix_upd)
        r1.pack_start(self.nix_name, False, False, 0)
        top.pack_start(r1, False, False, 0)

        r2 = Gtk.Box(spacing=8)
        r2.pack_start(self._lbl(
            f'<span foreground="#9aa8c0" size="small">'
            f'Sous-dossier <tt>(dans {CUSTOM_DIR}/)</tt> :</span>'
        ), False, False, 0)
        self.nix_sub = Gtk.Entry()
        self.nix_sub.set_placeholder_text("laisser vide pour la racine")
        self.nix_sub.set_width_chars(28); apply_css(self.nix_sub, "entry")
        self.nix_sub.connect("changed", self._nix_upd)
        r2.pack_start(self.nix_sub, False, False, 0)
        top.pack_start(r2, False, False, 0)

        self.nix_path_lbl = Gtk.Label(label="")
        apply_css(self.nix_path_lbl, "path")
        self.nix_path_lbl.set_halign(Gtk.Align.START)
        top.pack_start(self.nix_path_lbl, False, False, 0)
        self._nix_upd()

        r3 = Gtk.Box(spacing=8)
        btn_tpl = Gtk.Button(label="  📋  Template")
        apply_css(btn_tpl, "btn-secondary")
        btn_tpl.connect("clicked", self._nix_template)
        r3.pack_start(btn_tpl, False, False, 0)
        btn_cr = Gtk.Button(label="  💾  Créer + ajouter l'import")
        apply_css(btn_cr, "btn-primary")
        btn_cr.connect("clicked", self._nix_create)
        r3.pack_start(btn_cr, False, False, 0)
        top.pack_start(r3, False, False, 0)

        self.nix_status = Gtk.Label(label="")
        self.nix_status.set_halign(Gtk.Align.START)
        top.pack_start(self.nix_status, False, False, 0)
        paned.pack1(top, resize=False, shrink=False)

        self.nix_tv = Gtk.TextView(); self.nix_tv.set_monospace(True)
        self.nix_tv.set_left_margin(14); self.nix_tv.set_top_margin(10)
        self.nix_tv.set_right_margin(14); self.nix_tv.set_bottom_margin(10)
        self.nix_tv.set_wrap_mode(Gtk.WrapMode.NONE)
        self._add_nix_tags(self.nix_tv.get_buffer(), "_hl_handler_nix")
        self._buf_set_text(self.nix_tv.get_buffer(), "_hl_handler_nix", self._tpl_vide())
        self._attach_undo(self.nix_tv, "_hl_handler_nix")
        search_rev_nix = self._attach_search(self.nix_tv)
        editor_box = self._make_editor_with_lineno(self.nix_tv)
        editor_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        editor_outer.pack_start(search_rev_nix, False, False, 0)
        editor_outer.pack_start(editor_box, True, True, 0)
        paned.pack2(editor_outer, resize=True, shrink=True)
        paned.set_position(195)
        return paned

    def _nix_upd(self, *_):
        sub = self.nix_sub.get_text().strip().strip('/')
        name = self.nix_name.get_text().strip()
        if name and not name.endswith('.nix'): name += '.nix'
        base = f"{CUSTOM_DIR}/{sub}" if sub else CUSTOM_DIR
        path = f"{base}/{name}" if name else base + '/'
        self.nix_path_lbl.set_text(f"📂  {path}")
        return base, name, path

    def _nix_template(self, *_):
        items = [
            ("Module vide",               "Squelette minimal.",                self._tpl_vide()),
            ("Packages supplémentaires",  "systemPackages.",                   self._tpl_packages()),
            ("Configuration réseau",      "Hostname, pare-feu, NetworkManager.", self._tpl_reseau()),
            ("Services système",          "SSH, impression, etc.",             self._tpl_services()),
        ]
        dlg = Gtk.Dialog(title="", transient_for=self, modal=True, destroy_with_parent=True)
        self._style_dialog_csd(dlg, "Choisir un template")
        dlg.add_button("Annuler",   Gtk.ResponseType.CANCEL)
        dlg.add_button("Appliquer", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        dlg.set_default_size(420, 240)
        ca = dlg.get_content_area(); ca.set_spacing(6)
        ca.pack_start(self._lbl(
            '<span size="small" foreground="#9aa8c0">Sélectionnez puis <b>Appliquer</b> :</span>'
        ), False, False, 8)
        lb = Gtk.ListBox(); lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        for name, desc, _ in items:
            row = Gtk.ListBoxRow()
            vb  = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            vb.set_margin_start(10); vb.set_margin_top(6); vb.set_margin_bottom(6)
            l_name = Gtk.Label(xalign=0)
            l_name.set_markup(f'<b>{GLib.markup_escape_text(name)}</b>')
            l_desc = Gtk.Label(label=desc, xalign=0); apply_css(l_desc, "h2")
            vb.pack_start(l_name, False, False, 0)
            vb.pack_start(l_desc, False, False, 0)
            row.add(vb); lb.add(row)
        lb.connect("row-activated", lambda lb, row: dlg.response(Gtk.ResponseType.OK))
        lb.select_row(lb.get_row_at_index(0))
        ca.pack_start(lb, True, True, 0)
        self._apply_dialog_theme(dlg)
        resp = dlg.run()
        if resp == Gtk.ResponseType.OK:
            row = lb.get_selected_row()
            if row:
                _, _, content = items[row.get_index()]
                self._buf_set_text(self.nix_tv.get_buffer(), "_hl_handler_nix", content)
        dlg.destroy()

    def _tpl_vide(self):
        return "{ config, pkgs, lib, ... }:\n{\n  # Votre configuration ici\n}\n"

    def _tpl_packages(self):
        return ("{ config, pkgs, lib, ... }:\n{\n"
                "  environment.systemPackages = with pkgs; [\n"
                "    # Ajoutez vos packages ici\n    firefox\n    vlc\n  ];\n}\n")

    def _tpl_reseau(self):
        return ('{ config, pkgs, lib, ... }:\n{\n'
                '  networking = {\n'
                '    hostName = lib.mkForce "Fray";\n'
                '    networkmanager.enable = true;\n'
                '    firewall = {\n      enable = true;\n'
                '      allowedTCPPorts = [ 80 443 ];\n    };\n  };\n}\n')

    def _tpl_services(self):
        return ('{ config, pkgs, lib, ... }:\n{\n'
                '  services = {\n    # Exemple : activer SSH\n'
                '    openssh.enable = false;\n'
                '    # Exemple : impression\n    # printing.enable = true;\n  };\n}\n')

    def _nix_create(self, *_):
        base, name, path = self._nix_upd()
        if not name:
            return self._status(self.nix_status, "⚠  Entrez un nom de fichier.", "warn")
        try:
            real_custom = os.path.realpath(CUSTOM_DIR)
            real_dest = os.path.realpath(os.path.join(base, name))
            if not real_dest.startswith(real_custom + os.sep) and real_dest != real_custom:
                return self._status(self.nix_status, f"❌  Interdit hors de {CUSTOM_DIR}.", "err")
        except Exception:
            pass

        if os.path.isfile(path):
            return self._status(self.nix_status,
                f"❌  Le fichier existe déjà : {path}", "err")

        buf = self.nix_tv.get_buffer()
        file_content = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

        cfg, cerr = read_file(CONFIG_FILE)
        if cfg is None:
            return self._status(self.nix_status, f"❌  {cerr}", "err")

        cfg_lines = cfg.splitlines()
        try:
            rel = self._abs_to_rel_import(path)
        except Exception:
            return self._status(self.nix_status, "❌  Chemin relatif invalide.", "err")

        import_refs = self._find_import_in_default_nix(path)
        import_msg = ""
        cfg_new_content = None
        modified = False

        if import_refs:
            _, ln, _ = import_refs[0]
            import_msg = f" (import déjà présent dans default.nix:{ln})"
        else:
            new_cfg_lines, found_block = self._insert_import_grouped(cfg_lines, rel)
            if found_block:
                cfg_lines = new_cfg_lines
                modified = True
            else:
                idx = last_brace(cfg_lines)
                if idx is None:
                    return self._status(self.nix_status,
                        "❌  Bloc imports introuvable dans default.nix.", "err")
                group = self._group_key(rel)
                title = self._GROUP_TITLES.get((group or '').lower(),
                                                (group or '').capitalize())
                block = ['  imports = [']
                if group:
                    block.append(f'    # {title}')
                block.append(f'    {rel}')
                block.append('  ];')
                cfg_lines = cfg_lines[:idx] + block + cfg_lines[idx:]
                modified = True
            if modified:
                cfg_new_content = '\n'.join(cfg_lines) + '\n'
                import_msg = " + import ajouté dans default.nix"

        tmp_nix = tmp_cfg = None
        bid = None
        if cfg_new_content is not None:
            bid = self._backup_snapshot('create', f"Création {name}", [CONFIG_FILE])
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                    prefix='/tmp/fray-new-', delete=False) as f:
                f.write(file_content); tmp_nix = f.name
            if cfg_new_content is not None:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                        prefix='/tmp/fray-cfg-', delete=False) as f:
                    f.write(cfg_new_content); tmp_cfg = f.name
        except Exception as e:
            return self._status(self.nix_status, f"❌  Erreur tmp : {e}", "err")

        cmds = [f'mkdir -p "{base}"', f'cp "{tmp_nix}" "{path}"', f'chmod 644 "{path}"']
        if tmp_cfg:
            cmds.append(f'cp "{tmp_cfg}" "{CONFIG_FILE}"')

        ok, err = run_pkexec_script(cmds)
        for t in (tmp_nix, tmp_cfg):
            try:
                if t: os.unlink(t)
            except Exception:
                pass
        if ok:
            if bid:
                _backup_commit_after(bid, [CONFIG_FILE])
            self._status(self.nix_status,
                f"✅  {name} créé{import_msg}", "ok")
        else:
            self._status(self.nix_status, f"❌  {err}", "err")

    # ---
    # ONGLET 4 - Déplacer un fichier .nix
    # ---
    def tab_move(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        apply_css(vbox, "bg")

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apply_css(top, "pad")
        top.pack_start(self._h1("Déplacer un fichier .nix"), False, False, 0)

        top.pack_start(self._infobox(
            f'<b>Déplacement vers</b> <tt>{CUSTOM_DIR}/</tt>\n'
            '• Cochez <b>Téléchargements</b> et/ou <b>customConfig</b> pour lister '
            'les fichiers .nix disponibles.\n'
            '• Utilisez aussi les boutons pour parcourir manuellement.\n'
            'Les imports sont mis à jour uniquement dans <tt>default.nix</tt> '
            '(regroupement par dossier).'
        ), False, False, 0)

        filter_row = Gtk.Box(spacing=16)
        self.move_cb_downloads = Gtk.CheckButton(label="📥  Téléchargements")
        apply_css(self.move_cb_downloads, "h2")
        self.move_cb_downloads.set_active(True)
        self.move_cb_downloads.connect("toggled", self._move_filter_changed)
        filter_row.pack_start(self.move_cb_downloads, False, False, 0)
        self.move_cb_custom = Gtk.CheckButton(label="📁  customConfig")
        apply_css(self.move_cb_custom, "h2")
        self.move_cb_custom.set_active(True)
        self.move_cb_custom.connect("toggled", self._move_filter_changed)
        filter_row.pack_start(self.move_cb_custom, False, False, 0)
        top.pack_start(filter_row, False, False, 0)

        src_row = Gtk.Box(spacing=8)
        src_row.pack_start(self._lbl(
            '<span foreground="#9aa8c0" size="small">Fichier source :</span>'
        ), False, False, 0)
        self.move_src_entry = Gtk.Entry()
        self.move_src_entry.set_width_chars(36)
        apply_css(self.move_src_entry, "entry-search")
        src_row.pack_start(self.move_src_entry, True, True, 0)
        btn_src_dl = Gtk.Button(label="  📥  Téléchargements")
        apply_css(btn_src_dl, "btn-secondary")
        btn_src_dl.connect("clicked", self._move_browse_downloads)
        src_row.pack_start(btn_src_dl, False, False, 0)
        btn_src_cc = Gtk.Button(label="  📁  customConfig")
        apply_css(btn_src_cc, "btn-secondary")
        btn_src_cc.connect("clicked", self._move_browse_custom)
        src_row.pack_start(btn_src_cc, False, False, 0)
        top.pack_start(src_row, False, False, 0)

        dst_row = Gtk.Box(spacing=8)
        dst_row.pack_start(self._lbl(
            f'<span foreground="#9aa8c0" size="small">'
            f'Sous-dossier destination <tt>(dans {CUSTOM_DIR}/)</tt> :</span>'
        ), False, False, 0)
        self.move_dst_sub = Gtk.Entry()
        self.move_dst_sub.set_placeholder_text("ex: system, gaming, apps - vide = racine")
        self.move_dst_sub.set_width_chars(28)
        apply_css(self.move_dst_sub, "entry")
        self.move_dst_sub.connect("changed", self._move_upd_path)
        dst_row.pack_start(self.move_dst_sub, False, False, 0)
        top.pack_start(dst_row, False, False, 0)

        self.move_path_lbl = Gtk.Label(label="")
        apply_css(self.move_path_lbl, "path")
        self.move_path_lbl.set_halign(Gtk.Align.START)
        top.pack_start(self.move_path_lbl, False, False, 0)

        btn_row = Gtk.Box(spacing=8)
        btn_refresh = Gtk.Button(label="  🔄  Actualiser la liste")
        apply_css(btn_refresh, "btn-secondary")
        btn_refresh.connect("clicked", lambda *_: self._move_refresh())
        btn_row.pack_start(btn_refresh, False, False, 0)
        btn_go = Gtk.Button(label="  📂  Déplacer")
        apply_css(btn_go, "btn-primary")
        btn_go.connect("clicked", self._move_execute)
        btn_row.pack_start(btn_go, False, False, 0)
        top.pack_start(btn_row, False, False, 0)

        self.move_status = Gtk.Label(label="")
        self.move_status.set_halign(Gtk.Align.START)
        top.pack_start(self.move_status, False, False, 0)
        vbox.pack_start(top, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(120)

        self.move_store = Gtk.ListStore(bool, str, str, str)
        self.move_tree = Gtk.TreeView(model=self.move_store)
        rt = Gtk.CellRendererToggle()
        rt.connect("toggled", self._move_toggle)
        c0 = Gtk.TreeViewColumn("", rt, active=0)
        c0.set_fixed_width(36)
        self.move_tree.append_column(c0)
        r1 = Gtk.CellRendererText()
        r1.set_property("ellipsize", Pango.EllipsizeMode.END)
        c1 = Gtk.TreeViewColumn("Fichier .nix", r1, text=1)
        c1.set_expand(True)
        self.move_tree.append_column(c1)
        r2 = Gtk.CellRendererText()
        r2.set_property("foreground", "#e8b840")
        c2 = Gtk.TreeViewColumn("Source", r2, text=3)
        c2.set_fixed_width(130)
        self.move_tree.append_column(c2)
        scroll.add(self.move_tree)
        vbox.pack_start(scroll, True, True, 0)

        self.move_src_entry.connect("changed", self._move_upd_path)
        self._restore_move_filters()
        GLib.idle_add(self._move_refresh)
        return vbox

    def _restore_move_filters(self):
        if not hasattr(self, 'move_cb_downloads'):
            return
        settings = _load_settings()
        self._move_restoring = True
        try:
            self.move_cb_downloads.set_active(
                settings.get('move_show_downloads', True))
            self.move_cb_custom.set_active(
                settings.get('move_show_custom', True))
        finally:
            self._move_restoring = False

    def _move_filter_changed(self, *_):
        if getattr(self, '_move_restoring', False):
            return
        if hasattr(self, 'move_cb_downloads'):
            self._persist_setting(
                'move_show_downloads', self.move_cb_downloads.get_active())
            self._persist_setting(
                'move_show_custom', self.move_cb_custom.get_active())
        self._move_refresh()

    def _move_upd_path(self, *_):
        src = self.move_src_entry.get_text().strip()
        sub = self.move_dst_sub.get_text().strip().strip('/')
        if src:
            name = os.path.basename(src)
            if name and not name.endswith('.nix'):
                name += '.nix'
            base = os.path.join(CUSTOM_DIR, sub) if sub else CUSTOM_DIR
            dest = os.path.join(base, name) if name else base + '/'
            self.move_path_lbl.set_text(f"📂  ->  {dest}")
        else:
            self.move_path_lbl.set_text("")

    def _move_browse_downloads(self, *_):
        start = DOWNLOADS_DIR if os.path.isdir(DOWNLOADS_DIR) else os.path.expanduser("~")
        dlg = self._open_nix_file_chooser(
            "Choisir un fichier .nix (Téléchargements)", start)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            if path:
                self.move_src_entry.set_text(path)
        dlg.destroy()

    def _move_browse_custom(self, *_):
        dlg = self._open_nix_file_chooser(
            "Choisir un fichier .nix dans customConfig", CUSTOM_DIR)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            if path:
                self.move_src_entry.set_text(path)
        dlg.destroy()

    def _move_refresh(self):
        self.move_store.clear()
        count = 0
        show_dl = getattr(self, 'move_cb_downloads', None)
        show_cc = getattr(self, 'move_cb_custom', None)
        include_dl = show_dl.get_active() if show_dl else True
        include_cc = show_cc.get_active() if show_cc else True
        try:
            if include_cc:
                real_custom = os.path.realpath(CUSTOM_DIR)
                for root, dirs, files in os.walk(CUSTOM_DIR):
                    dirs.sort()
                    for fname in sorted(files):
                        if not fname.endswith('.nix'):
                            continue
                        full = os.path.join(root, fname)
                        if (os.path.basename(full) == 'default.nix' and
                                os.path.realpath(os.path.dirname(full)) == real_custom):
                            continue
                        rel = os.path.relpath(full, CUSTOM_DIR)
                        self.move_store.append(
                            [False, f"  📄  {rel}", full, "customConfig"])
                        count += 1

            if include_dl and os.path.isdir(DOWNLOADS_DIR):
                for fname in sorted(os.listdir(DOWNLOADS_DIR)):
                    if not fname.endswith('.nix'):
                        continue
                    full = os.path.join(DOWNLOADS_DIR, fname)
                    if os.path.isfile(full):
                        self.move_store.append(
                            [False, f"  📥  {fname}", full, "Téléchargements"])
                        count += 1

            parts = []
            if include_dl:
                parts.append("Téléchargements")
            if include_cc:
                parts.append("customConfig")
            src_lbl = " + ".join(parts) if parts else "aucune source"
            self._status(self.move_status,
                f"ℹ  {count} fichier(s) .nix ({src_lbl}).", "ok")
        except Exception as e:
            self._status(self.move_status, f"❌  {e}", "err")

    def _move_toggle(self, w, path):
        self.move_store[path][0] = not self.move_store[path][0]
        for i, row in enumerate(self.move_store):
            if i != int(path) and row[0]:
                row[0] = False
        if self.move_store[path][0]:
            self.move_src_entry.set_text(self.move_store[path][2])

    def _move_execute(self, *_):
        src = self.move_src_entry.get_text().strip()
        if not src:
            return self._status(self.move_status, "⚠  Indiquez un fichier source.", "warn")
        if not os.path.isfile(src):
            return self._status(self.move_status, f"❌  Fichier introuvable : {src}", "err")
        if not src.endswith('.nix'):
            return self._status(self.move_status, "❌  Seuls les fichiers .nix sont acceptés.", "err")

        sub = self.move_dst_sub.get_text().strip().strip('/')
        name = os.path.basename(src)
        dest_dir = os.path.join(CUSTOM_DIR, sub) if sub else CUSTOM_DIR
        dest = os.path.normpath(os.path.join(dest_dir, name))

        try:
            real_custom = os.path.realpath(CUSTOM_DIR)
            real_dest = os.path.realpath(dest)
            if not real_dest.startswith(real_custom + os.sep):
                return self._status(self.move_status,
                    f"❌  Destination hors de {CUSTOM_DIR}.", "err")
        except Exception as e:
            return self._status(self.move_status, f"❌  {e}", "err")

        src_norm = os.path.normpath(src)
        if src_norm == dest:
            return self._status(self.move_status, "ℹ  Source et destination identiques.", "warn")
        if os.path.isfile(dest):
            return self._status(self.move_status,
                f"❌  Le fichier destination existe déjà : {dest}", "err")

        from_custom = src_norm.startswith(os.path.normpath(CUSTOM_DIR) + os.sep)
        import_updates = []
        add_import = False

        if from_custom:
            import_updates = self._rewrite_import_in_default(src, dest)
        else:
            refs = self._find_import_in_default_nix(dest)
            if refs:
                _, ln, _ = refs[0]
                return self._status(self.move_status,
                    f"❌  Import déjà présent dans default.nix:{ln}.", "err")
            cfg, cerr = read_file(CONFIG_FILE)
            if cfg is None:
                return self._status(self.move_status, f"❌  {cerr}", "err")
            cfg_lines = cfg.splitlines()
            try:
                rel = self._abs_to_rel_import(dest)
            except Exception:
                return self._status(self.move_status, "❌  Chemin relatif invalide.", "err")
            new_cfg_lines, found_block = self._insert_import_grouped(cfg_lines, rel)
            if not found_block:
                idx = last_brace(cfg_lines)
                if idx is None:
                    return self._status(self.move_status,
                        "❌  Bloc imports introuvable dans default.nix.", "err")
                group = self._group_key(rel)
                title = self._GROUP_TITLES.get((group or '').lower(),
                                                (group or '').capitalize())
                block = ['  imports = [']
                if group:
                    block.append(f'    # {title}')
                block.append(f'    {rel}')
                block.append('  ];')
                new_cfg_lines = cfg_lines[:idx] + block + cfg_lines[idx:]
            import_updates.append((CONFIG_FILE, '\n'.join(new_cfg_lines) + '\n'))
            add_import = True

        if not self._confirm_dialog(
                "Confirmer le déplacement ?",
                secondary_markup=(
                    f"<b>Source :</b> <tt>{GLib.markup_escape_text(src)}</tt>\n"
                    f"<b>Destination :</b> <tt>{GLib.markup_escape_text(dest)}</tt>"),
                ok_label="Valider"):
            return

        bpaths = [src]
        if import_updates:
            bpaths.append(CONFIG_FILE)
        bid = self._backup_snapshot(
            'move',
            f"Déplacement {os.path.basename(src)}",
            bpaths)

        tmp_files = []
        cmds = [f'mkdir -p "{dest_dir}"']
        try:
            if from_custom:
                cmds.append(f'mv "{src}" "{dest}"')
            else:
                cmds.append(f'cp "{src}" "{dest}"')
                cmds.append(f'chmod 644 "{dest}"')
            for fpath, content in import_updates:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                        prefix='/tmp/fray-move-', delete=False) as f:
                    f.write(content)
                    tmp_files.append((f.name, fpath))
            for tmp, final in tmp_files:
                cmds.append(f'cp "{tmp}" "{final}"')
        except Exception as e:
            for tmp, _ in tmp_files:
                try: os.unlink(tmp)
                except OSError: pass
            return self._status(self.move_status, f"❌  Erreur tmp : {e}", "err")

        ok, err = run_pkexec_script(cmds)
        for tmp, _ in tmp_files:
            try: os.unlink(tmp)
            except OSError: pass

        if ok:
            _backup_commit_after(bid, bpaths)
            msg = f"✅  Déplacé vers {os.path.relpath(dest, CUSTOM_DIR)}"
            if add_import or import_updates:
                msg += " + imports mis à jour"
            self._status(self.move_status, msg, "ok")
            self.move_src_entry.set_text("")
            self._move_refresh()
        else:
            self._status(self.move_status, f"❌  {err}", "err")

    # ---
    # ONGLET 5 - Supprimer un fichier .nix
    # ---
    def tab_delete(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        apply_css(vbox, "bg")

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apply_css(top, "pad")
        top.pack_start(self._h1("Supprimer un fichier .nix"), False, False, 0)

        top.pack_start(self._infobox(
            f'<b>Suppression dans</b> <tt>{CUSTOM_DIR}</tt>\n'
            '• <tt>default.nix</tt> est protégé - impossible à supprimer.\n'
            '• Les imports associés dans <tt>default.nix</tt> sont retirés automatiquement.\n'
            '• La suppression d\'un dossier retire aussi le groupe correspondant '
            '(# Système, # Gaming…) s\'il ne reste plus d\'import.'
        ), False, False, 0)

        btn_row = Gtk.Box(spacing=8)
        btn_refresh = Gtk.Button(label="  🔄  Actualiser la liste")
        apply_css(btn_refresh, "btn-secondary")
        btn_refresh.connect("clicked", lambda *_: self._del_refresh())
        btn_row.pack_start(btn_refresh, False, False, 0)
        top.pack_start(btn_row, False, False, 0)

        del_search_row = Gtk.Box(spacing=8)
        self.del_search = Gtk.Entry()
        self.del_search.set_placeholder_text("Filtrer les fichiers .nix…")
        apply_css(self.del_search, "entry-search")
        self.del_search.connect("changed", self._del_filter)
        del_search_row.pack_start(self.del_search, True, True, 0)
        top.pack_start(del_search_row, False, False, 0)

        self.del_status = Gtk.Label(label="")
        self.del_status.set_halign(Gtk.Align.START)
        top.pack_start(self.del_status, False, False, 0)
        vbox.pack_start(top, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.del_store = Gtk.ListStore(bool, str, str, str)
        self.del_tree = Gtk.TreeView(model=self.del_store)

        rt = Gtk.CellRendererToggle(); rt.connect("toggled", self._del_toggle)
        c0 = Gtk.TreeViewColumn("", rt, active=0); c0.set_fixed_width(36)
        self.del_tree.append_column(c0)

        r1 = Gtk.CellRendererText(); r1.set_property("ellipsize", Pango.EllipsizeMode.END)
        c1 = Gtk.TreeViewColumn("Fichier / Dossier", r1, text=1); c1.set_expand(True)
        self.del_tree.append_column(c1)

        r2 = Gtk.CellRendererText(); r2.set_property("foreground", "#e8b840")
        self.del_type_renderer = r2
        c2 = Gtk.TreeViewColumn("Type", r2, text=3); c2.set_fixed_width(80)
        self.del_tree.append_column(c2)

        scroll.add(self.del_tree)
        vbox.pack_start(scroll, True, True, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        bot = Gtk.Box(spacing=8); bot.set_border_width(10)
        apply_css(bot, "pad")
        self.del_sel_lbl = Gtk.Label(label="Aucun élément sélectionné")
        apply_css(self.del_sel_lbl, "h2")
        bot.pack_start(self.del_sel_lbl, True, True, 0)
        btn_del = Gtk.Button(label="  🗑  Supprimer la sélection")
        apply_css(btn_del, "btn-warn")
        btn_del.connect("clicked", self._del_execute)
        bot.pack_start(btn_del, False, False, 0)
        vbox.pack_start(bot, False, False, 0)

        GLib.idle_add(self._del_refresh)
        return vbox

    def _del_filter(self, *_):
        q = self.del_search.get_text().strip().lower()
        self.del_store.clear()
        shown = 0
        for entry in getattr(self, '_del_all_entries', []):
            if not q or q in entry[1].lower():
                self.del_store.append(list(entry))
                if entry[3] == "fichier":
                    shown += 1
        if q:
            self._status(self.del_status,
                         f"ℹ  {shown} fichier(s) correspondant(s).", "ok")

    def _del_refresh(self):
        self._del_all_entries = []
        self.del_store.clear()
        try:
            real_custom = os.path.realpath(CUSTOM_DIR)
            entries = []
            for root, dirs, files in os.walk(CUSTOM_DIR):
                dirs.sort()
                for fname in sorted(files):
                    if not fname.endswith('.nix'):
                        continue
                    full = os.path.join(root, fname)
                    real_full = os.path.realpath(full)
                    if (os.path.basename(full) == 'default.nix' and
                            os.path.dirname(real_full) == real_custom):
                        continue
                    rel = os.path.relpath(full, CUSTOM_DIR)
                    entries.append((False, f"  📄  {rel}", full, "fichier"))
                if root != CUSTOM_DIR:
                    nix_files = [f for f in files if f.endswith('.nix')]
                    if not nix_files and not dirs:
                        rel_dir = os.path.relpath(root, CUSTOM_DIR)
                        entries.append((False, f"  📁  {rel_dir}/", root, "dossier vide"))
            self._del_all_entries = entries
            self._del_filter()
            count = sum(1 for r in self._del_all_entries if r[3] == "fichier")
            self._status(self.del_status, f"ℹ  {count} fichier(s) .nix trouvé(s).", "ok")
        except Exception as e:
            self._status(self.del_status, f"❌  {e}", "err")
        self._del_upd_lbl()

    def _del_toggle(self, w, path):
        self.del_store[path][0] = not self.del_store[path][0]
        self._del_upd_lbl()

    def _del_upd_lbl(self):
        sel = [r[2] for r in self.del_store if r[0]]
        if sel:
            names = [os.path.basename(p) for p in sel]
            self.del_sel_lbl.set_text(
                f"{len(sel)} sélectionné(s) : {', '.join(names[:3])}{'…' if len(sel)>3 else ''}")
        else:
            self.del_sel_lbl.set_text("Aucun élément sélectionné")

    def _del_execute(self, *_):
        selected = [(r[2], r[3]) for r in self.del_store if r[0]]
        if not selected:
            return self._status(self.del_status, "⚠  Sélectionnez d'abord des éléments.", "warn")

        names = '\n'.join(f"  • {os.path.relpath(p, CUSTOM_DIR)}" for p, _ in selected)
        if not self._confirm_dialog(
                f"Supprimer {len(selected)} élément(s) ?",
                secondary_markup=(
                    f"<tt>{GLib.markup_escape_text(names)}</tt>\n\n"
                    "⚠  Cette action est <b>irréversible</b>.\n"
                    "Les imports dans <tt>default.nix</tt> seront retirés automatiquement."),
                message_type=Gtk.MessageType.WARNING,
                ok_label="Supprimer"):
            return

        cfg, cerr = read_file(CONFIG_FILE)
        if cfg is None:
            return self._status(self.del_status, f"❌  {cerr}", "err")

        cfg_lines = cfg.splitlines(); cfg_modified = False
        for path, kind in selected:
            if kind == "fichier":
                cfg_lines, changed = self._remove_import_line(cfg_lines, path)
                if changed:
                    cfg_modified = True
            elif kind == "dossier vide":
                cfg_lines, changed = self._remove_folder_from_imports(cfg_lines, path)
                if changed:
                    cfg_modified = True

        if cfg_modified:
            cfg_lines, ch2 = self._prune_empty_import_groups(cfg_lines)
            if ch2:
                cfg_modified = True

        paths = [p for p, k in selected if k == "fichier"]
        desc_names = ', '.join(os.path.basename(p) for p in paths[:3])
        if len(paths) > 3:
            desc_names += '…'
        bid = self._backup_snapshot(
            'delete',
            f"Suppression : {desc_names}",
            paths,
            include_default=cfg_modified)

        cmds = []
        for path, kind in selected:
            safe = path.replace('"', '\\"')
            cmds.append(f'rm -rf "{safe}"')

        tmp_cfg = None
        if cfg_modified:
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.nix',
                        prefix='/tmp/fray-cfg-', delete=False) as f:
                    f.write('\n'.join(cfg_lines) + '\n'); tmp_cfg = f.name
                cmds.append(f'cp "{tmp_cfg}" "{CONFIG_FILE}"')
            except Exception as e:
                return self._status(self.del_status, f"❌  Erreur tmp : {e}", "err")

        ok, err = run_pkexec_script(cmds)
        if tmp_cfg:
            try: os.unlink(tmp_cfg)
            except OSError: pass

        if ok:
            commit_paths = list(paths)
            if cfg_modified:
                commit_paths.append(CONFIG_FILE)
            _backup_commit_after(bid, commit_paths)
            self._status(self.del_status,
                f"✅  {len(selected)} élément(s) supprimé(s)"
                + (" + imports retirés de default.nix" if cfg_modified else ""), "ok")
            self._del_refresh()
        else:
            self._status(self.del_status, f"❌  {err}", "err")

    def _remove_import_line(self, lines, file_path):
        try:
            rel1 = './' + os.path.relpath(file_path, os.path.dirname(CONFIG_FILE))
            rel2 = os.path.relpath(file_path, os.path.dirname(CONFIG_FILE))
        except Exception:
            return lines, False
        new_lines = []; changed = False
        for line in lines:
            s = line.strip()
            if s in (rel1, rel2, rel1+';', rel2+';', f'"{rel1}"', f'"{rel2}"'):
                changed = True; continue
            new_lines.append(line)
        return new_lines, changed

    # ---
    # ONGLET 6 - Éditer un fichier .nix
    # ---
    def tab_edit(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        apply_css(vbox, "pad")

        tb = Gtk.Box(spacing=8); tb.set_border_width(8)
        apply_css(tb, "hbar")
        self.edit_path_lbl = Gtk.Label(label=CONFIG_FILE)
        apply_css(self.edit_path_lbl, "path")
        self.edit_path_lbl.set_halign(Gtk.Align.START)
        self.edit_path_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        tb.pack_start(self.edit_path_lbl, True, True, 0)

        for lbl, cb in [
            ("💾  Sauvegarder", self._edit_save),
            ("↻  Recharger",    lambda *_: self._edit_load(self._edit_cur)),
            ("📁  Ouvrir…",     self._edit_open),
        ]:
            b = Gtk.Button(label=lbl)
            apply_css(b, "btn-primary" if "Sauv" in lbl else "btn-secondary")
            b.connect("clicked", cb); tb.pack_end(b, False, False, 0)

        vbox.pack_start(tb, False, False, 0)

        warn = self._infobox(
            f'⚠  Seuls les fichiers de <tt>{CUSTOM_DIR}/</tt> sont accessibles à l\'ouverture.',
            "warnbox")
        warn.set_border_width(6)
        vbox.pack_start(warn, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        self.edit_status = Gtk.Label(label="")
        self.edit_status.set_halign(Gtk.Align.START)
        self.edit_status.set_margin_start(10); self.edit_status.set_margin_top(4)
        vbox.pack_start(self.edit_status, False, False, 0)

        self.edit_tv = Gtk.TextView()
        self.edit_tv.set_editable(True); self.edit_tv.set_monospace(True)
        self.edit_tv.set_left_margin(16); self.edit_tv.set_right_margin(16)
        self.edit_tv.set_top_margin(10); self.edit_tv.set_wrap_mode(Gtk.WrapMode.NONE)
        self._add_nix_tags(self.edit_tv.get_buffer(), "_hl_handler_edit")
        self._edit_undo_reset = self._attach_undo(self.edit_tv, "_hl_handler_edit")
        search_rev_edit = self._attach_search(self.edit_tv)
        editor_box_e = self._make_editor_with_lineno(self.edit_tv)
        editor_outer_e = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        editor_outer_e.pack_start(search_rev_edit, False, False, 0)
        editor_outer_e.pack_start(editor_box_e, True, True, 0)
        vbox.pack_start(editor_outer_e, True, True, 0)

        self._edit_cur = CONFIG_FILE
        self._edit_load(CONFIG_FILE)
        return vbox

    # Numéros de ligne
    def _make_editor_with_lineno(self, tv, css_class="code"):
        """Retourne un HBox avec [gutter numéros | ScrolledWindow(tv)]."""
        apply_css(tv, css_class)
        buf = tv.get_buffer()

        # Gutter : un TextView read-only pour les numéros
        gutter = Gtk.TextView()
        gutter.set_editable(False); gutter.set_cursor_visible(False)
        gutter.set_wrap_mode(Gtk.WrapMode.NONE)
        gutter.set_monospace(True)
        gutter.set_left_margin(6); gutter.set_right_margin(6)
        gutter.set_top_margin(tv.get_top_margin())
        apply_css(gutter, "lineno")
        gutter_buf = gutter.get_buffer()

        def _upd_lineno(*_):
            n = buf.get_line_count()
            text = "\n".join(str(i) for i in range(1, n + 1))
            gutter_buf.set_text(text)
            # Sync largeur gutter
            w = max(28, len(str(n)) * 8 + 14)
            gutter.set_size_request(w, -1)
        _upd_lineno()
        buf.connect("changed", _upd_lineno)

        # Sync scroll vertical
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(tv)

        gutter_scroll = Gtk.ScrolledWindow()
        gutter_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)

        def _sync_vadj(*_):
            vadj = scroll.get_vadjustment()
            gadj = gutter_scroll.get_vadjustment()
            if gadj and vadj:
                gadj.set_value(vadj.get_value())
        scroll.get_vadjustment().connect("value-changed", _sync_vadj)
        gutter_scroll.add(gutter)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(gutter_scroll, False, False, 0)
        hbox.pack_start(scroll, True, True, 0)
        return hbox

    def _edit_open(self, *_):
        dlg = self._open_nix_file_chooser(
            "Choisir un fichier .nix", CUSTOM_DIR, ok_label="Ouvrir")
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename(); dlg.destroy()
            try:
                if not os.path.realpath(path).startswith(
                        os.path.realpath(CUSTOM_DIR) + os.sep):
                    return self._status(self.edit_status,
                        f"❌  Seuls les fichiers de {CUSTOM_DIR}/ sont accessibles.", "err")
            except Exception: pass
            self._edit_load(path)
        else:
            dlg.destroy()

    def _edit_load(self, path):
        content, err = read_file(path)
        if content is None:
            return self._status(self.edit_status, f"❌  {err}", "err")
        self._buf_set_text(self.edit_tv.get_buffer(), "_hl_handler_edit", content)
        if hasattr(self, '_edit_undo_reset'):
            self._edit_undo_reset()
        self._edit_cur = path; self.edit_path_lbl.set_text(path)
        self._status(self.edit_status, f"✅  {os.path.basename(path)} chargé", "ok")

    def _edit_save(self, *_):
        buf = self.edit_tv.get_buffer()
        content = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        old_content, _ = read_file(self._edit_cur)
        bid = None
        if old_content is not None:
            try:
                rel = os.path.relpath(self._edit_cur, CUSTOM_DIR)
            except Exception:
                rel = os.path.basename(self._edit_cur)
            desc = _backup_diff_desc(old_content, content, rel)
            bid = self._backup_snapshot('edit', desc, [self._edit_cur])
        ok, err = run_pkexec(content, self._edit_cur)
        if ok and bid:
            _backup_commit_after(bid, [self._edit_cur])
        self._status(self.edit_status,
            "✅  Sauvegardé !" if ok else f"❌  {err}",
            "ok" if ok else "err")

    # ---
    # ONGLET - Restaurer une sauvegarde
    # ---
    def tab_restore(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        apply_css(vbox, "bg")

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apply_css(top, "pad")
        top.pack_start(self._h1("Restaurer une sauvegarde"), False, False, 0)
        top.pack_start(self._infobox(
            'Avant chaque modification, une copie locale est enregistrée '
            f'dans <tt>{BACKUP_DIR_DISPLAY}</tt>.\n'
            'La restauration <b>annule uniquement le changement sélectionné</b> '
            '(lignes ajoutées, supprimées ou modifiées par cette action) '
            'sans écraser les modifications plus récentes.\n'
            'Chaque fichier est numéroté (#1, #2, #3…). '
            'Pour plusieurs versions du même fichier, restaurez de la plus récente '
            'à la plus ancienne (#3, puis #2, puis #1).\n'
            'La sauvegarde restaurée est retirée automatiquement de l\'historique.'
        ), False, False, 0)

        backup_btn_row = Gtk.Box(spacing=8)
        btn_restore = Gtk.Button(label="  ↩  Restaurer la sélection")
        apply_css(btn_restore, "btn-primary")
        btn_restore.connect("clicked", self._backup_restore_selected)
        backup_btn_row.pack_start(btn_restore, False, False, 0)
        self.backup_del_btn = Gtk.Button(label="  🗑  Supprimer")
        apply_css(self.backup_del_btn, "btn-warn")
        self.backup_del_btn.connect("clicked", self._backup_delete_selected)
        backup_btn_row.pack_start(self.backup_del_btn, False, False, 0)
        btn_bak_open = Gtk.Button(label="  📂  Ouvrir dossier")
        apply_css(btn_bak_open, "btn-secondary")
        btn_bak_open.connect("clicked", self._backup_open_folder)
        backup_btn_row.pack_start(btn_bak_open, False, False, 0)
        btn_refresh = Gtk.Button(label="  🔄  Actualiser")
        apply_css(btn_refresh, "btn-secondary")
        btn_refresh.connect("clicked", lambda *_: self._backup_refresh_list())
        backup_btn_row.pack_start(btn_refresh, False, False, 0)
        top.pack_start(backup_btn_row, False, False, 0)

        self.backup_status = Gtk.Label(label="")
        self.backup_status.set_halign(Gtk.Align.START)
        top.pack_start(self.backup_status, False, False, 0)
        vbox.pack_start(top, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(140)
        self.backup_store = Gtk.ListStore(bool, str, str, str, str, str)
        self.backup_tree = Gtk.TreeView(model=self.backup_store)
        self.backup_tree.set_headers_visible(True)

        rt = Gtk.CellRendererToggle()
        rt.connect("toggled", self._backup_toggle)
        c0 = Gtk.TreeViewColumn("", rt, active=0)
        c0.set_fixed_width(36)
        self.backup_tree.append_column(c0)

        for col_title, idx, width in [
            ("Date", 2, 150), ("Type", 3, 100),
            ("Description", 4, 0), ("Fichiers (n°)", 5, 160),
        ]:
            r = Gtk.CellRendererText()
            if idx == 4:
                r.set_property("ellipsize", Pango.EllipsizeMode.END)
            c = Gtk.TreeViewColumn(col_title, r, text=idx)
            if width:
                c.set_fixed_width(width)
            else:
                c.set_expand(True)
            self.backup_tree.append_column(c)
        sel = self.backup_tree.get_selection()
        sel.connect("changed", self._backup_on_selection_changed)
        scroll.add(self.backup_tree)
        vbox.pack_start(scroll, True, True, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        details_lbl = Gtk.Label(label="Détail de la sauvegarde sélectionnée")
        apply_css(details_lbl, "h2")
        details_lbl.set_halign(Gtk.Align.START)
        details_lbl.set_margin_start(18)
        details_lbl.set_margin_top(8)
        vbox.pack_start(details_lbl, False, False, 0)

        details_scroll = Gtk.ScrolledWindow()
        details_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        details_scroll.set_min_content_height(160)
        details_scroll.set_max_content_height(280)
        self.backup_details = Gtk.TextView()
        self.backup_details.set_editable(False)
        self.backup_details.set_wrap_mode(Gtk.WrapMode.WORD)
        self.backup_details.set_left_margin(12)
        self.backup_details.set_right_margin(12)
        apply_css(self.backup_details, "code")
        self.backup_details_buf = self.backup_details.get_buffer()
        details_scroll.add(self.backup_details)
        vbox.pack_start(details_scroll, False, False, 0)

        GLib.idle_add(self._backup_refresh_list)
        return vbox

    # ---
    # ONGLET 6 - Système (fray-update en vert + terminal lisible)
    # ---
    def tab_system(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        apply_css(vbox, "bg")

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apply_css(top, "pad")
        top.pack_start(self._h1("Commandes système Fray"), False, False, 0)

        self.sys_cmds_infobox = self._infobox(
            '<b>fray-update</b>  ->  flake update + Flatpak (pas de switch). '
            'Redémarrage recommandé après.\n'
            '<b>fray-update --switch</b>  ->  Applique les modifications immédiatement sans redémarrer.\n'
            '<b>Nix-Rebuild</b>  ->  Applique <b>uniquement</b> vos fichiers dans '
            '<tt>customConfig</tt> (nh os switch). '
            '<b>Ne fait pas</b> le switch - pour ça, utilisez fray-update --switch.\n\n'
            '⚠  Certaines modifications (nouveau noyau, services bas niveau) '
            'nécessitent un redémarrage complet même après un switch.')
        self.sys_cmds_lbl = self.sys_cmds_infobox.get_children()[0]
        top.pack_start(self.sys_cmds_infobox, False, False, 0)

        btn_row = Gtk.Box(spacing=10)
        self._sys_cmd_btns = {}
        for label, cmd_name, style in [
            ("  🔄  fray-update",  "fray-update",    "btn-primary"),
            ("  ⚡  fray-update --switch",  "fray-update --switch",    "btn-primary"),
            ("  🔨  Nix-Rebuild",  "__nh-switch__", "btn-primary"),
            ("  🔁  Redémarrer",  "__reboot__",    "btn-warn"),
        ]:
            b = Gtk.Button(label=label); apply_css(b, style)
            b.connect("clicked", self._sys_run, cmd_name)
            self._sys_cmd_btns[cmd_name] = b
            btn_row.pack_start(b, False, False, 0)
        top.pack_start(btn_row, False, False, 0)

        self.sys_maint_sep = Gtk.Separator()
        top.pack_start(self.sys_maint_sep, False, False, 4)
        self.sys_maint_title = self._h1("Maintenance et nettoyage")
        top.pack_start(self.sys_maint_title, False, False, 0)
        self.sys_maint_infobox = self._infobox(
            '<b>Nettoyer</b> - menu interactif intégré '
            '(générations Nix, logs, corbeille, Flatpak…).\n'
            '<b>Réparer</b> - vérifie le store Nix et répare les Flatpak.')
        top.pack_start(self.sys_maint_infobox, False, False, 0)
        maint_row = Gtk.Box(spacing=10)
        self.sys_maint_row = maint_row
        for label, cmd_name, style in [
            ("  🧹  Nettoyer",  "fray-cleanup",    "btn-secondary"),
            ("  🔧  Réparer",    "__fray-repair__", "btn-secondary"),
        ]:
            b = Gtk.Button(label=label)
            apply_css(b, style)
            b.connect("clicked", self._sys_run, cmd_name)
            self._sys_cmd_btns[cmd_name] = b
            maint_row.pack_start(b, False, False, 0)
        top.pack_start(maint_row, False, False, 0)

        log_row = Gtk.Box(spacing=8)
        self.sys_save_btn = Gtk.Button(label="  💾  Sauvegarder le log")
        apply_css(self.sys_save_btn, "btn-secondary")
        self.sys_save_btn.connect("clicked", self._sys_save_log)
        self.sys_save_btn.set_sensitive(False)
        log_row.pack_start(self.sys_save_btn, False, False, 0)
        btn_open_logs = Gtk.Button(label="  📂  Ouvrir dossier logs")
        apply_css(btn_open_logs, "btn-secondary")
        btn_open_logs.connect("clicked", self._sys_open_logs)
        log_row.pack_start(btn_open_logs, False, False, 0)
        self.sys_log_lbl = Gtk.Label(label=""); apply_css(self.sys_log_lbl, "h2")
        log_row.pack_start(self.sys_log_lbl, False, False, 0)
        top.pack_start(log_row, False, False, 0)

        vbox.pack_start(top, False, False, 0)
        vbox.pack_start(Gtk.Separator(), False, False, 0)

        ht = Gtk.Box(spacing=8)
        ht.set_name("term-header")
        apply_css(ht, "bg")
        lt = Gtk.Label(label="  📟  Terminal")
        apply_css(lt, "h1"); lt.set_name("term-lbl"); ht.pack_start(lt, False, False, 0)
        bc = Gtk.Button(label="Effacer"); apply_css(bc, "btn-secondary")
        vbox.pack_start(ht, False, False, 0)

        if _HAS_VTE:
            bc.connect("clicked", lambda *_: self.vte.reset(True, True))
            ht.pack_end(bc, False, False, 0)
            self.vte = Vte.Terminal()
            self.vte.set_scrollback_lines(50000)
            self.vte.set_mouse_autohide(True)
            self.vte.set_bold_is_bright(True)
            def _rgba(h):
                return Gdk.RGBA(
                    int(h[0:2], 16) / 255,
                    int(h[2:4], 16) / 255,
                    int(h[4:6], 16) / 255,
                    1.0
                )
            palette = [
                _rgba("12141f"), _rgba("f07575"), _rgba("50d080"), _rgba("e8b840"),
                _rgba("72aef5"), _rgba("c084f5"), _rgba("4dd0e1"), _rgba("ccd4e8"),
                _rgba("3a3f58"), _rgba("f87171"), _rgba("34d399"), _rgba("fbbf24"),
                _rgba("60a5fa"), _rgba("e879f9"), _rgba("22d3ee"), _rgba("ffffff"),
            ]
            self.vte.set_colors(_rgba("dce4f8"), _rgba("12141f"), palette)
            self.vte.connect("key-press-event",    self._vte_on_key)
            self.vte.connect("button-press-event", self._vte_popup)
            self.vte.connect("contents-changed", self._on_vte_contents_changed)

            self._vte_shell_pid = -1
            shell = os.environ.get('SHELL', '/bin/bash')
            home  = os.environ.get('HOME', os.path.expanduser('~'))
            env   = _make_env()
            env['TERM']      = 'xterm-256color'
            env['COLORTERM'] = 'truecolor'
            env_list = [f"{k}={v}" for k, v in env.items()]

            _rcfile = None
            if 'bash' in shell:
                try:
                    with tempfile.NamedTemporaryFile(
                            mode='w', suffix='.sh',
                            prefix='/tmp/fray-vte-rc-', delete=False) as _f:
                        _f.write('# Fray - VTE : sourcing profil NixOS\n')
                        _f.write('[ -f /etc/profile ] && source /etc/profile 2>/dev/null\n')
                        _f.write('[ -f /etc/bashrc ]  && source /etc/bashrc  2>/dev/null\n')
                        _f.write('[ -f ~/.bashrc ]    && source ~/.bashrc    2>/dev/null\n')
                        _rcfile = _f.name
                    spawn_cmd = [shell, '--rcfile', _rcfile, '-i']
                except Exception:
                    spawn_cmd = [shell, '-i']
                    _rcfile   = None
            else:
                spawn_cmd = [shell, '-i']

            def _on_spawn(terminal, pid, err):
                if _rcfile:
                    try: os.unlink(_rcfile)
                    except OSError: pass
                if err:
                    self._vte_append(
                        f"⚠  Impossible de démarrer le shell ({err})\n", "warn")
                else:
                    self._vte_shell_pid = pid

            self.vte.spawn_async(
                Vte.PtyFlags.DEFAULT,
                home,
                spawn_cmd,
                env_list,
                GLib.SpawnFlags.DEFAULT,
                None, None,
                -1,
                None,
                _on_spawn,
            )

            scroll_vte = Gtk.ScrolledWindow()
            scroll_vte.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scroll_vte.add(self.vte)
            vbox.pack_start(scroll_vte, True, True, 0)
            self._sys_log = ""
        else:
            bc.connect("clicked", lambda *_: self._fallback_buf.set_text(""))
            ht.pack_end(bc, False, False, 0)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self._fallback_tv = Gtk.TextView()
            self._fallback_tv.set_editable(False)
            self._fallback_tv.set_monospace(True)
            self._fallback_tv.set_left_margin(12); self._fallback_tv.set_top_margin(8)
            self._fallback_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            apply_css(self._fallback_tv, "terminal")
            self._fallback_buf = self._fallback_tv.get_buffer()
            self._fallback_buf.create_tag("err",  foreground="#f07575")
            self._fallback_buf.create_tag("ok",   foreground="#50d080")
            self._fallback_buf.create_tag("info", foreground="#9aa8c0")
            self._fallback_buf.create_tag("warn", foreground="#e8b840")
            self._fallback_buf.create_tag("cmd",  foreground="#72aef5", weight=Pango.Weight.BOLD)
            scroll.add(self._fallback_tv)
            vbox.pack_start(scroll, True, True, 0)
            self._sys_log = ""
            self._vte_append("⚠  python3-gi-vte non installé - terminal basique.\n", "warn")
            self._vte_append("Fray Editor Config - Terminal prêt.\n", "info")

        return vbox

    # Coloration syntaxique Nix
    _NIX_COMMENT   = re.compile(r'#[^\n]*')
    _NIX_MLSTRING  = re.compile(r"''(?:[^']|'(?!')|''(?=[$'\\]))*''", re.DOTALL)
    _NIX_STRING    = re.compile(r'"(?:[^"\\]|\\.)*"')
    _NIX_ANGLE     = re.compile(r'<[a-zA-Z][a-zA-Z0-9._/-]*>')
    _NIX_PATH      = re.compile(r'\.{1,2}/[a-zA-Z0-9_./-]+')
    _NIX_ABSPATH   = re.compile(r'/[a-zA-Z][a-zA-Z0-9._/-]{2,}')
    _NIX_KEYWORD   = re.compile(
        r'\b(let|in|with|import|rec|inherit|if|then|else|assert|or|and|not)\b')
    _NIX_BUILTIN   = re.compile(
        r'\b(builtins|lib|pkgs|pkgs-unstable|config|options|modulesPath)\b')
    _NIX_BOOL      = re.compile(r'\b(true|false|null)\b')
    _NIX_NUMBER    = re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\b')
    _NIX_ATTRKEY   = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\-\.]*)\s*(?==(?!=))')
    _NIX_FUNCARG   = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:')
    _NIX_OPERATOR  = re.compile(r'(\+\+|//|\?|@|\.\.\.)')
    _NIX_BRACKET   = re.compile(r'[{}\[\]();]')

    # Regex utilitaires (fonctions internes)
    _RE_INDENT   = re.compile(r'^(\s*)')
    _RE_SYSPKGS  = re.compile(r'environment\.systemPackages\s*=')
    _RE_PKG_VER  = re.compile(r'^(\S+)\s*(.*)')
    _RE_IMPORTS  = re.compile(r'\s*imports\s*=\s*\[')

    def _nix_highlight_safe(self, buf, handler_attr):
        """Debounce 80 ms pour la coloration syntaxique (frappe utilisateur)."""
        timer_attr = handler_attr + '_timer'
        existing = getattr(self, timer_attr, 0)
        if existing:
            try: GLib.source_remove(existing)
            except Exception: pass

        def _do():
            setattr(self, timer_attr, 0)
            handler_id = getattr(self, handler_attr, None)
            if handler_id:
                try: buf.handler_block(handler_id)
                except Exception: pass
            try:
                self._nix_highlight(buf)
            except Exception:
                pass
            finally:
                if handler_id:
                    try: buf.handler_unblock(handler_id)
                    except Exception: pass
            return False

        setattr(self, timer_attr, GLib.timeout_add(80, _do))

    def _nix_highlight(self, buf):
        """Applique la coloration syntaxique Nix sur tout le buffer."""
        start = buf.get_start_iter(); end = buf.get_end_iter()
        for tag_name, _ in self._NIX_TAGS_DEF:
            try:
                buf.remove_tag_by_name(tag_name, start, end)
            except Exception:
                return
        text = buf.get_text(start, end, True)

        def apply(m, tag_name):
            s = buf.get_iter_at_offset(m.start())
            e = buf.get_iter_at_offset(m.end())
            buf.apply_tag_by_name(tag_name, s, e)

        skip_ranges = []
        for m in self._NIX_COMMENT.finditer(text):
            apply(m, "nix-comment"); skip_ranges.append((m.start(), m.end()))

        def in_skip(m):
            return any(s <= m.start() < e for s, e in skip_ranges)

        for m in self._NIX_MLSTRING.finditer(text):
            if not in_skip(m):
                s_open  = buf.get_iter_at_offset(m.start())
                e_open  = buf.get_iter_at_offset(m.start() + 2)
                s_close = buf.get_iter_at_offset(m.end() - 2)
                e_close = buf.get_iter_at_offset(m.end())
                buf.apply_tag_by_name("nix-mlstring", s_open,  e_open)
                buf.apply_tag_by_name("nix-mlstring", s_close, e_close)
                skip_ranges.append((m.start(), m.end()))
        for m in self._NIX_STRING.finditer(text):
            if not in_skip(m):
                apply(m, "nix-string");  skip_ranges.append((m.start(), m.end()))

        for m in self._NIX_ANGLE.finditer(text):
            if not in_skip(m): apply(m, "nix-angle")
        for m in self._NIX_PATH.finditer(text):
            if not in_skip(m): apply(m, "nix-path")
        for m in self._NIX_ABSPATH.finditer(text):
            if not in_skip(m): apply(m, "nix-abspath")
        for m in self._NIX_KEYWORD.finditer(text):
            if not in_skip(m): apply(m, "nix-keyword")
        for m in self._NIX_BUILTIN.finditer(text):
            if not in_skip(m): apply(m, "nix-builtin")
        for m in self._NIX_BOOL.finditer(text):
            if not in_skip(m): apply(m, "nix-bool")
        for m in self._NIX_NUMBER.finditer(text):
            if not in_skip(m): apply(m, "nix-number")
        for m in self._NIX_ATTRKEY.finditer(text):
            if not in_skip(m): apply(m, "nix-attrkey")
        for m in self._NIX_FUNCARG.finditer(text):
            if not in_skip(m): apply(m, "nix-funcarg")
        for m in self._NIX_OPERATOR.finditer(text):
            if not in_skip(m): apply(m, "nix-operator")
        for m in self._NIX_BRACKET.finditer(text):
            if not in_skip(m): apply(m, "nix-bracket")

    # Terminal VTE - méthodes
    _TAG_ANSI = {
        'ok':   '\x1b[32m',
        'err':  '\x1b[31m',
        'warn': '\x1b[33m',
        'info': '\x1b[90m',
        'cmd':  '\x1b[34;1m',
    }
    _ANSI_SGR_FULL = re.compile(r'\x1b\[([0-9;?]*)m')

    def _vte_on_key(self, widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval in (ord('c'), ord('C')):
            if widget.get_has_selection():
                widget.copy_clipboard_format(Vte.Format.TEXT)
                return True
        return False

    def _vte_popup(self, widget, event):
        if event.button != 3:
            return False
        menu = Gtk.Menu()
        item_copy = Gtk.MenuItem(label="  📋  Copier la sélection")
        item_copy.connect("activate",
            lambda *_: widget.copy_clipboard_format(Vte.Format.TEXT))
        item_copy.set_sensitive(widget.get_has_selection())
        menu.append(item_copy)
        item_paste = Gtk.MenuItem(label="  📌  Coller")
        item_paste.connect("activate",
            lambda *_: widget.paste_clipboard())
        menu.append(item_paste)
        item_sep = Gtk.SeparatorMenuItem()
        menu.append(item_sep)
        item_clear = Gtk.MenuItem(label="  🗑  Effacer")
        item_clear.connect("activate", lambda *_: widget.reset(True, True))
        menu.append(item_clear)
        menu.show_all()
        menu.popup_at_pointer(event)
        return True

    def _vte_append(self, text: str, tag: str = None):
        if _HAS_VTE:
            ansi  = self._TAG_ANSI.get(tag, '')
            reset = '\x1b[0m' if ansi else ''
            data  = (ansi + text + reset).encode('utf-8', errors='replace')
            GLib.idle_add(self.vte.feed, data)
        else:
            clean = self._ANSI_SGR_FULL.sub('', text)
            def _do(clean=clean, tag=tag):
                end = self._fallback_buf.get_end_iter()
                if tag:
                    try: self._fallback_buf.insert_with_tags_by_name(end, clean, tag)
                    except: self._fallback_buf.insert(end, clean)
                else:
                    self._fallback_buf.insert(end, clean)
                adj = self._fallback_tv.get_vadjustment()
                adj.set_value(adj.get_upper() - adj.get_page_size())
            GLib.idle_add(_do)
        self._sys_log += text

    def _on_vte_contents_changed(self, terminal):
        """Snapshot le contenu VTE dans _sys_log pour la sauvegarde."""
        def _snap():
            try:
                rows = terminal.get_row_count()
                cols  = terminal.get_column_count()
                text  = ""
                # Nouvelle API Vte >= 0.72
                try:
                    raw  = terminal.get_text_range_format(
                        Vte.Format.TEXT, 0, 0, rows - 1, cols - 1)
                    text = (raw[0] if isinstance(raw, tuple) else raw) or ""
                except AttributeError:
                    # Ancienne API Vte < 0.72
                    try:
                        raw  = terminal.get_text(None, None)
                        text = (raw[0] if isinstance(raw, tuple) else raw) or ""
                    except Exception:
                        pass
                if text.strip():
                    self._sys_log = text
            except Exception:
                pass
            return GLib.SOURCE_REMOVE
        GLib.idle_add(_snap)

    def _go_system_tab(self):
        if getattr(self, 'advanced_mode', False):
            self._select_page("system")

    def _feed_vte_command(self, cmd_str, label):
        """Envoie une commande au terminal intégré (onglet Système)."""
        self._go_system_tab()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._vte_append(f"\n{'-'*50}\n", "info")
        self._vte_append(f"[{ts}] {label}\n", "cmd")
        if _HAS_VTE and getattr(self, '_vte_shell_pid', -1) > 0:
            self._sys_log = ""
            self.vte.feed_child(cmd_str.encode('utf-8'))
            self.sys_save_btn.set_sensitive(True)
            return True
        self._vte_append(cmd_str, "info")
        self.sys_save_btn.set_sensitive(True)
        return False

    def _offer_reboot_after_success(self, what):
        """Propose un redémarrage uniquement après un apply réussi."""
        resp = self._question_dialog(
            "Opération réussie",
            body_markup=(
                f"<b>{GLib.markup_escape_text(str(what))}</b> terminé avec succès.\n\n"
                "Certains changements (noyau, boot, drivers) demandent un redémarrage.\n"
                "Redémarrer maintenant ?"
            ),
            buttons=[
                ("Plus tard", Gtk.ResponseType.CANCEL, "secondary"),
                ("Redémarrer", Gtk.ResponseType.OK, "primary"),
            ],
        )
        if resp == Gtk.ResponseType.OK:
            self._sys_run(None, "__reboot__")
        return False

    def _sys_run(self, btn, cmd_name):
        sudo_path  = '/run/wrappers/bin/sudo'

        if cmd_name == 'fray-cleanup':
            script = self._write_maintenance_script()
            self._feed_vte_command(f"bash {script}\n", f"$ Fray Maintenance")
            return

        if cmd_name == '__fray-repair__':
            script = self._write_maintenance_script()
            self._feed_vte_command(
                f"bash {script} --repair-only\n", f"$ Fray Réparation")
            return

        if cmd_name == "__nh-switch__":
            plan = _nh_os_switch_plan()
            if plan.get("refuse_glf"):
                try:
                    _refuse_glf_rebuild()
                except RuntimeError as e:
                    self._dlg_info("Hôte GLF", str(e))
                    return
            resp = self._question_dialog(
                "Confirmer Nix-Rebuild ?",
                body_markup=(
                    "Reconstruit et applique <b>uniquement</b> vos modifications dans "
                    "<tt>customConfig</tt> - <b>sans</b> mise à jour Fray "
                    "(pas de téléchargement de paquets système).\n\n"
                    f"<tt>{GLib.markup_escape_text(plan['cmd'])}</tt>\n\n"
                    f"Outil : <b>{GLib.markup_escape_text(plan['tool'])}</b>\n"
                    f"Hôte  : <b>{GLib.markup_escape_text(plan['hostname'])}</b>\n\n"
                    f"Pour mettre à jour Fray, utilisez <b>fray-update</b>.\n"
                    f"⚠  Cette opération peut prendre plusieurs minutes."),
                buttons=[
                    ("Annuler", Gtk.ResponseType.CANCEL, "secondary"),
                    ("Exécuter", Gtk.ResponseType.OK, "primary"),
                ])
            if resp != Gtk.ResponseType.OK:
                return

        if cmd_name in ("fray-update", "fray-update --switch"):
            plan = _fray_os_command_plan(cmd_name)
            if plan.get("refuse_glf"):
                try:
                    _refuse_glf_rebuild()
                except RuntimeError as e:
                    self._dlg_info("Hôte GLF", str(e))
                    return
            steps_mk = []
            for i, (cmdline, label, *_rest) in enumerate(plan["steps"], 1):
                steps_mk.append(
                    f"<b>Étape {i}</b> - {GLib.markup_escape_text(label)} :\n"
                    f"<tt>  {GLib.markup_escape_text(cmdline)}</tt>"
                )
            body = (
                "\n\n".join(steps_mk)
                + "\n\n"
                + f"Outil : <b>{GLib.markup_escape_text(plan['tool'])}</b>\n"
                + f"Hôte  : <b>{GLib.markup_escape_text(plan['hostname'])}</b>\n\n"
                + "⚠  Cette opération peut prendre plusieurs minutes."
            )
            resp = self._question_dialog(
                f"Confirmer l'exécution de {cmd_name} ?",
                body_markup=body,
                buttons=[
                    ("Annuler", Gtk.ResponseType.CANCEL, "secondary"),
                    ("Exécuter", Gtk.ResponseType.OK, "primary"),
                ])
            if resp != Gtk.ResponseType.OK:
                return

        if _HAS_VTE and getattr(self, '_vte_shell_pid', -1) > 0:
            if cmd_name == "__reboot__":
                cmd_str = "systemctl reboot -i\n"
            elif cmd_name == "__nh-switch__":
                cmd_str = _nh_os_switch_plan()['shell_cmd']
            elif cmd_name in ("fray-update", "fray-update --switch"):
                cmd_str = _fray_os_command_plan(cmd_name)['shell_cmd']
            else:
                cmd_str = f"{cmd_name}\n"
            self._sys_log = ""  # sera mis à jour par _on_vte_contents_changed
            self.vte.feed_child(cmd_str.encode('utf-8'))
            self.sys_save_btn.set_sensitive(True)
            return

        self._sys_log = ""; self.sys_save_btn.set_sensitive(False)
        self.sys_log_lbl.set_text("")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._vte_append(f"\n{'-'*50}\n", "info")
        self._vte_append(f"[{ts}] $ {cmd_name}\n", "cmd")

        def _run():
            env = _make_env()
            env['PATH'] = '/run/wrappers/bin:' + env.get('PATH', '')

            if cmd_name == "__reboot__":
                for try_cmd in (
                    ['systemctl', 'reboot', '-i'],
                    ['/run/current-system/sw/bin/systemctl', 'reboot', '-i'],
                    ['/run/wrappers/bin/pkexec', 'systemctl', 'reboot', '-i'],
                    ['/run/wrappers/bin/sudo',   'systemctl', 'reboot', '-i'],
                ):
                    try:
                        subprocess.run(try_cmd, env=env); return
                    except FileNotFoundError: continue
                    except Exception as e:
                        self._vte_append(f"❌  {e}\n", "err")
                        GLib.idle_add(self.sys_save_btn.set_sensitive, True); return
                return

            if cmd_name == "__nh-switch__":
                plan = _nh_os_switch_plan()
                askpass = _make_askpass_script()
                if askpass:
                    env['SUDO_ASKPASS'] = askpass
                    env['NH_ASKPASS'] = askpass
                sudo_pfx = ([sudo_path, '-A'] if askpass else [sudo_path])
                cmd = (sudo_pfx + plan['argv'][1:] if plan['needs_sudo']
                       else plan['argv'])
                self._vte_append("▶  nh os switch…\n", "info")
                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1, env=env)
                    for line in proc.stdout:
                        lo = _strip_ansi(line).lower()
                        tag = ("err" if any(w in lo for w in ('error', 'erreur', 'failed'))
                               else ("warn" if 'warn' in lo else None))
                        self._vte_append(_strip_ansi(line), tag)
                    proc.wait()
                except Exception as e:
                    self._vte_append(f"❌  {e}\n", "err")
                    if askpass:
                        _try_unlink(askpass)
                    GLib.idle_add(self.sys_save_btn.set_sensitive, True)
                    return
                finally:
                    if askpass:
                        _try_unlink(askpass)
                if proc.returncode == 0:
                    self._vte_append("\n✅  Succès - nh os switch terminé.\n", "ok")
                    GLib.idle_add(self._offer_reboot_after_success, "nh os switch")
                else:
                    self._vte_append(
                        f"\n❌  nh os switch a échoué (code {proc.returncode}).\n", "err")
                    # Pas de proposition de reboot en cas d'échec
                GLib.idle_add(self.sys_save_btn.set_sensitive, True)
                return

            if cmd_name in ("fray-update", "fray-update --switch"):
                plan = _fray_os_command_plan(cmd_name)
                askpass = _make_askpass_script()
                if askpass:
                    env['SUDO_ASKPASS'] = askpass
                    env['NH_ASKPASS'] = askpass
                sudo_pfx = ([sudo_path, '-A'] if askpass else [sudo_path])

                for idx, (_disp, label, argv, needs_sudo) in enumerate(plan['steps'], 1):
                    if needs_sudo and argv and argv[0] == sudo_path:
                        cmd = sudo_pfx + argv[1:]
                    else:
                        cmd = argv
                    self._vte_append(f"▶  Étape {idx}/3 - {label}…\n", "info")
                    try:
                        proc = subprocess.Popen(
                            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=env)
                        for line in proc.stdout:
                            lo = _strip_ansi(line).lower()
                            tag = ("err" if any(w in lo for w in ('error', 'erreur', 'failed'))
                                   else ("warn" if 'warn' in lo else None))
                            self._vte_append(_strip_ansi(line), tag)
                        proc.wait()
                    except Exception as e:
                        self._vte_append(f"❌  {e}\n", "err")
                        if askpass:
                            _try_unlink(askpass)
                        GLib.idle_add(self.sys_save_btn.set_sensitive, True)
                        return
                    if proc.returncode != 0:
                        self._vte_append(
                            f"\n❌  {label} a échoué (code {proc.returncode}).\n", "err")
                        if askpass:
                            _try_unlink(askpass)
                        GLib.idle_add(self.sys_save_btn.set_sensitive, True)
                        return

                if askpass:
                    _try_unlink(askpass)
                self._vte_append(f"\n✅  Succès - {cmd_name} terminé.\n", "ok")
                # Reboot proposé seulement après succès (surtout --switch)
                if cmd_name == "fray-update --switch":
                    GLib.idle_add(self._offer_reboot_after_success, cmd_name)
                GLib.idle_add(self.sys_save_btn.set_sensitive, True)
                return

            found = _resolve_nix_cmd(cmd_name)
            bash  = shutil.which('bash') or '/bin/bash'
            shell_path = ('PATH=/run/wrappers/bin:/run/current-system/sw/bin'
                          ':/nix/var/nix/profiles/default/bin:$PATH')
            candidates = (
                [([found], "direct"), (['/run/wrappers/bin/sudo', '-E', found], "sudo")]
                if found else
                [(['/run/wrappers/bin/sudo', '-E', bash, '-c',
                   f'{shell_path}; exec {cmd_name}'], "sudo bash")]
            )
            for cmd, mode in candidates:
                try:
                    self._vte_append(f"▶  [{mode}]…\n", "info")
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1, env=env)
                    for line in proc.stdout:
                        lo  = line.lower()
                        tag = ("err"  if any(w in lo for w in ('error','erreur','failed','fatal'))
                               else ("warn" if 'warn' in lo else None))
                        self._vte_append(line, tag)
                    proc.wait()
                    if proc.returncode == 0:
                        self._vte_append(f"\n✅  Succès (code {proc.returncode})\n", "ok"); break
                    elif proc.returncode in (1, 126, 127):
                        self._vte_append(f"ℹ  Code {proc.returncode}…\n", "info")
                    else:
                        self._vte_append(f"\n❌  Erreur (code {proc.returncode})\n", "err"); break
                except FileNotFoundError:
                    continue
                except Exception as e:
                    self._vte_append(f"❌  {e}\n", "err"); break

            GLib.idle_add(self.sys_save_btn.set_sensitive, True)

        threading.Thread(target=_run, daemon=True).start()

    def _sys_save_log(self, *_):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            path = os.path.join(LOG_DIR, f"fray-log_{ts}.txt")
            log_text = self._sys_log
            with open(path, 'w') as f:
                f.write(log_text or "")
            self.sys_log_lbl.set_text(f"✅  Sauvegardé -> {path}")
            apply_css(self.sys_log_lbl, "ok")
        except Exception as e:
            self.sys_log_lbl.set_text(f"❌  {e}")
            apply_css(self.sys_log_lbl, "err")

    def _sys_open_logs(self, *_):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except Exception:
            pass
        for cmd in (['xdg-open', LOG_DIR], ['nautilus', LOG_DIR],
                    ['dolphin', LOG_DIR], ['thunar', LOG_DIR]):
            try:
                subprocess.Popen(cmd, env=_make_env()); return
            except FileNotFoundError:
                continue
        self.sys_log_lbl.set_text(f"ℹ  Dossier : {LOG_DIR}")
        apply_css(self.sys_log_lbl, "info")

if __name__ == "__main__":
    _setup_app_identity()
    win = App()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()
