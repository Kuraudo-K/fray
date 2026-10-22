use crate::domain::{DesktopKind, WallpaperError, WallpaperResult};
use crate::ports::WallpaperApplier;
use std::process::Command;

pub struct GnomeApplier;

impl WallpaperApplier for GnomeApplier {
    fn apply(&self, desktop: DesktopKind, path: &str) -> WallpaperResult<()> {
        if desktop != DesktopKind::Gnome {
            return Err(WallpaperError::Unsupported(
                "GnomeApplier réservé à GNOME".into(),
            ));
        }
        let uri = format!("file://{path}");
        for key in ["picture-uri", "picture-uri-dark"] {
            let status = Command::new("gsettings")
                .args(["set", "org.gnome.desktop.background", key, &uri])
                .status()
                .map_err(|e| WallpaperError::Io(e.to_string()))?;
            if !status.success() {
                return Err(WallpaperError::Io(format!(
                    "gsettings {key} a échoué (code {status})"
                )));
            }
        }
        let _ = Command::new("gsettings")
            .args([
                "set",
                "org.gnome.desktop.screensaver",
                "picture-uri",
                &uri,
            ])
            .status();
        Ok(())
    }

    fn current(&self, desktop: DesktopKind) -> WallpaperResult<Option<String>> {
        if desktop != DesktopKind::Gnome {
            return Ok(None);
        }
        let out = Command::new("gsettings")
            .args(["get", "org.gnome.desktop.background", "picture-uri"])
            .output()
            .map_err(|e| WallpaperError::Io(e.to_string()))?;
        if !out.status.success() {
            return Ok(None);
        }
        let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
        let s = s.trim_matches('\'').trim_start_matches("file://").to_string();
        if s.is_empty() {
            Ok(None)
        } else {
            Ok(Some(s))
        }
    }
}
