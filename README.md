# Fray

NixOS gaming personnel (GNOME + PaperWM, ou Niri + Noctalia).

## Emplacement

```
/home/kouro/Téléchargements/GLF pc/NIX/fray/
```

Ancienne version : `../fray-old-archive/`.

## Structure

```
flake.nix / flake.lock
hosts/vm.nix          # machine de test
hosts/iso.nix         # ISO optionnelle
customConfig/
  desktop/gnome/      # PaperWM
  desktop/niri/       # Noctalia
  desktop/de-switch.nix
  gaming/launchers/   # Steam, Heroic, Faugus
  gaming/             # gamemode, gamescope, mangohud, proton
  hardware/ apps/ services/ system/
```

## Bureaux

| Session | Contenu |
|---|---|
| `gnome` | GNOME + PaperWM |
| `niri` | Niri + Noctalia |

Basculer : `fray-de-switch switch gnome|niri`  
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
