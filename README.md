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
hosts/iso.nix         # ISO optionnelle (légère)
customConfig/
  desktop/gnome/      # PaperWM
  desktop/niri/       # Noctalia
  desktop/kde/        # Plasma 6
  desktop/mango/      # MangoWM + DankMaterialShell
  desktop/de-switch.nix
  gaming/launchers/   # Steam, Heroic, Faugus
  gaming/             # lutris, 8bitdo (opt), gamemode…
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

## Interdit

- Écrire sous `/etc/nixos` / `glf-switch` sans ordre
- Push GitHub sans accord
