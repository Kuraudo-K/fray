//! Composition root : câble domaine ← ports ← adapters.

use std::sync::Arc;

use fray_update_manager::adapters::config::AppConfig;
use fray_update_manager::adapters::gtk;
use fray_update_manager::adapters::prefs_fs::FsPreferencesStore;
use fray_update_manager::adapters::power_fs::FsPowerStore;
use fray_update_manager::adapters::system_nixos::NixOsSystemGateway;
use fray_update_manager::adapters::theme_desktop::{DesktopThemeDetector, EnvIconLocator};
use fray_update_manager::application::UpdateManagerService;

fn main() {
    if std::env::args()
        .nth(1)
        .is_some_and(|arg| arg == "-h" || arg == "--help")
    {
        println!(
            "fray-update-manager — GUI mises à jour Fray\n\
             \n  (sans argument)  ouvre l'interface\n\
             Variables : FRAY_UM_DEMO=1  FRAY_UM_STATE_DIR=…  FRAY_UM_PREFS_FILE=…"
        );
        return;
    }

    let config = AppConfig::from_env();
    let prefs = Arc::new(FsPreferencesStore::new(&config));
    let power = Arc::new(FsPowerStore::new(&config));
    let system = Arc::new(NixOsSystemGateway::new(&config));
    let theme = Arc::new(DesktopThemeDetector);
    let icons = Arc::new(EnvIconLocator);

    let service = Arc::new(UpdateManagerService::new(prefs, power, system, theme));
    gtk::run(service, config, icons);
}
