# Fray

NixOS gaming personnel - quatre bureaux (GNOME, Niri, Plasma, Mango+DMS).

## Emplacement

```
/home/kouro/Téléchargements/GLF pc/NIX/fray/
```

Docs : `DOC/` pointe vers `../DOC` (copie locale). Ancienne version : `../fray-old-archive/`.

## Structure

```
flake.nix / flake.lock
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
  gaming/             # lutris, gamemode, gamescope...
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

## ISO

```bash
cd "/home/kouro/Téléchargements/GLF pc/NIX/fray"
nix build .#iso -L -o result-iso
# voir docs/iso-calamares.md
```

## Outils

| Commande | Rôle |
|---|---|
| `fray-update` / `fray-update --switch` | CLI update unifiée |
| `fray-apply` | Éditeur / apply Python (`customConfig/apps/fray-apply/`) |
| `fray-wallpaper` | Fonds Fray (Rust hexa) |
| Catalogue | `customConfig/catalog/` puis `/etc/fray/catalog.json` |

Logo officiel : **10-seal-fray** - voir `docs/branding-logo10.md`.

Rust update-manager GLF : **pas encore** (apply = Python pour l'instant).

## Interdit

- Écrire sous `/etc/nixos` / `glf-switch` sans ordre
- Rebuild hôte GLF via `fray-update --switch`
