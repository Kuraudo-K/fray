use crate::adapters::home_dir;
use crate::domain::{SessionId, SwitchError, SwitchResult};
use crate::ports::GreeterConfig;
use std::fs;
use std::process::Command;

pub struct DmrcGreeter;

impl GreeterConfig for DmrcGreeter {
    fn set_preferred(&self, session: SessionId) -> SwitchResult<()> {
        let dmrc = home_dir().join(".dmrc");
        let body = format!("[Desktop]\nSession={}\n", session.greeter_id());
        fs::write(&dmrc, body).map_err(|e| SwitchError::Io(e.to_string()))?;
        eprintln!(
            "[fray-de-switch] session greeter -> {} ({})",
            session.greeter_id(),
            dmrc.display()
        );

        if let Ok(user) = std::env::var("USER") {
            let as_path = format!("/var/lib/AccountsService/users/{user}");
            if std::path::Path::new(&as_path).exists() {
                let uid = Command::new("id")
                    .arg("-u")
                    .output()
                    .ok()
                    .and_then(|o| String::from_utf8(o.stdout).ok())
                    .and_then(|s| s.trim().parse::<u32>().ok())
                    .unwrap_or(1000);
                let _ = Command::new("pkexec")
                    .args([
                        "busctl",
                        "call",
                        "org.freedesktop.Accounts",
                        &format!("/org/freedesktop/Accounts/User{uid}"),
                        "org.freedesktop.Accounts.User",
                        "SetXSession",
                        "s",
                        session.greeter_id(),
                    ])
                    .status();
            }
        }
        Ok(())
    }
}
