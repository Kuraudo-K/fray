#!/usr/bin/env python3
"""Fray Disk - GUI GTK inspirée nix-disk (liste, mount, gen Nix)."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Pango
import json
import os
import shutil
import subprocess
import threading

APP_ID = "fray-disk"
TITLE = "Fray Disk"


def _bin():
    return (
        os.environ.get("FRAY_DISK_BIN", "").strip()
        or shutil.which("fray-disk")
        or "fray-disk"
    )


def _icon():
    for p in (
        os.environ.get("FRAY_ICON", ""),
        "/run/current-system/sw/share/icons/hicolor/256x256/apps/fray-disk.png",
        "/run/current-system/sw/share/fray/logo/apps/fray-disk.png",
        "/run/current-system/sw/share/pixmaps/fray.png",
    ):
        if p and os.path.isfile(p):
            return p
    return ""


def _run(args, timeout=120):
    return subprocess.run(
        [_bin()] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class DiskWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=TITLE)
        self.set_default_size(720, 480)
        self.set_border_width(10)
        icon = _icon()
        if icon:
            try:
                self.set_icon_from_file(icon)
            except Exception:
                pass

        self._rows = []
        self._selected = None

        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(v)

        head = Gtk.Label()
        head.set_markup(
            "<b>Fray Disk</b>\nDisques et partitions - mount / umount / génération Nix"
        )
        head.set_xalign(0)
        v.pack_start(head, False, False, 0)

        self.msg = Gtk.Label(label="")
        self.msg.set_xalign(0)
        self.msg.set_line_wrap(True)
        v.pack_start(self.msg, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.store = Gtk.ListStore(str, str, str, str, str, str, str)  # path size fs mnt label kind name
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.get_selection().connect("changed", self._on_sel)
        for i, title in enumerate(
            ["Périphérique", "Taille", "FS", "Montage", "Label", "Type"]
        ):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            self.tree.append_column(col)
        scroll.add(self.tree)
        v.pack_start(scroll, True, True, 0)

        detail = Gtk.Label(label="Sélectionne une partition.")
        detail.set_xalign(0)
        detail.set_line_wrap(True)
        self.detail = detail
        v.pack_start(detail, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, cb in (
            ("Actualiser", lambda *_: self.refresh()),
            ("Monter", self._mount),
            ("Démonter", self._umount),
            ("Générer Nix…", self._gen_nix),
            ("Ouvrir outil DE", self._open_de),
        ):
            b = Gtk.Button(label=label)
            b.connect("clicked", cb)
            row.pack_start(b, False, False, 0)
        v.pack_start(row, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.refresh()

    def _set_msg(self, text, err=False):
        if err:
            self.msg.set_markup(f'<span foreground="#c62828">{GLib.markup_escape_text(text)}</span>')
        else:
            self.msg.set_text(text)

    def _on_sel(self, sel):
        model, it = sel.get_selected()
        if not it:
            self._selected = None
            return
        path = model[it][6]
        self._selected = next((r for r in self._rows if r.get("path") == path), None)
        if not self._selected:
            return
        r = self._selected
        self.detail.set_text(
            f"{r.get('path')}  |  {r.get('size')}  |  FS={r.get('fstype') or '-'}  |  "
            f"mount={r.get('mountpoint') or '-'}  |  {r.get('kind')}"
        )

    def refresh(self):
        self.store.clear()
        self._rows = []
        try:
            r = _run(["list-json"], timeout=30)
            if r.returncode != 0:
                self._set_msg(r.stderr.strip() or "list-json échoué", err=True)
                return
            self._rows = json.loads(r.stdout)
        except Exception as e:
            self._set_msg(str(e), err=True)
            return
        for row in self._rows:
            pad = "  " * int(row.get("depth") or 0)
            self.store.append(
                [
                    row.get("path") or "",
                    row.get("size") or "",
                    row.get("fstype") or "-",
                    row.get("mountpoint") or "-",
                    row.get("label") or "-",
                    row.get("kind") or "",
                    row.get("name") or "",
                ]
            )
            # show indent in first column
            it = self.store[-1].iter
            self.store.set_value(it, 0, pad + (row.get("path") or ""))
            # keep real path in row data; fix display vs path
            row["_display"] = pad + (row.get("path") or "")
        # re-fill with display path but selection uses stored rows by index
        self.store.clear()
        for row in self._rows:
            pad = "  " * int(row.get("depth") or 0)
            self.store.append(
                [
                    pad + (row.get("path") or ""),
                    row.get("size") or "",
                    row.get("fstype") or "-",
                    row.get("mountpoint") or "-",
                    row.get("label") or "-",
                    row.get("kind") or "",
                    row.get("path") or "",
                ]
            )
        self._set_msg(f"{len(self._rows)} entrées")

    def _selected_path(self):
        model, it = self.tree.get_selection().get_selected()
        if not it:
            return None
        # column 6 holds real path
        return model[it][6]

    def _confirm(self, title, body):
        d = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.CANCEL,
            text=title,
        )
        d.format_secondary_text(body)
        d.add_button("Confirmer", Gtk.ResponseType.OK)
        resp = d.run()
        d.destroy()
        return resp == Gtk.ResponseType.OK

    def _mount(self, *_):
        path = self._selected_path()
        if not path:
            self._set_msg("Sélectionne un périphérique", err=True)
            return
        if not self._confirm(
            "Confirmer le montage",
            f"Monter {path} via udisks ?\nAucune écriture destructive.",
        ):
            return
        self._async(["mount", path, "--yes"], f"Montage de {path}")

    def _umount(self, *_):
        path = self._selected_path()
        if not path:
            self._set_msg("Sélectionne un périphérique", err=True)
            return
        row = next((r for r in self._rows if r.get("path") == path), {})
        target = row.get("mountpoint") or path
        if target in ("/", "/boot", "/nix") or str(target).startswith("/nix/"):
            self._set_msg(f"Cible refusée (sensible) : {target}", err=True)
            return
        if not self._confirm(
            "Confirmer le démontage",
            f"Démonter {target} ?\nPas de formatage.",
        ):
            return
        self._async(["umount", target, "--yes"], f"Démontage de {target}")

    def _open_de(self, *_):
        self._async(["open"], "Ouverture outil DE")

    def _gen_nix(self, *_):
        include_system = self._confirm(
            "Inclure partitions système ?",
            "Oui = inclure /, /boot, /nix dans le fichier.\n"
            "Non = seulement les montages supplémentaires (recommandé).",
        )
        args = ["gen-nix"]
        if include_system:
            args.append("--system")
        try:
            r = _run(args, timeout=30)
        except Exception as e:
            self._set_msg(str(e), err=True)
            return
        if r.returncode != 0:
            self._set_msg(r.stderr.strip() or "gen-nix échoué", err=True)
            return

        default = os.environ.get("FRAY_DISK_NIX_OUT", "").strip()
        if not default:
            flake = os.environ.get("FRAY_FLAKE", "").strip()
            if flake:
                default = os.path.join(flake, "customConfig/hardware/generated-disks.nix")
            else:
                default = os.path.expanduser("~/.config/fray/generated-disks.nix")

        dlg = Gtk.Dialog(title="Génération Nix", transient_for=self, modal=True)
        dlg.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dlg.add_button("Écrire le fichier", Gtk.ResponseType.OK)
        box = dlg.get_content_area()
        box.set_spacing(8)
        box.set_border_width(10)
        box.add(Gtk.Label(label="Aperçu :", xalign=0))
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.get_buffer().set_text(r.stdout)
        tv.override_font(Pango.FontDescription("monospace 10"))
        sc = Gtk.ScrolledWindow()
        sc.set_min_content_height(220)
        sc.set_min_content_width(520)
        sc.add(tv)
        box.add(sc)
        ent = Gtk.Entry()
        ent.set_text(default)
        box.add(Gtk.Label(label="Chemin d'écriture (hors /etc/nixos hôte) :", xalign=0))
        box.add(ent)
        box.show_all()
        resp = dlg.run()
        path = ent.get_text().strip()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK:
            return
        if not path or path.startswith("/etc/nixos"):
            self._set_msg("Chemin refusé (évite /etc/nixos).", err=True)
            return
        if not self._confirm(
            "Écrire le fichier Nix ?",
            f"Écrire dans :\n{path}\n\nConfirme explicitement.",
        ):
            return
        wargs = ["write-nix", "--path", path, "--yes"]
        if include_system:
            wargs.append("--system")
        self._async(wargs, f"Écriture {path}")

    def _async(self, args, label):
        self._set_msg(f"{label}…")

        def work():
            try:
                r = _run(args, timeout=180)
                msg = (r.stdout or r.stderr or "").strip()
                GLib.idle_add(self._done, r.returncode, msg or label)
            except Exception as e:
                GLib.idle_add(self._done, 1, str(e))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, rc, msg):
        if rc == 0:
            self._set_msg(msg or "OK")
        else:
            self._set_msg(msg or f"Erreur code {rc}", err=True)
        self.refresh()
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
    win = DiskWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
