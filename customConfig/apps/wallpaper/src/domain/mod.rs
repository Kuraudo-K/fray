//! Domaine : fonds d'écran - zéro I/O

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Wallpaper {
    pub id: String,
    pub path: String,
    pub source: WallpaperSource,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WallpaperSource {
    Fray,
    System,
    User,
}

impl WallpaperSource {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Fray => "fray",
            Self::System => "system",
            Self::User => "user",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DesktopKind {
    Gnome,
    Plasma,
    Niri,
    Other,
}

impl DesktopKind {
    pub fn detect(xdg_desktop: &str, xdg_session: &str) -> Self {
        let hay = format!("{xdg_desktop};{xdg_session}").to_lowercase();
        if hay.contains("gnome") {
            Self::Gnome
        } else if hay.contains("kde") || hay.contains("plasma") {
            Self::Plasma
        } else if hay.contains("niri") {
            Self::Niri
        } else {
            Self::Other
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::Gnome => "gnome",
            Self::Plasma => "plasma",
            Self::Niri => "niri",
            Self::Other => "other",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WallpaperError {
    Io(String),
    NotFound(String),
    Unsupported(String),
}

impl std::fmt::Display for WallpaperError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(s) | Self::NotFound(s) | Self::Unsupported(s) => write!(f, "{s}"),
        }
    }
}

impl std::error::Error for WallpaperError {}

pub type WallpaperResult<T> = Result<T, WallpaperError>;

pub fn find_by_id<'a>(list: &'a [Wallpaper], id_or_path: &str) -> Option<&'a Wallpaper> {
    list.iter().find(|w| w.id == id_or_path || w.path == id_or_path)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detect_gnome() {
        assert_eq!(
            DesktopKind::detect("GNOME", "wayland"),
            DesktopKind::Gnome
        );
    }

    #[test]
    fn detect_plasma() {
        assert_eq!(DesktopKind::detect("KDE", "wayland"), DesktopKind::Plasma);
    }
}
