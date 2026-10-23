//! Domaine : règles et modèles purs (aucune I/O, aucun GTK).

pub mod model;
pub mod prefs_nix;
pub mod text;

pub use model::{PowerMode, Settings, Weekday, POWER_MODE_LABELS, WEEKDAY_LABELS};
pub use prefs_nix::{parse_prefs_nix, render_prefs_nix};
pub use text::{short_msg, strip_ansi};
