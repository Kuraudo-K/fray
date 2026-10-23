#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PowerMode {
    Standard,
    Eco,
}

impl PowerMode {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Standard => "standard",
            Self::Eco => "eco",
        }
    }

    pub fn parse(value: &str) -> Self {
        match value.trim() {
            "eco" => Self::Eco,
            "performance" | "standard" => Self::Standard,
            _ => Self::Standard,
        }
    }
}

impl Default for PowerMode {
    fn default() -> Self {
        Self::Standard
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Weekday {
    Mon,
    Tue,
    Wed,
    Thu,
    Fri,
    Sat,
    Sun,
}

impl Weekday {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Mon => "Mon",
            Self::Tue => "Tue",
            Self::Wed => "Wed",
            Self::Thu => "Thu",
            Self::Fri => "Fri",
            Self::Sat => "Sat",
            Self::Sun => "Sun",
        }
    }

    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "Mon" => Some(Self::Mon),
            "Tue" => Some(Self::Tue),
            "Wed" => Some(Self::Wed),
            "Thu" => Some(Self::Thu),
            "Fri" => Some(Self::Fri),
            "Sat" => Some(Self::Sat),
            "Sun" => Some(Self::Sun),
            _ => None,
        }
    }
}

pub const WEEKDAY_LABELS: &[(Weekday, &str)] = &[
    (Weekday::Mon, "Lundi"),
    (Weekday::Tue, "Mardi"),
    (Weekday::Wed, "Mercredi"),
    (Weekday::Thu, "Jeudi"),
    (Weekday::Fri, "Vendredi"),
    (Weekday::Sat, "Samedi"),
    (Weekday::Sun, "Dimanche"),
];

pub const POWER_MODE_LABELS: &[(PowerMode, &str)] = &[
    (PowerMode::Standard, "Standard — tous les cœurs"),
    (PowerMode::Eco, "Éco — moitié des cœurs (moins chauffant)"),
];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Settings {
    pub auto_upgrade: bool,
    pub schedule_enable: bool,
    pub weekday: Weekday,
    pub hour: u8,
    pub minute: u8,
    pub power_mode: PowerMode,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            auto_upgrade: true,
            schedule_enable: false,
            weekday: Weekday::Sat,
            hour: 16,
            minute: 0,
            power_mode: PowerMode::Standard,
        }
    }
}

impl Settings {
    pub fn from_ui(
        auto: bool,
        schedule: bool,
        weekday: Weekday,
        hour: u8,
        minute: u8,
        power_mode: PowerMode,
    ) -> Self {
        // Règle métier : auto et planning sont exclusifs.
        Self {
            auto_upgrade: auto && !schedule,
            schedule_enable: schedule && !auto,
            weekday,
            hour: hour.min(23),
            minute: minute.min(59),
            power_mode,
        }
    }
}
