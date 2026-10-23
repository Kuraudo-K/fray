use std::path::Path;

use gio::prelude::SettingsExt;
use gtk::prelude::*;

use crate::adapters::theme_desktop;

pub fn apply_gtk_theme() -> bool {
    let Some(settings) = gtk::Settings::default() else {
        return false;
    };
    let dark = theme_desktop::system_prefers_dark();
    settings.set_property("gtk-application-prefer-dark-theme", dark);

    let current = settings
        .property::<Option<String>>("gtk-theme-name")
        .unwrap_or_default();
    let target = pick_theme_name(dark, &current);

    // Forcer un thème installé (sinon GTK reste sur Adwaita clair).
    settings.set_property("gtk-theme-name", "");
    settings.set_property("gtk-theme-name", target.as_str());
    dark
}

/// Style dialogs / TextView : couleurs du thème GTK (clair + sombre).
/// Sous KDE/Breeze, TextView reste souvent blanc → couleurs explicites.
pub fn style_log_surfaces(dialog: &gtk::Dialog, text_view: &gtk::TextView) {
    let css = if theme_desktop::desktop_is_kde() {
        if theme_desktop::system_prefers_dark() {
            r#"
            dialog, dialog.background, dialog box, dialog scrolledwindow, dialog viewport {
                background-color: #2a2e32;
                color: #eceff1;
            }
            dialog label { color: #cfd8dc; }
            dialog button {
                background-image: none;
                background-color: #3d4450;
                color: #eceff1;
                border-color: #555b66;
            }
            dialog button:hover { background-color: #4a5160; }
            textview, textview text {
                background-color: #1b1e22;
                color: #eceff1;
                caret-color: #eceff1;
            }
            "#
        } else {
            r#"
            textview, textview text {
                background-color: #ffffff;
                color: #212121;
            }
            "#
        }
    } else {
        // GNOME / adw-gtk3 : suivre le thème (pas de noir forcé).
        r#"
        dialog, dialog.background, dialog box, dialog scrolledwindow, dialog viewport {
            background-color: @theme_bg_color;
            color: @theme_fg_color;
        }
        dialog label { color: @theme_fg_color; }
        textview, textview text {
            background-color: @theme_base_color;
            color: @theme_text_color;
            caret-color: @theme_text_color;
        }
        "#
    };

    let provider = gtk::CssProvider::new();
    if provider.load_from_data(css.as_bytes()).is_err() {
        return;
    }
    let priority = gtk::STYLE_PROVIDER_PRIORITY_APPLICATION;
    dialog.style_context().add_provider(&provider, priority);
    text_view.style_context().add_provider(&provider, priority);
    for child in dialog.children() {
        child.style_context().add_provider(&provider, priority);
    }
    let area = dialog.content_area();
    area.style_context().add_provider(&provider, priority);
    for child in area.children() {
        child.style_context().add_provider(&provider, priority);
    }
}

fn theme_exists(name: &str) -> bool {
    let mut roots = Vec::new();
    if let Ok(xdg) = std::env::var("XDG_DATA_DIRS") {
        for part in xdg.split(':').filter(|p| !p.is_empty()) {
            roots.push(format!("{part}/themes"));
        }
    }
    roots.push("/run/current-system/sw/share/themes".to_string());
    roots.push("/usr/share/themes".to_string());
    if let Ok(home) = std::env::var("HOME") {
        roots.push(format!("{home}/.local/share/themes"));
        roots.push(format!("{home}/.themes"));
    }
    for root in roots {
        let base = Path::new(&root).join(name);
        if base.join("gtk-3.0").is_dir() || base.join("gtk-3.0").is_file() {
            return true;
        }
        if base.is_dir() {
            return true;
        }
    }
    false
}

fn first_existing(candidates: &[&str]) -> Option<String> {
    candidates
        .iter()
        .find(|name| theme_exists(name))
        .map(|name| (*name).to_string())
}

/// KDE → Breeze(-Dark). GNOME / autre → adw-gtk3 / Adwaita (jamais Breeze).
fn pick_theme_name(dark: bool, _current: &str) -> String {
    if theme_desktop::desktop_is_kde() {
        if dark {
            return first_existing(&["Breeze-Dark", "Breeze", "adw-gtk3-dark", "Adwaita-dark"])
                .unwrap_or_else(|| "Breeze-Dark".to_string());
        }
        return first_existing(&["Breeze", "adw-gtk3", "Adwaita"])
            .unwrap_or_else(|| "Breeze".to_string());
    }

    // GNOME et sessions hors Plasma : Libadwaita / Adwaita uniquement.
    if dark {
        return first_existing(&["adw-gtk3-dark", "Adwaita-dark", "Adwaita"])
            .unwrap_or_else(|| "Adwaita-dark".to_string());
    }
    first_existing(&["adw-gtk3", "Adwaita"]).unwrap_or_else(|| "Adwaita".to_string())
}

pub struct GnomeThemeWatch {
    _settings: gio::Settings,
    _handlers: Vec<glib::SignalHandlerId>,
}

pub fn watch_gnome_theme() -> Option<GnomeThemeWatch> {
    let blob = format!(
        "{}{}",
        std::env::var("XDG_CURRENT_DESKTOP").unwrap_or_default(),
        std::env::var("DESKTOP_SESSION").unwrap_or_default()
    )
    .to_lowercase();
    if !blob.contains("gnome") {
        return None;
    }
    let source = gio::SettingsSchemaSource::default()?;
    if source
        .lookup("org.gnome.desktop.interface", true)
        .is_none()
    {
        return None;
    }
    let settings = gio::Settings::new("org.gnome.desktop.interface");
    let h1 = settings.connect_changed(Some("color-scheme"), |_, _| {
        apply_gtk_theme();
    });
    let h2 = settings.connect_changed(Some("gtk-theme"), |_, _| {
        apply_gtk_theme();
    });
    Some(GnomeThemeWatch {
        _settings: settings,
        _handlers: vec![h1, h2],
    })
}
