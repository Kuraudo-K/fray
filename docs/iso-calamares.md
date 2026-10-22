# ISO Fray + Calamares

## Build

```bash
cd "/home/kouro/Téléchargements/GLF pc/NIX/fray"
nix build .#iso -L -o result-iso
```

Artefact typique :

```
result-iso/iso/fray-*-x86_64-linux.iso
```

Copie durable recommandée :

```bash
mkdir -p iso
cp -L result-iso/iso/*.iso iso/
ls -lh iso/
```

## Contenu live

- GNOME + PaperWM (léger)
- Calamares autostart (branding Fray, logo 10)
- `fray-wallpaper`, branding, Plymouth thème `fray`
- Pas de Steam/Heroic sur l'ISO (poids) - profil VM/complet après install

## Flasher (toi-même, SSD de test)

```bash
# Vérifier le périphérique (DANGER : mauvais disque = perte de données)
lsblk

# Exemple (adapter /dev/sdX) :
sudo dd if=iso/fray-….iso of=/dev/sdX bs=4M status=progress oflag=sync
# ou Ventoy / balenaEtcher / Fedora Media Writer
```

Boot USB, puis session live, puis **Install Fray** (Calamares), partitionne le SSD de test, puis reboot.

Après install stock NixOS via Calamares, clone le flake Fray et :

```bash
fray-update --switch
# ou nh / nixos-rebuild avec le flake Kuraudo-K/fray
```

L'agent ne flashe **pas** le SSD sans demande explicite.
