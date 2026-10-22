#!/usr/bin/env python3
"""Fray Wallpaper - GUI GTK + applique un fond."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
import json
import os
import shutil
import subprocess
import threading

APP_ID = "fray-wallpaper"
TITLE = "Fray Wallpaper"


def _bin():
    return (
        os.environ.get("FRAY_WALLPAPER_BIN", "").strip()
        or shutil.which("fray-wallpaper")
        or "fray-wallpaper"
    )


def _icon():
    for p in (
        os.environ.get("FRAY_ICON", ""),
        "/run/current-system/sw/share/pixmaps/fray.png",
        "/run/current-system/sw/share/fray/logo/fray-icon.png",
        "/run/current-system/sw/share/fray/logo/04gr10-charcoal-crimson.png",
    ):
        if p and os.path.isfile(p):
            return p
    return ""


def _run(args, timeout=60):
    return subprocess.run(
        [_bin()] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class WallpaperWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=TITLE)
        self.set_default_size(560, 420)
        self.set_border_width(12)
        icon = _icon()
        if icon:
            try:
                self.set_icon_from_file(icon)
            except Exception:
                pass

        self._items = []
        self._selected = None

        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(v)

        head = Gtk.Label()
        head.set_markup("<b>Fray Wallpaper</b>\nChoisir et appliquer un fond Fray")
        head.set_xalign(0)
        v.pack_start(head, False, False, 0)

        self.status = Gtk.Label(label="")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        v.pack_start(self.status, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_sel)
        scroll.add(self.listbox)
        v.pack_start(scroll, True, True, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_apply = Gtk.Button(label="Appliquer")
        btn_apply.get_style_context().add_class("suggested-action")
        btn_apply.connect("clicked", self._apply)
        row.pack_start(btn_apply, False, False, 0)
        btn_auto = Gtk.Button(label="Auto (dernier / défaut)")
        btn_auto.connect("clicked", self._auto)
        row.pack_start(btn_auto, False, False, 0)
        btn_ref = Gtk.Button(label="Actualiser")
        btn_ref.connect("clicked", lambda *_: self.refresh())
        row.pack_end(btn_ref, False, False, 0)
        v.pack_start(row, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.refresh()
        self._load_current()

    def _on_sel(self, _lb, row):
        if row is None:
            self._selected = None
            return
        self._selected = row.get_child().wall_id

    def refresh(self):
        for c in list(self.listbox.get_children()):
            self.listbox.remove(c)
        try:
            r = _run(["list-json"], timeout=30)
            if r.returncode != 0:
                self.status.set_text(r.stderr.strip() or "list-json échoué")
                return
            self._items = json.loads(r.stdout)
        except Exception as e:
            self.status.set_text(str(e))
            return
        for w in self._items:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(8)
            title = Gtk.Label(label=w.get("id") or "?")
            title.set_xalign(0)
            sub = Gtk.Label(label=f"{w.get('source')}  {w.get('path')}")
            sub.set_xalign(0)
            box.pack_start(title, False, False, 0)
            box.pack_start(sub, False, False, 0)
            box.wall_id = w.get("id")
            row.add(box)
            self.listbox.add(row)
            if w.get("id") == "fray-gaming-arena":
                self.listbox.select_row(row)
                self._selected = w.get("id")
        self.listbox.show_all()

    def _load_current(self):
        try:
            r = _run(["current"], timeout=15)
            if r.returncode == 0:
                self.status.set_text(r.stdout.strip().replace("\n", "  |  "))
        except Exception:
            pass

    def _apply(self, *_):
        wid = self._selected
        if not wid:
            self.status.set_text("Sélectionne un fond")
            return
        self._async(["set", wid], f"Application de {wid}")

    def _auto(self, *_):
        self._async(["auto"], "Auto-apply")

    def _async(self, args, label):
        self.status.set_text(f"{label}…")

        def work():
            try:
                r = _run(args, timeout=60)
                msg = (r.stdout or r.stderr or label).strip()
                GLib.idle_add(self._done, r.returncode, msg)
            except Exception as e:
                GLib.idle_add(self._done, 1, str(e))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, rc, msg):
        self.status.set_text(("OK: " if rc == 0 else "Erreur: ") + msg)
        if rc == 0:
            self._load_current()
        return False


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
    win = WallpaperWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
