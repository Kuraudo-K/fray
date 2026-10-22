//! Inventaire des fonds Fray / système / utilisateur

use crate::domain::{Wallpaper, WallpaperError, WallpaperResult, WallpaperSource};
use crate::ports::WallpaperCatalog;
use std::fs;
use std::path::{Path, PathBuf};

pub struct FsCatalog {
    pub roots: Vec<(PathBuf, WallpaperSource)>,
}

impl Default for FsCatalog {
    fn default() -> Self {
        let mut roots = Vec::new();
        if let Ok(branding) = std::env::var("FRAY_BRANDING") {
            let base = PathBuf::from(branding);
            roots.push((base.join("share/backgrounds/fray"), WallpaperSource::Fray));
            roots.push((
                base.join("share/backgrounds/gnome"),
                WallpaperSource::Fray,
            ));
        }
        roots.push((
            PathBuf::from("/run/current-system/sw/share/backgrounds/fray"),
            WallpaperSource::Fray,
        ));
        roots.push((
            PathBuf::from("/run/current-system/sw/share/backgrounds/gnome"),
            WallpaperSource::System,
        ));
        if let Some(home) = dirs::home_dir() {
            roots.push((home.join(".local/share/backgrounds"), WallpaperSource::User));
            roots.push((home.join("Images"), WallpaperSource::User));
            roots.push((home.join("Pictures"), WallpaperSource::User));
        }
        Self { roots }
    }
}

fn is_image(path: &Path) -> bool {
    matches!(
        path.extension()
            .and_then(|e| e.to_str())
            .map(|e| e.to_ascii_lowercase())
            .as_deref(),
        Some("png" | "jpg" | "jpeg" | "webp" | "jxl")
    )
}

impl WallpaperCatalog for FsCatalog {
    fn list(&self) -> WallpaperResult<Vec<Wallpaper>> {
        let mut out = Vec::new();
        let mut seen = std::collections::BTreeSet::new();
        for (root, source) in &self.roots {
            if !root.is_dir() {
                continue;
            }
            let entries = fs::read_dir(root).map_err(|e| WallpaperError::Io(e.to_string()))?;
            for ent in entries.flatten() {
                let path = ent.path();
                if !path.is_file() || !is_image(&path) {
                    continue;
                }
                let path_str = path.display().to_string();
                if !seen.insert(path_str.clone()) {
                    continue;
                }
                let id = path
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("wallpaper")
                    .to_string();
                out.push(Wallpaper {
                    id,
                    path: path_str,
                    source: *source,
                });
            }
        }
        out.sort_by(|a, b| a.id.cmp(&b.id));
        Ok(out)
    }
}
