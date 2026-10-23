use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::LazyLock;
use std::time::Duration;

use regex::Regex;

use crate::adapters::process;
use crate::ports::{IconLocator, ThemePort};

pub struct DesktopThemeDetector;

impl ThemePort for DesktopThemeDetector {
    fn prefers_dark(&self) -> bool {
        system_prefers_dark()
    }
}

pub struct EnvIconLocator;

impl IconLocator for EnvIconLocator {
    fn resolve_png(&self) -> Option<PathBuf> {
        if let Ok(env_icon) = env::var("FRAY_UM_ICON") {
            let path = PathBuf::from(env_icon.trim());
            if path.is_file()
                && path
                    .extension()
                    .is_some_and(|ext| ext.eq_ignore_ascii_case("png"))
            {
                return Some(path);
            }
        }
        for size in [256, 128, 48] {
            for base in [
                format!(
                    "/run/current-system/sw/share/icons/hicolor/{size}x{size}/apps/fray-update-manager.png"
                ),
                format!("/usr/share/icons/hicolor/{size}x{size}/apps/fray-update-manager.png"),
            ] {
                let path = PathBuf::from(base);
                if path.is_file() {
                    return Some(path);
                }
            }
        }
        if let Ok(cwd) = env::current_dir() {
            let png = cwd.join("fray-update-manager.png");
            if png.is_file() {
                return Some(png);
            }
        }
        None
    }
}

pub fn system_prefers_dark() -> bool {
    if let Ok(forced) = env::var("FRAY_UM_THEME") {
        let forced = forced.trim().to_lowercase();
        if matches!(forced.as_str(), "dark" | "sombre" | "1" | "true" | "night") {
            return true;
        }
        if matches!(forced.as_str(), "light" | "clair" | "0" | "false" | "day") {
            return false;
        }
    }

    if desktop_is_kde() {
        if let Some(dark) = kde_prefers_dark() {
            return dark;
        }
        if let Some(dark) = portal_color_scheme() {
            return dark;
        }
        if let Some(dark) = gtk_settings_prefer_dark() {
            return dark;
        }
        return false;
    }

    // GNOME / autre : gsettings + portal d'abord.
    // Ne pas lire ~/.config/gtk-*/settings.ini en premier (souvent un reste Plasma
    // qui force le sombre alors que GNOME est en clair).
    if desktop_is_gnome() {
        if let Some(dark) = gnome_prefers_dark() {
            return dark;
        }
        if let Some(dark) = portal_color_scheme() {
            return dark;
        }
        if let Ok(theme) = env::var("GTK_THEME") {
            if let Some(dark) = name_looks_dark(&theme) {
                return dark;
            }
        }
        return false;
    }

    if let Some(dark) = portal_color_scheme() {
        return dark;
    }
    if let Some(dark) = gnome_prefers_dark() {
        return dark;
    }
    if let Some(dark) = gtk_settings_prefer_dark() {
        return dark;
    }
    if let Ok(theme) = env::var("GTK_THEME") {
        if let Some(dark) = name_looks_dark(&theme) {
            return dark;
        }
    }
    false
}

pub fn desktop_is_kde() -> bool {
    let blob = format!(
        "{} {} {}",
        env::var("XDG_CURRENT_DESKTOP").unwrap_or_default(),
        env::var("DESKTOP_SESSION").unwrap_or_default(),
        env::var("XDG_SESSION_DESKTOP").unwrap_or_default()
    )
    .to_lowercase();
    blob.contains("kde") || blob.contains("plasma")
}

pub fn desktop_is_gnome() -> bool {
    let blob = format!(
        "{} {} {}",
        env::var("XDG_CURRENT_DESKTOP").unwrap_or_default(),
        env::var("DESKTOP_SESSION").unwrap_or_default(),
        env::var("XDG_SESSION_DESKTOP").unwrap_or_default()
    )
    .to_lowercase();
    blob.contains("gnome")
}

fn portal_color_scheme() -> Option<bool> {
    static NUM_RE: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"\bu?int32\s+(\d+)\b|\b(\d+)\b").expect("portal regex"));
    let methods = [
        (
            "org.freedesktop.portal.Settings.Read",
            ["org.freedesktop.appearance", "color-scheme"],
        ),
        (
            "org.freedesktop.portal.Settings.ReadOne",
            ["org.freedesktop.appearance", "color-scheme"],
        ),
    ];
    for object_path in [
        "/org/freedesktop/portal/desktop",
        "/org/freedesktop/portal/Desktop",
    ] {
        for (method, args) in methods {
            let mut cmd = Command::new("gdbus");
            cmd.args([
                "call",
                "--session",
                "--dest",
                "org.freedesktop.portal.Desktop",
                "--object-path",
                object_path,
                "--method",
                method,
                args[0],
                args[1],
            ]);
            let Ok(output) = process::capture(cmd, Duration::from_secs(2)) else {
                continue;
            };
            let text = process::lossy(&output.stdout);
            let mut vals = Vec::new();
            for caps in NUM_RE.captures_iter(&text) {
                let Some(raw) = caps.get(1).or_else(|| caps.get(2)) else {
                    continue;
                };
                if let Ok(value) = raw.as_str().parse::<i32>() {
                    vals.push(value);
                }
            }
            let Some(code) = vals.last().copied() else {
                continue;
            };
            if code == 1 {
                return Some(true);
            }
            if code == 2 {
                return Some(false);
            }
        }
    }
    None
}

fn gtk_settings_prefer_dark() -> Option<bool> {
    static RE: LazyLock<Regex> = LazyLock::new(|| {
        Regex::new(r"(?im)^\s*gtk-application-prefer-dark-theme\s*=\s*([01]|true|false)\s*$")
            .expect("gtk ini regex")
    });
    let home = home_dir();
    for relative in ["gtk-3.0/settings.ini", "gtk-4.0/settings.ini"] {
        let path = home.join(".config").join(relative);
        let Ok(bytes) = std::fs::read(&path) else {
            continue;
        };
        let text = String::from_utf8_lossy(&bytes);
        let Some(caps) = RE.captures(&text) else {
            continue;
        };
        match caps.get(1).map(|m| m.as_str().to_lowercase()).as_deref() {
            Some("1") | Some("true") => return Some(true),
            Some("0") | Some("false") => return Some(false),
            _ => continue,
        }
    }
    None
}

fn kde_prefers_dark() -> Option<bool> {
    if let Some(dark) = kde_luminance_dark() {
        return Some(dark);
    }
    for name in ["kreadconfig6", "kreadconfig5"] {
        let Some(bin) = kread_bin(name) else {
            continue;
        };
        for (group, key) in [("General", "ColorScheme"), ("KDE", "LookAndFeelPackage")] {
            let mut cmd = Command::new(&bin);
            cmd.args(["--file", "kdeglobals", "--group", group, "--key", key]);
            if let Ok(output) = process::capture(cmd, Duration::from_secs(2)) {
                let value = process::lossy(&output.stdout);
                if let Some(dark) = name_looks_dark(value.trim()) {
                    return Some(dark);
                }
            }
        }
    }
    kde_name_from_files()
}

fn kde_luminance_dark() -> Option<bool> {
    let home = home_dir();
    for path in [
        home.join(".config/kdeglobals"),
        home.join(".config/kdedefaults/kdeglobals"),
    ] {
        let Ok(bytes) = std::fs::read(&path) else {
            continue;
        };
        let text = String::from_utf8_lossy(&bytes);
        for section in ["Colors:View", "Colors:Window"] {
            let pattern = format!(
                r"(?ims)^\s*\[{}\]\s*$(.*?)(?=^\s*\[|\Z)",
                regex::escape(section)
            );
            let Ok(re) = Regex::new(&pattern) else {
                continue;
            };
            let Some(body) = re.captures(&text).and_then(|c| c.get(1)) else {
                continue;
            };
            static BG: LazyLock<Regex> = LazyLock::new(|| {
                Regex::new(r"(?im)^\s*BackgroundNormal\s*=\s*(.+?)\s*$").expect("bg regex")
            });
            let Some(color) = BG.captures(body.as_str()).and_then(|c| c.get(1)) else {
                continue;
            };
            let Some(rgb) = parse_rgb(color.as_str()) else {
                continue;
            };
            return Some(luma(rgb) < 128.0);
        }
    }
    None
}

fn kde_name_from_files() -> Option<bool> {
    let home = home_dir();
    for path in [
        home.join(".config/kdeglobals"),
        home.join(".config/kdedefaults/kdeglobals"),
    ] {
        let Ok(bytes) = std::fs::read(&path) else {
            continue;
        };
        let text = String::from_utf8_lossy(&bytes);
        for key in ["ColorScheme", "LookAndFeelPackage"] {
            let pattern = format!(r"(?im)^\s*{key}\s*=\s*(.+?)\s*$");
            let Ok(re) = Regex::new(&pattern) else {
                continue;
            };
            let Some(value) = re.captures(&text).and_then(|c| c.get(1)) else {
                continue;
            };
            if let Some(dark) = name_looks_dark(value.as_str()) {
                return Some(dark);
            }
        }
    }
    None
}

fn gnome_prefers_dark() -> Option<bool> {
    let mut cmd = Command::new("gsettings");
    cmd.args(["get", "org.gnome.desktop.interface", "color-scheme"]);
    if let Ok(output) = process::capture(cmd, Duration::from_secs(2)) {
        let scheme = process::lossy(&output.stdout)
            .trim()
            .trim_matches(|c| c == '\'' || c == '"')
            .to_lowercase();
        if scheme.contains("dark") {
            return Some(true);
        }
        if scheme.contains("light") {
            return Some(false);
        }
    }
    let mut cmd = Command::new("gsettings");
    cmd.args(["get", "org.gnome.desktop.interface", "gtk-theme"]);
    if let Ok(output) = process::capture(cmd, Duration::from_secs(2)) {
        let theme = process::lossy(&output.stdout);
        let theme = theme.trim().trim_matches(|c| c == '\'' || c == '"');
        if let Some(dark) = name_looks_dark(theme) {
            return Some(dark);
        }
    }
    None
}

fn kread_bin(name: &str) -> Option<PathBuf> {
    if let Some(found) = process::which(name) {
        return Some(found);
    }
    for base in ["/run/current-system/sw/bin", "/run/wrappers/bin"] {
        let path = Path::new(base).join(name);
        if path.is_file() {
            return Some(path);
        }
    }
    None
}

fn home_dir() -> PathBuf {
    env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/"))
}

fn name_looks_dark(name: &str) -> Option<bool> {
    let n = name.trim().to_lowercase().replace(' ', "");
    if n.is_empty() {
        return None;
    }
    const DARK: &[&str] = &["dark", "night", "black", "dim", "ombra", "noir", "twilight"];
    if DARK.iter().any(|token| n.contains(token)) {
        return Some(true);
    }
    const LIGHT: &[&str] = &["light", "clair", "bright", "day"];
    if LIGHT.iter().any(|token| n.contains(token)) {
        return Some(false);
    }
    if n == "breeze" || n == "org.kde.breeze.desktop" {
        return Some(false);
    }
    None
}

fn parse_rgb(value: &str) -> Option<(i32, i32, i32)> {
    let v = value.trim().trim_matches(|c| c == '"' || c == '\'');
    if let Some(hex) = v.strip_prefix('#') {
        if hex.len() >= 6 {
            let r = i32::from_str_radix(&hex[0..2], 16).ok()?;
            let g = i32::from_str_radix(&hex[2..4], 16).ok()?;
            let b = i32::from_str_radix(&hex[4..6], 16).ok()?;
            return Some((r, g, b));
        }
    }
    let parts: Vec<&str> = v
        .split(|c: char| c == ',' || c.is_whitespace())
        .filter(|p| !p.is_empty())
        .collect();
    if parts.len() >= 3 {
        let r = parts[0].parse::<f64>().ok()? as i32;
        let g = parts[1].parse::<f64>().ok()? as i32;
        let b = parts[2].parse::<f64>().ok()? as i32;
        return Some((r, g, b));
    }
    None
}

fn luma(rgb: (i32, i32, i32)) -> f64 {
    0.299 * rgb.0 as f64 + 0.587 * rgb.1 as f64 + 0.114 * rgb.2 as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn theme_names() {
        assert_eq!(name_looks_dark("Breeze Dark"), Some(true));
        assert_eq!(name_looks_dark("Breeze"), Some(false));
        assert_eq!(name_looks_dark("  "), None);
        assert_eq!(name_looks_dark("org.kde.breeze.desktop"), Some(false));
    }

    #[test]
    fn parses_colors() {
        assert_eq!(parse_rgb("#1a7ab8"), Some((0x1a, 0x7a, 0xb8)));
        assert_eq!(parse_rgb("30, 30, 30"), Some((30, 30, 30)));
        assert!(luma((30, 30, 30)) < 128.0);
        assert!(luma((250, 250, 250)) > 128.0);
    }
}
