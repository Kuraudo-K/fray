use std::env;
use std::path::PathBuf;

#[derive(Clone, Debug)]
pub struct AppConfig {
    pub demo: bool,
    pub power_file: PathBuf,
    pub prefs_file: PathBuf,
}

impl AppConfig {
    pub fn from_env() -> Self {
        let demo = env::var("FRAY_UM_DEMO")
            .map(|value| matches!(value.to_ascii_lowercase().as_str(), "1" | "true" | "yes"))
            .unwrap_or(false);

        let state_dir = env::var("FRAY_UM_STATE_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                if demo {
                    PathBuf::from("/tmp/fray-update-manager-demo")
                } else {
                    PathBuf::from("/var/lib/fray-update-manager")
                }
            });

        let prefs_file = env::var("FRAY_UM_PREFS_FILE")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                env::current_dir()
                    .unwrap_or_else(|_| PathBuf::from("."))
                    .join("fray-update-manager-prefs.nix")
            });

        Self {
            demo,
            power_file: state_dir.join("power-mode"),
            prefs_file,
        }
    }
}
