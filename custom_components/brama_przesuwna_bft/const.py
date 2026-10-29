"""Constants for Brama przesuwna BFT."""

DOMAIN = "brama_przesuwna_bft"
DEFAULT_NAME = "Brama przesuwna BFT"
OPTION_PEDESTRIAN_MODE = "pedestrian_mode_enabled"
OPTION_OPENING_DIRECTION = "opening_direction"
OPTION_NOTIFY_OPEN = "notify_when_open"
OPTION_NOTIFY_CLOSED = "notify_when_closed"
NOTIFY_SERVICE = "cala_rodzina"
GATE_STATUS_ENTITY = "sensor.brama_wjazdowa_dokladny_stan_bramy"
PEDESTRIAN_MODE_ENTITY = "binary_sensor.brama_przesuwna_bft_tryb_furtki"
PLATFORMS = ["binary_sensor"]
