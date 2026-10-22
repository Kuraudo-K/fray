mod catalog;
mod desktop;
mod gnome;
mod plasma;
mod swww;

pub use catalog::FsCatalog;
pub use desktop::EnvDesktopDetector;
pub use gnome::GnomeApplier;
pub use plasma::PlasmaApplier;
pub use swww::CompositeApplier;
