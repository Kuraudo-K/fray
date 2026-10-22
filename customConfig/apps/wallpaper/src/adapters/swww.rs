//! Applier composite : GNOME / Plasma / swww (niri) / copie état

use crate::domain::{DesktopKind, WallpaperError, WallpaperResult};
use crate::ports::WallpaperApplier;
use std::fs;
use std::process::Command;

use super::{GnomeApplier, PlasmaApplier};

pub struct CompositeApplier;

impl WallpaperApplier for CompositeApplier {
    fn apply(&self, desktop: DesktopKind, path: &str) -> WallpaperResult<()> {
        match desktop {
            DesktopKind::Gnome => GnomeApplier.apply(desktop, path),
            DesktopKind::Plasma => PlasmaApplier.apply(desktop, path),
            DesktopKind::Niri | DesktopKind::Other => {
                if let Some(home) = dirs::home_dir() {
                    let state = home.join(".local/share/fray/wallpaper-current");
                    if let Some(parent) = state.parent() {
                        let _ = fs::create_dir_all(parent);
                    }
                    fs::write(&state, path).map_err(|e| WallpaperError::Io(e.to_string()))?;
                }
                match Command::new("swww").args(["img", path]).status() {
                    Ok(st) if st.success() => Ok(()),
                    Ok(st) => Err(WallpaperError::Io(format!(
                        "swww img a échoué ({st}) — chemin noté dans ~/.local/share/fray/"
                    ))),
                    Err(_) => Err(WallpaperError::Unsupported(format!(
                        "DE {} : installe swww ou applique manuellement (chemin noté)",
                        desktop.as_str()
                    ))),
                }
            }
        }
    }

    fn current(&self, desktop: DesktopKind) -> WallpaperResult<Option<String>> {
        match desktop {
            DesktopKind::Gnome => GnomeApplier.current(desktop),
            DesktopKind::Plasma => PlasmaApplier.current(desktop),
            DesktopKind::Niri | DesktopKind::Other => {
                if let Some(home) = dirs::home_dir() {
                    let state = home.join(".local/share/fray/wallpaper-current");
                    if state.is_file() {
                        let s = fs::read_to_string(state)
                            .map_err(|e| WallpaperError::Io(e.to_string()))?;
                        return Ok(Some(s.trim().to_string()));
                    }
                }
                Ok(None)
            }
        }
    }
}
