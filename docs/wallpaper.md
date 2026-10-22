# fray-wallpaper

Outil Rust **hexagonal** (comme `fray-disk` / `fray-de-switch`) pour lister et appliquer les fonds Fray.

## Chemins

- Sources : `customConfig/apps/wallpaper/`
- Module : `customConfig/apps/wallpaper.nix` -> `fray.apps.wallpaper.enable`
- Image livrée : `customConfig/branding/assets/wallpaper/fray-gaming-arena.png`

## Commandes

```bash
fray-wallpaper list
fray-wallpaper set fray-gaming-arena
fray-wallpaper set /chemin/vers/image.png
fray-wallpaper current
fray-wallpaper explain
```

## DE

| DE | Backend |
|---|---|
| GNOME | `gsettings` picture-uri / dark |
| Plasma | `plasma-apply-wallpaperimage` |
| Niri / autre | `swww img` si présent, sinon état dans `~/.local/share/fray/wallpaper-current` |
