#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Module Calamares « nixos » Fray : génère calamares-generated.nix,
# copie le flake embarqué (/iso/iso-cfg) et lance nixos-install --flake …#fray.
# Locales limitées pour éviter le rebuild massif de glibc-locales.

import json
import libcalamares
import os
import re
import shutil
import subprocess

import gettext

_ = gettext.translation(
    "calamares-python",
    localedir=libcalamares.utils.gettext_path(),
    languages=libcalamares.utils.gettext_languages(),
    fallback=True,
).gettext

# Snippets pour calamares-generated.nix (importé par hosts/fray.nix)
cfghead = """\
# Généré par Calamares (Fray) — utilisateur, hostname, locale, bootloader.
{ config, pkgs, lib, ... }:
{
"""

cfgbootefi = """\
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

"""

cfgbootbios = """\
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "@@bootdev@@";
  boot.loader.grub.useOSProber = true;

"""

cfgbootbiosbtrfs = """\
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "@@bootdev@@";
  boot.loader.grub.useOSProber = true;
  boot.loader.grub.fsIdentifier = "provided";

"""

cfgbootnone = """\
  boot.loader.grub.enable = false;

"""

cfgbootgrubcrypt = """\
  boot.initrd.secrets = {
    "/boot/crypto_keyfile.bin" = null;
  };
  boot.loader.grub.enableCryptodisk = true;

"""

cfgnetwork = """\
  networking.hostName = "@@hostname@@";

"""

cfgtime = """\
  time.timeZone = "@@timezone@@";

"""

# Locales limitées : hit cache / build léger (pas glibc-locales « all »)
cfglocale = """\
  i18n.defaultLocale = "@@LANG@@";
  i18n.extraLocales = [
    "C.UTF-8/UTF-8"
    "en_US.UTF-8/UTF-8"
    "fr_FR.UTF-8/UTF-8"
    "de_DE.UTF-8/UTF-8"
    "es_ES.UTF-8/UTF-8"
    "it_IT.UTF-8/UTF-8"
    "pt_BR.UTF-8/UTF-8"
  ];

"""

cfglocaleextra = """\
  i18n.extraLocaleSettings = {
    LC_ADDRESS = "@@LC_ADDRESS@@";
    LC_IDENTIFICATION = "@@LC_IDENTIFICATION@@";
    LC_MEASUREMENT = "@@LC_MEASUREMENT@@";
    LC_MONETARY = "@@LC_MONETARY@@";
    LC_NAME = "@@LC_NAME@@";
    LC_NUMERIC = "@@LC_NUMERIC@@";
    LC_PAPER = "@@LC_PAPER@@";
    LC_TELEPHONE = "@@LC_TELEPHONE@@";
    LC_TIME = "@@LC_TIME@@";
  };

"""

cfgkeymap = """\
  console.useXkbConfig = true;
  services.xserver.xkb = {
    layout = "@@kblayout@@";
    variant = "@@kbvariant@@";
  };

"""

cfgconsole = """\
  console.keyMap = "@@vconsole@@";

"""

cfgusers = """\
  users.users."@@username@@" = {
    isNormalUser = true;
    description = "@@fullname@@";
    extraGroups = [ @@groups@@ ];
  };

"""

cfgautologin = """\
  services.displayManager.autoLogin.enable = true;
  services.displayManager.autoLogin.user = "@@username@@";

"""

cfgtail = """\
  system.stateVersion = "@@nixosversion@@";
}
"""

INSTALL_PROGRESS_START = 0.31
INSTALL_PROGRESS_END = 0.94

_ACT_COPY_PATH = 100
_ACT_COPY_PATHS = 103
_ACT_BUILDS = 104
_RES_PROGRESS = 105


class NixProgress:
    def __init__(self):
        self._builds_done = 0
        self._builds_expected = 0
        self._copies_done = 0
        self._copies_expected = 0
        self._per_act_progress = {}
        self._copy_bytes = {}
        self._activities = {}
        self.fraction = 0.0
        self._floor = 0.0
        self._floor_done = 0
        self.log_messages = []

    def handle(self, line):
        line = line.strip()
        if not line:
            return True
        if not line.startswith("@nix "):
            return False
        try:
            msg = json.loads(line[5:])
        except (json.JSONDecodeError, ValueError):
            return False

        action = msg.get("action")
        if action == "start":
            self._on_start(msg)
        elif action == "stop":
            self._on_stop(msg)
        elif action == "result":
            self._on_result(msg)
        elif action == "msg":
            level = msg.get("level", 0)
            text = msg.get("msg", "")
            if level <= 1 and text:
                self.log_messages.append(text)

        self._update()
        return True

    def _on_start(self, msg):
        act_id = msg["id"]
        act_type = msg.get("type", 0)
        self._activities[act_id] = act_type
        text = msg.get("text", "")
        if text and msg.get("level", 5) <= 3:
            self.log_messages.append(text)

    def _on_stop(self, msg):
        act_id = msg["id"]
        self._activities.pop(act_id, None)
        self._copy_bytes.pop(act_id, None)

    def _on_result(self, msg):
        act_id = msg["id"]
        res_type = msg.get("type", 0)
        fields = msg.get("fields", [])
        act_type = self._activities.get(act_id, 0)

        if res_type != _RES_PROGRESS or len(fields) < 2:
            return
        if act_type == _ACT_BUILDS:
            self._per_act_progress[(act_type, act_id)] = (
                "builds",
                fields[0],
                fields[1],
            )
            self._recompute_counts()
        elif act_type == _ACT_COPY_PATHS:
            self._per_act_progress[(act_type, act_id)] = (
                "copies",
                fields[0],
                fields[1],
            )
            self._recompute_counts()
        elif act_type == _ACT_COPY_PATH:
            self._copy_bytes[act_id] = (fields[0], max(fields[1], 1))

    def _update(self):
        count_total = self._builds_expected + self._copies_expected
        count_done = self._builds_done + self._copies_done
        if count_total <= 0:
            return

        effective_total = max(count_total, 3)
        count_frac = count_done / effective_total

        copy_frac = 0.0
        if self._copy_bytes:
            done_b = sum(d for d, _t in self._copy_bytes.values())
            total_b = sum(t for _d, t in self._copy_bytes.values())
            if total_b > 0:
                copy_frac = done_b / total_b

        raw = min(0.99, 0.85 * count_frac + 0.15 * copy_frac)
        if count_done > self._floor_done:
            self._floor = self.fraction
            self._floor_done = count_done
        self.fraction = max(self._floor, raw)

    def _recompute_counts(self):
        builds = [
            (d, e)
            for kind, d, e in self._per_act_progress.values()
            if kind == "builds"
        ]
        copies = [
            (d, e)
            for kind, d, e in self._per_act_progress.values()
            if kind == "copies"
        ]
        if builds:
            self._builds_done = max(d for d, _e in builds)
            self._builds_expected = max(e for _d, e in builds)
        if copies:
            self._copies_done = max(d for d, _e in copies)
            self._copies_expected = max(e for _d, e in copies)


status = _("Installing Fray.")


def pretty_name():
    return _("Installing Fray.")


def pretty_status_message():
    return status


def catenate(d, key, *values):
    if [v for v in values if v is None]:
        return
    d[key] = "".join(values)


def env_is_set(name):
    envValue = os.environ.get(name)
    return not (envValue is None or envValue == "")


def generateProxyStrings():
    proxyEnv = []
    for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        if env_is_set(key):
            proxyEnv.append("{}={}".format(key, os.environ.get(key)))
    if proxyEnv:
        proxyEnv.insert(0, "env")
    return proxyEnv


def fix_btrfs_subvolumes(hardware_config, partitions):
    subvol_map = {"/home": "home", "/nix": "nix"}
    root_is_btrfs = False
    for part in partitions or []:
        if part.get("mountPoint") == "/" and part.get("fs") == "btrfs":
            root_is_btrfs = True
            break
    if not root_is_btrfs:
        return hardware_config
    for mount_point, correct_subvol in subvol_map.items():
        pattern = r'(fileSystems\."{}"[^;]*"subvol=)[^"]*"'.format(
            re.escape(mount_point)
        )
        replacement = r'\g<1>{}"'.format(correct_subvol)
        hardware_config = re.sub(pattern, replacement, hardware_config, flags=re.DOTALL)
    return hardware_config


def _copy_tree(src, dst):
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst)


def run():
    """Calamares job entry point."""
    global status

    gs = libcalamares.globalstorage
    root_mount_point = gs.value("rootMountPoint")
    if not root_mount_point:
        return (_("No root mount point"), _("Partitioning did not set a root."))

    variables = {}
    cfg = cfghead

    # Bootloader
    partitions = gs.value("partitions") or []
    bootdev = None
    efi = False
    btrfs_root = False
    crypt = False
    for p in partitions:
        if p.get("mountPoint") == "/boot/efi" or p.get("fs") == "fat32" and p.get(
            "mountPoint"
        ) in ("/boot", "/boot/efi"):
            if p.get("mountPoint") in ("/boot/efi", "/boot"):
                efi = True
        if p.get("mountPoint") == "/" and p.get("fs") == "btrfs":
            btrfs_root = True
        if p.get("luksMapperName"):
            crypt = True
        if p.get("device") and bootdev is None:
            # disque parent pour GRUB BIOS
            dev = p.get("device")
            if dev:
                bootdev = re.sub(r"p?\d+$", "", dev)
                if bootdev.endswith("/"):
                    bootdev = bootdev[:-1]

    fw = gs.value("firmwareType") or ""
    if fw.lower() == "efi" or efi:
        cfg += cfgbootefi
    elif bootdev:
        catenate(variables, "bootdev", bootdev)
        cfg += cfgbootbiosbtrfs if btrfs_root else cfgbootbios
        if crypt:
            cfg += cfgbootgrubcrypt
    else:
        cfg += cfgbootnone

    # Hostname
    hostname = gs.value("hostname")
    if not hostname:
        hostname = "fray"
    cfg += cfgnetwork
    catenate(variables, "hostname", str(hostname))

    # Timezone
    if gs.value("locationRegion") is not None and gs.value("locationZone") is not None:
        cfg += cfgtime
        catenate(
            variables,
            "timezone",
            gs.value("locationRegion"),
            "/",
            gs.value("locationZone"),
        )

    # Locale (toujours avec extraLocales limitées)
    locale = "fr_FR.UTF-8"
    if gs.value("localeConf") is not None:
        localeconf = dict(gs.value("localeConf"))
        if "LANG" in localeconf:
            locale = localeconf.pop("LANG").split("/")[0]
        cfg += cfglocale
        catenate(variables, "LANG", locale)
        if localeconf and (
            len(set(localeconf.values())) != 1
            or list(set(localeconf.values()))[0].split("/")[0] != locale
        ):
            cfg += cfglocaleextra
            for conf in localeconf:
                catenate(variables, conf, localeconf.get(conf).split("/")[0])
    else:
        cfg += cfglocale
        catenate(variables, "LANG", locale)

    # Keyboard
    if gs.value("keyboardLayout") is not None:
        cfg += cfgkeymap
        catenate(variables, "kblayout", gs.value("keyboardLayout") or "fr")
        catenate(variables, "kbvariant", gs.value("keyboardVariant") or "")
        if gs.value("keyboardVConsoleKeymap") is not None:
            cfg += cfgconsole
            catenate(variables, "vconsole", gs.value("keyboardVConsoleKeymap").strip())

    # User
    if gs.value("username") is not None:
        groups = ["networkmanager", "wheel", "input", "render", "video"]
        cfg += cfgusers
        catenate(variables, "username", gs.value("username"))
        catenate(variables, "fullname", gs.value("fullname") or gs.value("username"))
        catenate(
            variables,
            "groups",
            " ".join(['"' + s + '"' for s in groups]),
        )
        if gs.value("autoLoginUser") is not None:
            cfg += cfgautologin

    cfg += cfgtail
    version = ".".join(subprocess.getoutput(["nixos-version"]).split(".")[:2])[:5]
    catenate(variables, "nixosversion", version or "25.11")

    for key in list(variables.keys()):
        pattern = "@@{key}@@".format(key=key)
        if pattern not in cfg:
            libcalamares.utils.warning(
                "Variable '{key}' is not used.".format(key=key)
            )

    for match in re.compile(r"@@\w+@@").finditer(cfg):
        variable_name = cfg[match.start() + 2 : match.end() - 2]
        if variable_name not in variables:
            libcalamares.utils.warning(
                "Variable '{key}' is used but not defined.".format(key=variable_name)
            )

    for key in variables.keys():
        cfg = cfg.replace("@@{key}@@".format(key=key), str(variables[key]))

    status = _("Generating NixOS configuration")
    libcalamares.job.setprogress(0.05)

    try:
        subprocess.check_output(
            ["pkexec", "nixos-generate-config", "--root", root_mount_point],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        out = e.output.decode("utf8") if e.output is not None else str(e)
        libcalamares.utils.error(out)
        return (_("nixos-generate-config failed"), _(out))

    hw_path = os.path.join(root_mount_point, "etc/nixos/hardware-configuration.nix")
    with open(hw_path, "r") as hf:
        htxt = hf.read()
    htxt_fixed = fix_btrfs_subvolumes(htxt, partitions)
    if htxt_fixed != htxt:
        libcalamares.utils.host_env_process_output(
            ["cp", "/dev/stdin", hw_path], None, htxt_fixed
        )
    hw_backup = htxt_fixed

    # Copier le flake Fray depuis l'ISO
    status = _("Copying Fray flake")
    libcalamares.job.setprogress(0.15)

    iso_cfg = "/iso/iso-cfg"
    dest_nixos = os.path.join(root_mount_point, "etc/nixos")
    os.makedirs(dest_nixos, exist_ok=True)

    if not os.path.isdir(iso_cfg):
        return (
            _("Fray flake missing on ISO"),
            _("Expected {} (isoImage.contents). Rebuild the ISO.").format(iso_cfg),
        )

    # Fichiers / dossiers nécessaires au flake
    for name in ("flake.nix", "flake.lock", "customConfig", "hosts"):
        src = os.path.join(iso_cfg, name)
        dst = os.path.join(dest_nixos, name)
        if not os.path.exists(src):
            return (
                _("Incomplete Fray flake on ISO"),
                _("Missing {}").format(src),
            )
        try:
            subprocess.run(["sudo", "rm", "-rf", dst], check=False)
            subprocess.run(["sudo", "cp", "-a", src, dst], check=True)
        except subprocess.CalledProcessError as e:
            return (_("Failed to copy Fray flake"), str(e))

    # Écrire calamares-generated.nix (après la copie pour ne pas l'écraser)
    gen_path = os.path.join(dest_nixos, "calamares-generated.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", gen_path], None, cfg
    )

    # Restaurer hardware-configuration (la copie hosts/ ne l'inclut pas, mais
    # nixos-generate-config l'a déjà créé ; s'assurer qu'il est intact)
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", hw_path], None, hw_backup
    )
    try:
        subprocess.run(["sudo", "chmod", "644", hw_path, gen_path], check=False)
        subprocess.run(
            ["sudo", "chown", "root:root", hw_path, gen_path], check=False
        )
    except Exception:
        pass

    # Sécuriser chemins nix / tmp
    status = _("Installing Fray")
    libcalamares.job.setprogress(INSTALL_PROGRESS_START)

    try:
        subprocess.check_output(
            ["pkexec", "chmod", "755", root_mount_point],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        libcalamares.utils.warning(
            "Failed to set permissions on {}: {}".format(root_mount_point, e.output)
        )

    secure_tmpdir = os.path.join(root_mount_point, "var/tmp/nix-installer")
    for d, mode in (
        (secure_tmpdir, "0700"),
        (os.path.join(root_mount_point, "nix"), "0755"),
        (os.path.join(root_mount_point, "nix/var"), "0755"),
        (os.path.join(root_mount_point, "nix/var/nix"), "0755"),
        (os.path.join(root_mount_point, "nix/var/nix/builds"), "0755"),
    ):
        try:
            libcalamares.utils.host_env_process_output(["mkdir", "-p", d], None)
            libcalamares.utils.host_env_process_output(["chmod", mode, d], None)
        except Exception as e:
            libcalamares.utils.warning("mkdir/chmod {}: {}".format(d, e))

    nixosInstallCmd = ["pkexec"]
    nixosInstallCmd.extend(generateProxyStrings())
    nixosInstallCmd.extend(
        [
            "nixos-install",
            "--no-root-passwd",
            "--root",
            root_mount_point,
            "--flake",
            "{}#fray".format(dest_nixos),
            "--option",
            "sandbox",
            "false",
            "--option",
            "build-users-group",
            "",
            "--option",
            "build-dir",
            "/nix/var/nix/builds",
            "--log-format",
            "internal-json",
        ]
    )

    progress = NixProgress()
    try:
        install_env = os.environ.copy()
        install_env["TMPDIR"] = secure_tmpdir
        proc = subprocess.Popen(
            nixosInstallCmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=install_env,
        )
        output = ""
        while True:
            raw = proc.stdout.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace")
            output += line
            if not progress.handle(line):
                libcalamares.utils.debug("nixos-install: {}".format(line.strip()))
            frac = INSTALL_PROGRESS_START + progress.fraction * (
                INSTALL_PROGRESS_END - INSTALL_PROGRESS_START
            )
            libcalamares.job.setprogress(frac)
        exit_code = proc.wait()
        if exit_code != 0:
            return (_("nixos-install failed"), _(output))
    except Exception as e:
        return (_("nixos-install failed"), _(str(e)))

    # Mot de passe utilisateur (module users Calamares s'en charge ensuite en chroot)
    libcalamares.job.setprogress(INSTALL_PROGRESS_END)
    status = _("Fray installation finished")
    return None
