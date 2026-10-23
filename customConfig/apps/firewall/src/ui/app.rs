use crate::models::FirewallConfig;
use crate::ui::window::FrayFirewallWindow;
use crate::utils::{parse_firewall_nix, default_nix_has_firewall_import};
use gtk4::gdk;
use gtk4::prelude::*;
use gtk4::glib;
use libadwaita as adw;
use std::cell::RefCell;
use std::fs;
use std::path::{Path, PathBuf};
use std::rc::Rc;

const FIREWALL_NIX_PATH: &str = "/etc/nixos/customConfig/system/firewall-managed.nix";
const DEFAULT_NIX_PATH: &str = "/etc/nixos/customConfig/default.nix";

/// Load saved theme preference from XDG config directory.
/// Returns the adw::ColorScheme to apply.
pub fn load_theme_preference() -> adw::ColorScheme {
    let config_dir = glib::user_config_dir().join("fray-firewall");
    let config_file = config_dir.join("theme.conf");

    if let Ok(content) = fs::read_to_string(&config_file) {
        match content.trim() {
            "light" => adw::ColorScheme::ForceLight,
            "dark" => adw::ColorScheme::ForceDark,
            _ => adw::ColorScheme::Default,
        }
    } else {
        adw::ColorScheme::Default
    }
}

/// Save theme preference to XDG config directory.
pub fn save_theme_preference(scheme: adw::ColorScheme) {
    let config_dir = glib::user_config_dir().join("fray-firewall");
    let _ = fs::create_dir_all(&config_dir);
    let config_file = config_dir.join("theme.conf");

    let value = match scheme {
        adw::ColorScheme::ForceLight => "light",
        adw::ColorScheme::ForceDark => "dark",
        _ => "system",
    };
    let _ = fs::write(&config_file, value);
}

fn add_icon_search_path(icon_theme: &gtk4::IconTheme, path: impl AsRef<Path>) {
    let path = path.as_ref();
    if path.is_dir() {
        icon_theme.add_search_path(path);
    }
}

fn configure_icon_theme() {
    if let Some(settings) = gtk4::Settings::default() {
        settings.set_property("gtk-icon-theme-name", "Adwaita");
    }

    let Some(display) = gdk::Display::default() else {
        return;
    };
    let icon_theme = gtk4::IconTheme::for_display(&display);

    if let Some(path) = option_env!("ADWAITA_ICON_THEME_PATH") {
        add_icon_search_path(&icon_theme, path);
    }

    for data_dir in std::env::split_paths(&std::env::var_os("XDG_DATA_DIRS").unwrap_or_default()) {
        add_icon_search_path(&icon_theme, data_dir.join("icons"));
    }

    add_icon_search_path(&icon_theme, "/run/current-system/sw/share/icons");
    add_icon_search_path(&icon_theme, "/usr/local/share/icons");
    add_icon_search_path(&icon_theme, "/usr/share/icons");

    for icon in [
        "org.fray.firewall",
        "security-high-symbolic",
        "security-medium-symbolic",
        "display-brightness-symbolic",
        "document-edit-symbolic",
        "document-save-symbolic",
        "list-add-symbolic",
        "view-list-symbolic",
        "user-trash-symbolic",
    ] {
        if !icon_theme.has_icon(icon) {
            eprintln!("Icon not found in current GTK icon theme: {}", icon);
        }
    }
}

pub struct NixFirewallApp {
    app: adw::Application,
}

impl NixFirewallApp {
    pub fn new() -> Self {
        let app = adw::Application::builder()
            .application_id("org.fray.firewall")
            .build();

        glib::set_application_name("Fray Firewall");
        glib::set_prgname(Some("fray-firewall"));

        app.connect_activate(move |app| {
            Self::on_activate(app);
        });

        Self { app }
    }

    fn on_activate(app: &adw::Application) {
        configure_icon_theme();

        // Apply saved theme preference (works on GNOME via libadwaita,
        // and on KDE Plasma via XDG Desktop Portal color-scheme)
        let style_manager = adw::StyleManager::default();
        let saved_scheme = load_theme_preference();
        style_manager.set_color_scheme(saved_scheme);

        let firewall_path = PathBuf::from(FIREWALL_NIX_PATH);
        let default_nix_path = PathBuf::from(DEFAULT_NIX_PATH);

        // Load or create firewall config
        let config = if firewall_path.exists() {
            match fs::read_to_string(&firewall_path) {
                Ok(content) => match parse_firewall_nix(&content) {
                    Ok(cfg) => {
                        eprintln!("Firewall config loaded: {} rules", cfg.rules.len());
                        cfg
                    }
                    Err(e) => {
                        eprintln!("Failed to parse firewall.nix: {}", e);
                        FirewallConfig::default()
                    }
                },
                Err(e) => {
                    eprintln!("Failed to read firewall.nix: {}", e);
                    FirewallConfig::default()
                }
            }
        } else {
            eprintln!("No firewall.nix found, starting with default config");
            FirewallConfig::default()
        };

        // Check if default.nix needs the import
        let needs_import = if default_nix_path.exists() {
            match fs::read_to_string(&default_nix_path) {
                Ok(content) => !default_nix_has_firewall_import(&content),
                Err(_) => false,
            }
        } else {
            false
        };

        let config = Rc::new(RefCell::new(config));
        let needs_import = Rc::new(RefCell::new(needs_import));

        let window = FrayFirewallWindow::new(
            app,
            config,
            firewall_path,
            default_nix_path,
            needs_import,
        );

        window.present();
    }

    pub fn run(&self) -> i32 {
        self.app.run().into()
    }
}
