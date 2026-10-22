# Fray Apply (Python)

Éditeur GTK pour `customConfig/` — **apply** Fray en attendant le port Rust.

- Binaire : `fray-apply`
- Source : GLF Config Editor, renommé / chemins `FRAY_FLAKE`, CLI `fray-update`
- Rust « apply en rust » (update-manager GLF) : **pas encore** dans ce tree

```bash
# Dev rapide (hors Nix)
FRAY_FLAKE="/home/kouro/Téléchargements/GLF pc/NIX/fray" python3 ./fray-apply.py
```

Sur VM Fray : `fray.apps.apply.enable = true` (déjà dans `hosts/vm.nix`).
