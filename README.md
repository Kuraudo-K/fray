# Fray

NixOS gaming perso — **pas** un fork GLF-OS.

## Emplacement

```
/home/kouro/Téléchargements/GLF pc/NIX/fray/
```

Archive ancienne version : `../fray-old-archive/`.  
Docs Nixerion à côté (`00B__…`, `00C__…`) — non touchés.

## Structure

```
flake.nix          # inputs → flake.lock (apps pinées)
hosts/vm.nix       # seule machine de test
hosts/iso.nix      # ISO optionnelle
customConfig/      # tout le custom, 1 module = 1 enable
  desktop/         # GNOME+PaperWM, Niri+Noctalia, de-switch Rust
  gaming/ hardware/ apps/ services/ system/
```

## DE

| DE | Session greeter | Shell |
|---|---|---|
| A | `gnome` | GNOME + PaperWM |
| B | `niri` | Niri + Noctalia |

Switcher : `fray-de-switch switch gnome|niri` (persistance `~/.local/share/fray/de-profiles/`).

## Build VM

```bash
cd "/home/kouro/Téléchargements/GLF pc/NIX/fray"
git add -A
nix build .#vm -L
./result/bin/run-fray-vm-vm
# SSH : ssh -p 2222 root@127.0.0.1   (mdp: fray)
```

## Interdit

- Écrire sous `/etc/nixos` / `glf-switch`
- Push GitHub sans accord
