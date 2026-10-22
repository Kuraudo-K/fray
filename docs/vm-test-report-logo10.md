# Rapport tests VM Fray — logo 10 / branding / wallpaper

Date : 2026-10-22  
Projet : `/home/kouro/Téléchargements/GLF pc/NIX/fray/`  
Commit : `fe534df` (main + branche `cursor/logo10-branding-iso-vm-463f`)  
Accès tests : `sshpass` non-interactif (mdp VM documenté `fray`, port `2222`) — **aucun** SSH_ASKPASS / popup.  
QEMU **arrêté** en fin de campagne. Hôte GLF / `/etc/nixos` **non touchés**.

Légende : **OK** / **KO** / **PARTIEL** / **N/A**

## Branding logo 10

| Item | Statut | Notes |
|---|---|---|
| `10-seal-fray.png` / `.svg` sous `/sw/share/fray/logo/` | **OK** | |
| Icône hicolor `fray.svg` | **OK** | |
| Wallpaper `fray-gaming-arena` (fray + gnome + Plasma) | **OK** | |
| `FRAY_BRANDING` | **OK** | store path fray-branding |
| Plymouth thème `fray` (fichiers live) | **N/A** | `fray.boot.plymouth.enable=false` en VM QEMU (attendu) |
| GDM logo dconf | **N/A** | headless ; config présente dans module |

## Wallpaper tool

| Item | Statut | Notes |
|---|---|---|
| `fray-wallpaper` binaire | **OK** | |
| `list` voit `fray-gaming-arena` | **OK** | source `fray` |
| `explain` | **OK** | |

## Système / DE / gaming / apps (reprise checklist)

| Zone | Statut |
|---|---|
| Boot multi-user `running`, hostname `fray-vm` | **OK** |
| NetworkManager, firewall nft | **OK** |
| Bluetooth | **PARTIEL** (inactive VM headless) |
| zram, fstrim.timer, nix-ld, nh 4.4.2 | **OK** |
| ntsync + xpadneo, sysctl map_count / split_lock | **OK** |
| Sessions : gnome/niri/plasma/mango via `fray-de-switch list` | **OK** |
| Extensions GNOME (10) | **OK** |
| Steam, Heroic, gamemode, gamescope, MangoHud, umu, vkBasalt | **OK** |
| input-remapper actif | **OK** |
| Firefox, kitty, calc, fray-disk, fray-update, fray-apply | **OK** |
| Flathub + timers auto-update | **OK** |
| GUI / jeu interactif | **N/A** |

## Synthèse

| | |
|---|---|
| **OK** | ~majorité checklist + branding + wallpaper |
| **KO bloquants** | **0** |
| **PARTIEL** | bluetooth VM |
| **N/A** | Plymouth boot réel, GDM GUI, jeux |

**SSH** : BatchMode sans clé = fail (attendu) ; `sshpass -p fray` = **OK** sans popup.
