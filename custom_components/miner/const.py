"""Constants for the Miner integration."""

DOMAIN = "miner"

CONF_IP = "ip"
CONF_TITLE = "title"
CONF_SSH_PASSWORD = "ssh_password"
CONF_SSH_USERNAME = "ssh_username"
CONF_RPC_PASSWORD = "rpc_password"
CONF_WEB_PASSWORD = "web_password"
CONF_WEB_USERNAME = "web_username"
CONF_MIN_POWER = "min_power"
CONF_MAX_POWER = "max_power"

SERVICE_REBOOT = "reboot"
SERVICE_RESTART_BACKEND = "restart_backend"
SERVICE_CURTAIL_WAKEUP = "curtail_wakeup"
SERVICE_CURTAIL_SLEEP = "curtail_sleep"

TERA_HASH_PER_SECOND = "TH/s"
JOULES_PER_TERA_HASH = "J/TH"

DEFAULT_HEAT_SETPOINT_F = 68.0
HEAT_SETPOINT_ENTITY_ID = "number.miner_heat_setpoint"
LIVING_ROOM_TEMPERATURE_SENSOR = "sensor.living_room_temperature_2"
LIVING_ROOM_THERMOSTAT = "climate.living_room"
NEST_FAN_MODE_AUTO = "auto"
NEST_FAN_MODE_ON = "on"


PYASIC_VERSION = "0.72.9"
