use crate::models::Disk;
use crate::ui::window::FrayDiskManagerWindow;
use crate::utils::{find_missing_partitions, get_disks, parse_nix_filesystems};
use gtk4::prelude::*;
use gtk4::glib;
use libadwaita as adw;
use std::cell::RefCell;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::rc::Rc;

/// Get the real (invoking) user's config directory.
/// When running as root via pkexec/sudo, glib::user_config_dir() returns /root/.config
/// which is wrong — we need the actual user's config dir.
fn get_real_user_config_dir() -> PathBuf {
    // Check PKEXEC_UID (set by pkexec) or SUDO_UID (set by sudo)
    if let Ok(uid_str) = env::var("PKEXEC_UID").or_else(|_| env::var("SUDO_UID")) {
        if let Ok(uid) = uid_str.parse::<u32>() {
            if uid != 0 {
                // Resolve home directory from /etc/passwd
                if let Ok(content) = fs::read_to_string("/etc/passwd") {
                    for line in content.lines() {
                        let fields: Vec<&str> = line.split(':').collect();
                        if fields.len() >= 6 {
                            if let Ok(passwd_uid) = fields[2].parse::<u32>() {
                                if passwd_uid == uid {
                                    return PathBuf::from(fields[5]).join(".config");
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Fallback: SUDO_HOME is sometimes set
    if let Ok(home) = env::var("SUDO_HOME") {
        if home != "/root" {
            return PathBuf::from(home).join(".config");
        }
    }

    // Default
    glib::user_config_dir()
}

/// Detect the system color scheme when running as root (no XDG portal access).
/// Queries the real user's gsettings via runuser.
fn detect_system_color_scheme() -> adw::ColorScheme {
    // Find the real username
    let real_user = env::var("SUDO_USER").ok().or_else(|| {
        env::var("PKEXEC_UID").ok().and_then(|uid_str| {
            let uid: u32 = uid_str.parse().ok()?;
            if uid == 0 { return None; }
            let content = fs::read_to_string("/etc/passwd").ok()?;
            for line in content.lines() {
                let fields: Vec<&str> = line.split(':').collect();
                if fields.len() >= 6 {
                    if let Ok(passwd_uid) = fields[2].parse::<u32>() {
                        if passwd_uid == uid {
                            return Some(fields[0].to_string());
                        }
                    }
                }
            }
            None
        })
    });

    if let Some(user) = real_user {
        // Query the real user's GNOME color-scheme preference
        if let Ok(output) = Command::new("runuser")
            .args(["-u", &user, "--", "gsettings", "get",
                   "org.gnome.desktop.interface", "color-scheme"])
            .output()
        {
            let stdout = String::from_utf8_lossy(&output.stdout);
            if stdout.contains("prefer-dark") {
                return adw::ColorScheme::PreferDark;
            } else if stdout.contains("prefer-light") {
                return adw::ColorScheme::PreferLight;
            }
        }
    }

    // Fallback: let libadwaita try on its own
    adw::ColorScheme::Default
}

pub fn load_theme_preference() -> adw::ColorScheme {
    let config_dir = get_real_user_config_dir().join("fray-disk");
    let config_file = config_dir.join("theme.conf");

    if let Ok(content) = fs::read_to_string(&config_file) {
        match content.trim() {
            "light" => adw::ColorScheme::ForceLight,
            "dark" => adw::ColorScheme::ForceDark,
            _ => detect_system_color_scheme(),
        }
    } else {
        detect_system_color_scheme()
    }
}

pub fn save_theme_preference(scheme: adw::ColorScheme) {
    let config_dir = get_real_user_config_dir().join("fray-disk");
    let _ = fs::create_dir_all(&config_dir);
    let config_file = config_dir.join("theme.conf");

    let value = match scheme {
        adw::ColorScheme::ForceLight => "light",
        adw::ColorScheme::ForceDark => "dark",
        _ => "system",
    };
    let _ = fs::write(&config_file, value);
}

pub struct FrayDiskApp {
    app: adw::Application,
    #[allow(dead_code)]
    hardware_config_file: PathBuf,
    #[allow(dead_code)]
    hardware_config: Rc<RefCell<String>>,
    #[allow(dead_code)]
    disks: Rc<RefCell<Vec<Disk>>>,
    #[allow(dead_code)]
    must_save: Rc<RefCell<bool>>,
    #[allow(dead_code)]
    windows: Rc<RefCell<Vec<adw::ApplicationWindow>>>,
}

impl FrayDiskApp {
    pub fn new() -> Self {
        let app = adw::Application::builder()
            .application_id("org.glfos.fraydiskmanager")
            .build();

        glib::set_application_name("Nix-disk");
        glib::set_prgname(Some("fray-disk"));

        let hardware_config_file = PathBuf::from("/etc/nixos/hardware-configuration.nix");
        let hardware_config = Rc::new(RefCell::new(String::new()));
        let disks = Rc::new(RefCell::new(Vec::new()));
        let must_save = Rc::new(RefCell::new(false));
        let windows: Rc<RefCell<Vec<adw::ApplicationWindow>>> = Rc::new(RefCell::new(Vec::new()));

        let app_instance = Self {
            app: app.clone(),
            hardware_config_file: hardware_config_file.clone(),
            hardware_config: hardware_config.clone(),
            disks: disks.clone(),
            must_save: must_save.clone(),
            windows: windows.clone(),
        };

        // Setup activation
        let hardware_config_clone = hardware_config.clone();
        let disks_clone = disks.clone();
        let config_file_clone = hardware_config_file.clone();
        let must_save_clone = must_save.clone();
        let windows_clone = windows.clone();

        app.connect_activate(move |app| {
            Self::on_activate(
                app,
                &config_file_clone,
                &hardware_config_clone,
                &disks_clone,
                &must_save_clone,
                &windows_clone,
            );
        });

        app_instance
    }

    fn on_activate(
        app: &adw::Application,
        config_file: &PathBuf,
        hardware_config: &Rc<RefCell<String>>,
        disks: &Rc<RefCell<Vec<Disk>>>,
        must_save: &Rc<RefCell<bool>>,
        windows: &Rc<RefCell<Vec<adw::ApplicationWindow>>>,
    ) {
        // Apply saved theme preference
        // Handles pkexec/sudo context: reads real user's config and gsettings
        let style_manager = adw::StyleManager::default();
        let saved_scheme = load_theme_preference();
        style_manager.set_color_scheme(saved_scheme);

        // Load hardware configuration
        if let Ok(config) = fs::read_to_string(config_file) {
            *hardware_config.borrow_mut() = config;
        } else {
            eprintln!("Failed to read hardware configuration file");
            return;
        }

        // Parse disks
        let config_ref = hardware_config.borrow();
        match get_disks(Some(&config_ref)) {
            Ok(parsed_disks) => {
                // Check for missing partitions
                let configured_partitions = match parse_nix_filesystems(&config_ref) {
                    Ok(parts) => parts.into_values().collect::<Vec<_>>(),
                    Err(e) => {
                        eprintln!("Failed to parse filesystems: {}", e);
                        Vec::new()
                    }
                };

                let missing = find_missing_partitions(&configured_partitions, &parsed_disks);

                *disks.borrow_mut() = parsed_disks;

                // Create and show window
                let window = FrayDiskManagerWindow::new(
                    app,
                    disks.clone(),
                    hardware_config.clone(),
                    config_file.clone(),
                    must_save.clone(),
                    true, // Skip welcome dialog
                );

                // Store window reference for theme updates
                windows.borrow_mut().push(window.gtk_window().clone());

                window.present();

                // Show missing partitions dialog AFTER window is presented
                // This ensures it appears on top
                if !missing.is_empty() {
                    window.show_missing_partitions_dialog(&missing);
                }
            }
            Err(e) => {
                eprintln!("Failed to get disks: {}", e);
            }
        }
    }

    pub fn run(&self) -> i32 {
        self.app.run().into()
    }
}
