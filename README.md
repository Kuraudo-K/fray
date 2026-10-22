# Fray

NixOS gaming personnel — quatre bureaux (GNOME, Niri, Plasma, Mango+DMS).

## Emplacement

```
/home/kouro/Téléchargements/GLF pc/NIX/fray/
```

Docs : `DOC/` → `../DOC` (copie locale). Ancienne version : `../fray-old-archive/`.

## Structure

```
flake.nix / flake.lock
hosts/vm.nix          # machine de test (4 DE)
hosts/iso.nix         # ISO Calamares (logo 10)
iso-cfg/              # branding Calamares Fray
customConfig/
  branding/           # logo 10-seal-fray, wallpaper, Plymouth
  desktop/gnome/      # PaperWM
  desktop/niri/       # Noctalia
  desktop/kde/        # Plasma 6
  desktop/mango/      # MangoWM + DankMaterialShell
  desktop/de-switch.nix
  gaming/launchers/   # Steam, Heroic, Faugus
  gaming/             # lutris, gamemode, gamescope…
  hardware/ apps/ services/ system/ boot/
```

## Bureaux

| Session | Contenu |
|---|---|
| `gnome` | GNOME + PaperWM |
| `niri` | Niri + Noctalia |
| `plasma` | KDE Plasma 6 |
| `mango` | MangoWM + DankMaterialShell |

Basculer : `fray-de-switch switch gnome|niri|plasma|mango`  
Profils : `~/.local/share/fray/de-profiles/`

## Build VM

```bash
cd "/home/kouro/Téléchargements/GLF pc/NIX/fray"
git add -A
nix build .#vm -L
./result/bin/run-fray-vm-vm
# SSH : ssh -p 2222 root@127.0.0.1   (mdp: fray)
```

## Outils

| Commande | Rôle |
|---|---|
| `fray-update` / `fray-update --switch` | CLI update unifiée |
| `fray-apply` | Éditeur / apply Python (`customConfig/apps/fray-apply/`) |
| `fray-wallpaper` | Fonds Fray (Rust hexa) |
| Catalogue | `customConfig/catalog/` → `/etc/fray/catalog.json` |

Logo officiel : **10-seal-fray** — voir `docs/branding-logo10.md`.  
ISO : `nix build .#iso -o result-iso` — voir `docs/iso-calamares.md`.

Rust update-manager GLF : **pas encore** (apply = Python pour l’instant).

## Interdit

- Écrire sous `/etc/nixos` / `glf-switch` sans ordre
- Rebuild hôte GLF via `fray-update --switch`
