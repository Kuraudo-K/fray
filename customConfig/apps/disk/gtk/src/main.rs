mod models;
mod ui;
mod utils;

use anyhow::Result;
use gettextrs::{bind_textdomain_codeset, bindtextdomain, setlocale, textdomain, LocaleCategory};
use libadwaita as adw;
use std::env;

use ui::app::FrayDiskApp;

fn main() -> Result<()> {
    // Initialize GTK
    gtk4::init()?;
    adw::init()?;
    force_adwaita_icon_theme();

    // Setup internationalization
    setup_i18n()?;

    // Get locale from system
    let locale = get_system_locale();
    setlocale(LocaleCategory::LcAll, locale);

    // Create and run the application
    let app = FrayDiskApp::new();
    let exit_code = app.run();

    std::process::exit(exit_code);
}

fn force_adwaita_icon_theme() {
    let Some(display) = gtk4::gdk::Display::default() else {
        return;
    };

    let icon_theme = gtk4::IconTheme::for_display(&display);
    icon_theme.set_theme_name(Some("Adwaita"));
}

fn setup_i18n() -> Result<()> {
    // These paths will be set by the build system
    let locale_dir = option_env!("LOCALE_DIR").unwrap_or("/usr/share/locale");

    bindtextdomain("fraydiskmanager", locale_dir)?;
    bind_textdomain_codeset("fraydiskmanager", "UTF-8")?;
    textdomain("fraydiskmanager")?;

    Ok(())
}

fn get_system_locale() -> &'static str {
    // Try to get locale from environment variables
    if let Ok(locale) = env::var("LANG") {
        Box::leak(locale.into_boxed_str())
    } else if let Ok(locale) = env::var("LC_ALL") {
        Box::leak(locale.into_boxed_str())
    } else {
        "C.UTF-8"
    }
}
