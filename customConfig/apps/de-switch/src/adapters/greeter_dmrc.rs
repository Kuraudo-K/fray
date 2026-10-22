use crate::adapters::home_dir;
use crate::domain::{SessionId, SwitchError, SwitchResult};
use crate::ports::GreeterConfig;
use std::fs;
use std::process::Command;

/// Persist preferred greeter session for GDM / AccountsService.
///
/// `.dmrc` alone is ignored by modern GDM (Wayland). We also:
/// 1. call `fray-set-session` (sudo NOPASSWD helper from the Nix module)
/// 2. fall back to D-Bus SetXSession / Properties.Set Session
pub struct DmrcGreeter;

impl GreeterConfig for DmrcGreeter {
    fn set_preferred(&self, session: SessionId) -> SwitchResult<()> {
        let greeter = session.greeter_id();
        let dmrc = home_dir().join(".dmrc");
        let body = format!("[Desktop]\nSession={greeter}\n");
        fs::write(&dmrc, body).map_err(|e| SwitchError::Io(e.to_string()))?;
        eprintln!(
            "[fray-de-switch] session greeter -> {greeter} ({})",
            dmrc.display()
        );

        let user = std::env::var("USER").unwrap_or_default();
        if user.is_empty() {
            return Ok(());
        }

        // Privileged helper writes /var/lib/AccountsService/users/<user>
        // (Session= + XSession=). This is what GDM actually reads after reboot.
        let helper = std::env::var("FRAY_SET_SESSION_BIN")
            .unwrap_or_else(|_| "/run/current-system/sw/bin/fray-set-session".into());
        let helper_ok = Command::new("sudo")
            .args(["-n", &helper, greeter, &user])
            .status()
            .map(|s| s.success())
            .unwrap_or(false);

        if helper_ok {
            eprintln!("[fray-de-switch] AccountsService via fray-set-session OK");
            return Ok(());
        }
        eprintln!("[fray-de-switch] fray-set-session unavailable, trying D-Bus");

        let uid = Command::new("id")
            .arg("-u")
            .output()
            .ok()
            .and_then(|o| String::from_utf8(o.stdout).ok())
            .and_then(|s| s.trim().parse::<u32>().ok())
            .unwrap_or(1000);
        let object = format!("/org/freedesktop/Accounts/User{uid}");

        let _ = Command::new("busctl")
            .args([
                "--user",
                "call",
                "org.freedesktop.Accounts",
                &object,
                "org.freedesktop.Accounts.User",
                "SetXSession",
                "s",
                greeter,
            ])
            .status();

        // System bus (needs polkit); best-effort.
        let _ = Command::new("busctl")
            .args([
                "call",
                "org.freedesktop.Accounts",
                &object,
                "org.freedesktop.Accounts.User",
                "SetXSession",
                "s",
                greeter,
            ])
            .status();
        let _ = Command::new("busctl")
            .args([
                "set-property",
                "org.freedesktop.Accounts",
                &object,
                "org.freedesktop.Accounts.User",
                "Session",
                "s",
                greeter,
            ])
            .status();

        Ok(())
    }
}
