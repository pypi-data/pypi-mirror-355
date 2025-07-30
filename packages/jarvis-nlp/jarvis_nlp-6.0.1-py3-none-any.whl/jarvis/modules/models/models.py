# noinspection PyUnresolvedReferences
"""This is a space where all the validated environment variables are loaded and evalued as per requirements.

>>> Models

"""

import os
import pathlib
import warnings
from importlib import metadata

import cv2
import pvporcupine
import requests
from packaging.version import Version
from pydantic import PositiveInt

from jarvis.modules.camera import camera
from jarvis.modules.database import database
from jarvis.modules.exceptions import (
    CameraError,
    DependencyError,
    EgressErrors,
    InvalidEnvVars,
)
from jarvis.modules.models.classes import (
    AUDIO_DRIVER,
    Indicators,
    env,
    fileio,
    settings,
)
from jarvis.modules.models.enums import (
    DistanceUnits,
    StartupOptions,
    SupportedPlatforms,
    TemperatureUnits,
)
from jarvis.modules.utils import util

# Shared across other modules
voices = AUDIO_DRIVER.getProperty("voices")
indicators = Indicators()
# TABLES to be created in `fileio.base_db`
TABLES = {
    env.event_app: ("info", "date"),
    "ics": ("info", "date"),
    "stopper": ("flag", "caller"),
    "restart": ("flag", "caller"),
    "children": (
        "meetings",
        "events",
        "crontab",
        "party",
        "guard",
        "surveillance",
        "plot_mic",
        "undefined",
    ),
    "vpn": ("state",),
    "party": ("pid",),
    "guard": ("state", "trigger"),
    "robinhood": ("summary",),
    "listener": ("state",),
}
WAKE_WORD_DETECTOR = metadata.version(pvporcupine.__name__)
# TABLES to keep from `fileio.base_db`
KEEP_TABLES = ("vpn", "party", "listener")
startup = settings.pname in ("JARVIS", "telegram_api", "jarvis_api")
# 'startup_gpt' is required since it has to be invoked only for certain child processes
# this will avoid running GPT instance for pre-commit as well
if startup and StartupOptions.all in env.startup_options:
    startup_car = True
    startup_gpt = env.ollama
    startup_thermostat = True
elif startup:
    startup_car = StartupOptions.car in env.startup_options
    startup_gpt = env.ollama
    startup_thermostat = StartupOptions.thermostat in env.startup_options
else:
    startup_car = False
    startup_gpt = False
    startup_thermostat = False


def _distance_temperature_brute_force() -> None:
    """Convert distance and temperature so that, metric goes with kilometers and imperial with miles."""
    # If distance is requested in miles, then temperature is brute forced to imperial units
    if env.distance_unit == DistanceUnits.MILES:
        env.temperature_unit = TemperatureUnits.IMPERIAL

    # If temperature is requested in imperial, then distance is brute forced to miles
    if env.temperature_unit == TemperatureUnits.IMPERIAL:
        env.distance_unit = DistanceUnits.MILES

    # If neither temperature nor distance is set, then defaults temperature to imperial and distance to miles
    if not env.distance_unit and not env.temperature_unit:
        env.distance_unit = DistanceUnits.MILES
        env.temperature_unit = TemperatureUnits.IMPERIAL

    if not env.distance_unit:
        # If distance is not set, but temperature is requested as imperial, then defaults distance to miles
        if env.temperature_unit == TemperatureUnits.IMPERIAL:
            env.distance_unit = DistanceUnits.MILES
        # If distance is not set, but temperature is requested as metric, then defaults distance to kilometers
        elif env.temperature_unit == TemperatureUnits.METRIC:
            env.distance_unit = DistanceUnits.KILOMETERS

    if not env.temperature_unit:
        # If temperature is not set, but distance is requested as miles, then defaults temperature to imperial
        if env.distance_unit == DistanceUnits.MILES:
            env.temperature_unit = TemperatureUnits.IMPERIAL
        # If temperature is not set, but distance is requested as kms, then defaults temperature to metric
        elif env.distance_unit == DistanceUnits.KILOMETERS:
            env.temperature_unit = TemperatureUnits.METRIC


def _set_default_voice_name() -> None:
    """Set default voice name based on the Operating System."""
    if settings.os == SupportedPlatforms.macOS:
        env.voice_name = "Daniel"
    elif settings.os == SupportedPlatforms.windows:
        env.voice_name = "David"
    elif settings.os == SupportedPlatforms.linux:
        env.voice_name = "english-us"


def _main_process_validations() -> None:
    """Validations that should happen only when the main process is triggered."""
    try:
        # 3.0.2 is the last tested version on macOS - arm64 - 14.5
        assert WAKE_WORD_DETECTOR == "1.9.5" or Version(WAKE_WORD_DETECTOR) >= Version(
            "3.0.2"
        )
    except AssertionError:
        raise DependencyError(
            f"{settings.os} is only supported with porcupine versions 1.9.5 or 3.0.2 and above (requires key)"
        )

    for keyword in env.wake_words:
        if not pvporcupine.KEYWORD_PATHS.get(keyword) or not os.path.isfile(
            pvporcupine.KEYWORD_PATHS[keyword]
        ):
            raise InvalidEnvVars(
                f"Detecting {keyword!r} is unsupported!\n"
                f"Available keywords are: {', '.join(list(pvporcupine.KEYWORD_PATHS.keys()))}"
            )

    # If sensitivity is an integer or float, converts it to a list
    if isinstance(env.sensitivity, float) or isinstance(env.sensitivity, PositiveInt):
        env.sensitivity = [env.sensitivity] * len(env.wake_words)

    # Create all necessary DB tables during startup
    if not os.path.isdir(fileio.root):
        os.mkdir(fileio.root)
    db = database.Database(database=fileio.base_db)
    for table, column in TABLES.items():
        db.create_table(table_name=table, columns=column)
    # Create required file for alarms
    if not os.path.isfile(fileio.alarms):
        pathlib.Path(fileio.alarms).touch()
    # Create required file for reminders
    if not os.path.isfile(fileio.reminders):
        pathlib.Path(fileio.reminders).touch()
    # Create required directory for uploads
    if not os.path.isdir(fileio.uploads):
        os.mkdir(fileio.uploads)


def _global_validations() -> None:
    """Validations that should happen for all processes including parent and child."""
    main = True if settings.pname == "JARVIS" else False
    if voice_names := [__voice.name for __voice in voices]:
        if not env.voice_name:
            _set_default_voice_name()
        elif env.voice_name not in voice_names:
            if main:
                raise InvalidEnvVars(
                    f"{env.voice_name!r} is not available.\n"
                    f"Available voices are: {', '.join(voice_names)}"
                )
            else:
                _set_default_voice_name()
                warnings.warn(
                    f"{env.voice_name!r} is not available. Defaulting to {env.voice_name!r}"
                )

    if not all((env.open_gmail_user, env.open_gmail_pass)):
        env.open_gmail_user = env.gmail_user
        env.open_gmail_pass = env.gmail_pass

    # Note: Pydantic validation for ICS_URL can be implemented using regex=".*ics$"
    # However it will NOT work in this use case, since the type hint is HttpUrl
    if env.ics_url and not env.ics_url.path.endswith(".ics"):
        if main:
            raise InvalidEnvVars("'ICS_URL' should end with .ics")
        else:
            env.ics_url = None
            warnings.warn("'ICS_URL' should end with .ics")

    if env.speech_synthesis_port == env.offline_port:
        if main:
            raise InvalidEnvVars(
                "Speech synthesizer and offline communicator cannot run simultaneously on the same port number."
            )
        else:
            env.speech_synthesis_port = util.get_free_port()
            warnings.warn(
                "Speech synthesizer and offline communicator cannot run on same port number. "
                f"Defaulting to {env.speech_synthesis_port}"
            )

    # Forces limited version if env var is set, otherwise it is enforced based on the number of cores
    if env.limited:
        settings.limited = True
    # If env var is set as False to brute force full version on a device with < 4 processors
    if env.limited is False:
        settings.limited = False
    if settings.limited is True and env.weather_alert:
        warnings.warn("weather alert cannot function on limited mode")
    if env.author_mode and settings.limited:
        warnings.warn(
            "'author_mode' cannot be set when 'limited' mode is enabled, disabling author mode."
        )

    # Validate if able to read camera only if a camera env var is set,
    try:
        if env.camera_index is None:
            cameras = []
        else:
            cameras = camera.Camera().list_cameras()
    except CameraError:
        cameras = []
    if cameras:
        if env.camera_index >= len(cameras):
            if main:
                raise InvalidEnvVars(
                    f"Camera index # {env.camera_index} unavailable.\n"
                    "Camera index cannot exceed the number of available cameras.\n"
                    f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                )
            else:
                warnings.warn(
                    f"Camera index # {env.camera_index} unavailable.\n"
                    "Camera index cannot exceed the number of available cameras.\n"
                    f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                )
                env.camera_index = None
    else:
        env.camera_index = None

    if env.camera_index is None:
        env.camera_index = 0  # Set default but skip validation
    else:
        cam = cv2.VideoCapture(env.camera_index)
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            if main:
                raise CameraError(
                    f"Unable to read the camera - {cameras[env.camera_index]}"
                )
            else:
                warnings.warn(
                    f"Unable to read the camera - {cameras[env.camera_index]}"
                )
                env.camera_index = None
        cam.release()

    # Validate voice for speech synthesis
    try:
        # noinspection HttpUrlsUsage
        # Set connect and read timeout explicitly
        response = requests.get(
            url=f"http://{env.speech_synthesis_host}:{env.speech_synthesis_port}/api/voices",
            timeout=(3, 3),
        )
        if response.ok:
            available_voices = [
                value.get("id").replace("/", "_")
                for key, value in response.json().items()
            ]
            if env.speech_synthesis_voice not in available_voices:
                if main:
                    raise InvalidEnvVars(
                        f"{env.speech_synthesis_voice} is not available.\n"
                        f"Available Voices for Speech Synthesis: {', '.join(available_voices).replace('/', '_')}"
                    )
                else:
                    warnings.warn(
                        f"{env.speech_synthesis_voice} is not available.\n"
                        f"Available Voices for Speech Synthesis: {', '.join(available_voices).replace('/', '_')}"
                    )
    except EgressErrors:
        pass
    _distance_temperature_brute_force()


_global_validations()

# Required at top level to let other modules access it
if env.temperature_unit == TemperatureUnits.IMPERIAL:
    temperature_symbol = "F"
elif env.temperature_unit == TemperatureUnits.METRIC:
    temperature_symbol = "C"

if settings.pname in (
    "JARVIS",
    "pre_commit",
    "startup_script",
    "plot_mic",
    "crontab_executor",
):
    _main_process_validations()
