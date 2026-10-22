# Branding Fray - logo 10 (`10-seal-fray`)

Logo officiel : sceau Fray (store `media/logos/10-seal-fray.{svg,png}`).

## Assets dans le tree

| Fichier | Rôle |
|---|---|
| `customConfig/branding/assets/logo/10-seal-fray.svg` | Logo vectoriel |
| `customConfig/branding/assets/logo/10-seal-fray.png` | Raster + GDM |
| `customConfig/branding/assets/logo/fray-logo-{16..256}.png` | Icônes hicolor |
| `customConfig/branding/assets/wallpaper/fray-gaming-arena.png` | Fond gaming |
| `customConfig/branding/plymouth/` | Thème Plymouth `fray` |

## Modules

| Option | Fichier | Effet |
|---|---|---|
| `fray.branding.enable` | `customConfig/branding/default.nix` | Paquet `fray-branding`, logo GDM, `FRAY_BRANDING` |
| `fray.boot.plymouth.enable` | `customConfig/boot/plymouth.nix` | Thème `fray` + `plymouth-fray` |
| Plasma | `customConfig/desktop/kde/plasma.nix` | Hint wallpaper + icône apps `fray` |
| DE switch / wallpaper .desktop | `icon = "fray"` | Boutons / lanceurs |

## Où le logo apparaît

1. **Plymouth** (boot) - `logo.png` centré + anneau progress  
2. **GDM** - `services.displayManager.gdm.logo`  
3. **Icônes** - `hicolor/*/apps/fray.png` (menus Plasma / GNOME)  
4. **Calamares** - `iso-cfg/calamares/branding/fray/`  
5. **Wallpaper tool** - fonds sous `$FRAY_BRANDING/share/backgrounds/fray/`

Activer : `fray.branding.enable = true` (déjà dans `hosts/iso.nix`).
