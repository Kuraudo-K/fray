# Fray Editor Config (Python)

Éditeur GTK pour `customConfig/` - apply Fray.

- Nom UI : **Fray Editor Config**
- Binaire : `fray-apply`
- Icône : `04gr10-charcoal-crimson`
- CLI : `fray-update` / `fray-update --switch`
- Reboot proposé seulement après succès (`--switch` / nh)

```bash
# Dev rapide (hors Nix)
FRAY_FLAKE="/home/kouro/Téléchargements/GLF pc/NIX/fray" python3 ./fray-apply.py
```

Activer : `fray.apps.apply.enable = true`.
