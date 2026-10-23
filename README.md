# Fray

NixOS gaming (GNOME + PaperWM, KDE Plasma 6).

## Clone

```bash
git clone https://github.com/Kuraudo-K/fray.git
cd fray
```

## ISO

```bash
nix build .#iso -L -o result-iso
# image : result-iso/iso/*.iso
```

Flasher l'ISO sur une clé/SSD (vérifier le disque avec `lsblk`), boot live, puis **Install Fray** (Calamares).

Après install : clone ce flake et `fray-update --switch` (ou `nh` / `nixos-rebuild` avec le flake).

## Modules

`customConfig/` - options `fray.*.enable`. Logo : **04gr10-charcoal-crimson**.
