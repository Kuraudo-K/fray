#!/usr/bin/env python3
"""Fray Switch - GUI GTK pour fray-de-switch."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import json
import os
import shutil
import subprocess
import threading

APP_ID = "fray-de-switch"
TITLE = "Fray Switch"


def _bin():
    return (
        os.environ.get("FRAY_DE_SWITCH_BIN", "").strip()
        or shutil.which("fray-de-switch")
        or "fray-de-switch"
    )


def _icon():
    for p in (
        os.environ.get("FRAY_ICON", ""),
        "/run/current-system/sw/share/icons/hicolor/256x256/apps/fray-de-switch.png",
        "/run/current-system/sw/share/fray/logo/apps/fray-de-switch.png",
        "/run/current-system/sw/share/pixmaps/fray.png",
    ):
        if p and os.path.isfile(p):
            return p
    return ""


def _run(args, timeout=600):
    return subprocess.run(
        [_bin()] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class SwitchWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=TITLE)
        self.set_default_size(520, 420)
        self.set_border_width(12)
        icon = _icon()
        if icon:
            try:
                self.set_icon_from_file(icon)
            except Exception:
                pass

        self._busy = False
        self._selected = None

        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(v)

        head = Gtk.Label()
        head.set_markup("<b>Fray Switch</b>\nBasculer de bureau (profils persistants)")
        head.set_xalign(0)
        v.pack_start(head, False, False, 0)

        self.status = Gtk.Label(label="Chargement…")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        v.pack_start(self.status, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(160)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_select)
        scroll.add(self.listbox)
        v.pack_start(scroll, True, True, 0)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.progress.set_text("En attente")
        self.progress.set_fraction(0)
        v.pack_start(self.progress, False, False, 0)

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_min_content_height(100)
        self.log = Gtk.TextView()
        self.log.set_editable(False)
        self.log.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        log_scroll.add(self.log)
        v.pack_start(log_scroll, True, True, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_switch = Gtk.Button(label="Basculer")
        self.btn_switch.get_style_context().add_class("suggested-action")
        self.btn_switch.connect("clicked", self._on_switch)
        row.pack_start(self.btn_switch, False, False, 0)

        self.btn_logout = Gtk.Button(label="Se déconnecter")
        self.btn_logout.set_sensitive(False)
        self.btn_logout.connect("clicked", lambda *_: self._session_exit("logout"))
        row.pack_start(self.btn_logout, False, False, 0)

        self.btn_reboot = Gtk.Button(label="Redémarrer")
        self.btn_reboot.set_sensitive(False)
        self.btn_reboot.connect("clicked", lambda *_: self._session_exit("reboot"))
        row.pack_start(self.btn_reboot, False, False, 0)

        btn_refresh = Gtk.Button(label="Actualiser")
        btn_refresh.connect("clicked", lambda *_: self.refresh())
        row.pack_end(btn_refresh, False, False, 0)
        v.pack_start(row, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.refresh()
        # Mission: démarrer l'action si cible passée (--to / env)
        auto = os.environ.get("FRAY_SWITCH_TO", "").strip()
        if auto:
            GLib.idle_add(self._auto_start, auto)

    def _append(self, text):
        buf = self.log.get_buffer()
        buf.insert(buf.get_end_iter(), text)

    def _on_select(self, _lb, row):
        if row is None:
            self._selected = None
            return
        self._selected = row.get_child().de_id

    def refresh(self):
        for c in list(self.listbox.get_children()):
            self.listbox.remove(c)
        try:
            r = _run(["list-json"], timeout=30)
            if r.returncode != 0:
                self.status.set_text(r.stderr.strip() or "Erreur list-json")
                return
            data = json.loads(r.stdout)
        except Exception as e:
            self.status.set_text(str(e))
            return

        cur = data.get("current") or "?"
        pref = data.get("preferred") or "(aucun)"
        self.status.set_text(f"Session : {cur}  |  Préféré : {pref}")

        for s in data.get("sessions") or []:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(8)
            box.set_margin_end(8)
            title = Gtk.Label(label=s.get("label") or s.get("id"))
            title.set_xalign(0)
            sub = Gtk.Label(
                label=f"id={s.get('id')}  profil={'oui' if s.get('has_profile') else 'non'}"
            )
            sub.set_xalign(0)
            sub.get_style_context().add_class("dim-label")
            box.pack_start(title, False, False, 0)
            box.pack_start(sub, False, False, 0)
            box.de_id = s.get("id")
            row.add(box)
            self.listbox.add(row)
            if s.get("id") == cur:
                self.listbox.select_row(row)
                self._selected = s.get("id")
        self.listbox.show_all()

    def _auto_start(self, de_id):
        self._selected = de_id
        self._on_switch(None)
        return False

    def _on_switch(self, _btn):
        if self._busy:
            return
        de = self._selected
        if not de:
            self._dlg("Choisis un bureau", "Sélectionne une session dans la liste.")
            return
        self._busy = True
        self.btn_switch.set_sensitive(False)
        self.btn_logout.set_sensitive(False)
        self.btn_reboot.set_sensitive(False)
        self.progress.set_fraction(0.15)
        self.progress.set_text("Installation du profil…")
        self._append(f"\n>>> switch {de}\n")

        def work():
            try:
                proc = subprocess.Popen(
                    [_bin(), "switch", de],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                out_lines = []
                for line in proc.stdout:
                    out_lines.append(line)
                    GLib.idle_add(self._append, line)
                rc = proc.wait()
                GLib.idle_add(self._switch_done, rc, "".join(out_lines), de)
            except Exception as e:
                GLib.idle_add(self._switch_done, 1, str(e), de)

        threading.Thread(target=work, daemon=True).start()

    def _switch_done(self, rc, out, de):
        self._busy = False
        self.btn_switch.set_sensitive(True)
        if rc == 0:
            self.progress.set_fraction(1.0)
            self.progress.set_text("Succès")
            self._append(f"\nOK -> {de}\n")
            self.btn_logout.set_sensitive(True)
            self.btn_reboot.set_sensitive(True)
            self._offer_session_exit(de)
        else:
            self.progress.set_fraction(0)
            self.progress.set_text("Échec")
            self._append(f"\nERREUR (code {rc})\n")
            self.btn_logout.set_sensitive(False)
            self.btn_reboot.set_sensitive(False)
            self._dlg(
                "Échec du basculement",
                out.strip() or f"fray-de-switch a échoué (code {rc}). Pas de redémarrage proposé.",
            )
        self.refresh()
        return False

    def _offer_session_exit(self, de):
        dlg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Basculement réussi",
        )
        dlg.format_secondary_text(
            f"Profil « {de} » appliqué.\n"
            "Déconnecte-toi (ou redémarre) pour choisir la session au greeter.\n"
            "Aucun redémarrage n'est forcé."
        )
        dlg.add_button("Plus tard", Gtk.ResponseType.CANCEL)
        dlg.add_button("Se déconnecter", Gtk.ResponseType.ACCEPT)
        dlg.add_button("Redémarrer", Gtk.ResponseType.YES)
        resp = dlg.run()
        dlg.destroy()
        if resp == Gtk.ResponseType.ACCEPT:
            self._session_exit("logout")
        elif resp == Gtk.ResponseType.YES:
            self._session_exit("reboot")

    def _session_exit(self, kind):
        if kind == "logout":
            cmds = [
                ["loginctl", "terminate-user", os.environ.get("USER", "")],
                ["gnome-session-quit", "--logout", "--no-prompt"],
            ]
        else:
            cmds = [["systemctl", "reboot", "-i"]]
        for c in cmds:
            try:
                subprocess.Popen(c)
                return
            except FileNotFoundError:
                continue
        self._dlg("Action impossible", f"Impossible de lancer {kind}.")

    def _dlg(self, title, body):
        d = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        d.format_secondary_text(body)
        d.run()
        d.destroy()


def main():
    GLib.set_application_name(TITLE)
    GLib.set_prgname(APP_ID)
    try:
        Gdk.set_program_class(APP_ID)
    except Exception:
        pass
    icon = _icon()
    if icon:
        try:
            Gtk.Window.set_default_icon_from_file(icon)
        except Exception:
            pass
    win = SwitchWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
