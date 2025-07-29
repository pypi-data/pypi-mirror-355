import ctypes
from enum import IntEnum, IntFlag

from .hydrosim_struct_base import HydroSimStructure, hydrosimify


class PlayerState(IntEnum):
    ON_TRAILER = 0
    ON_WATER = 1


class ClientType(IntEnum):
    USER = 0
    ADMIN = 1
    REFEREE = 2
    SUPER_ADMIN = 3


class FinishStatus(IntEnum):
    LEGAL = 0
    DNF = 1
    DNS = 2
    DQ = 3


class SessionType(IntEnum):
    PRACTICE = 0
    QUALIFYING = 1
    RACE = 2


class SessionStatus(IntEnum):
    WAITING = 0
    MILLING = 1
    RUNNING = 2
    FINISHED = 3


class BuoyType(IntFlag):
    NONE = 0x0
    INNER = 0x1
    OUTER = 0x2
    TURN = 0x4
    START_FINISH = 0x8
    ONE_MINUTE = 0x10


class InfractionTypes(IntEnum):
    UNDER_REVIEW = 0
    START_CLOCK = 1
    DISLODGED_BUOY = 2
    MISSED_BUOY = 3
    ONE_MINUTE = 4
    SPEED_LIMIT = 5
    DMZ = 6
    LANE_VIOLATION = 7
    WRECKLESS_DRIVING = 8


class SeverityTypes(IntEnum):
    AUTO = 0
    INVALID = 1
    WARNING = 2
    ONE_MINUTE = 3
    ONE_LAP = 4
    DQ = 5


class WeatherTypes(IntEnum):
    RANDOM = 0
    CLEAR = 1
    PARTLY_CLOUDY = 2
    MOSTLY_CLOUDY = 3
    OVERCAST = 4
    FOGGY = 5
    LIGHT_RAIN = 6
    RAIN = 7


class ScoreUpTypes(IntEnum):
    TURN_ONE_EXIT = 0
    START_FINISH = 1


class SessionTransitionTypes(IntEnum):
    NONE = 0
    ADVANCE = 1
    RESTART = 2


class ImpactTypes(IntEnum):
    WATER = 0
    LAND = 1
    BOAT = 2
    BUOY = 3


class HydroSimConstants:
    MAX_PENALTIES = 128
    MAX_LAPS = 256
    MAX_STRING = 128
    MAX_DESCRIPTION = 1024
    MAX_DRIVERS = 48
    GUID_SIZE = 16
    MAX_ANCHORS = 128
    MAX_BUOYS = 128
    MAX_CHAT_MESSAGE = 1024
    MAX_CHAT_COUNT = 16
    MAX_COURSES = 64
    MAX_LAYOUTS = 16
    MAX_IMPACTS = 32


@hydrosimify
class NameIPC(HydroSimStructure):
    _pack_ = 1
    name: ctypes.c_char * HydroSimConstants.MAX_STRING


@hydrosimify
class Vec3IPC(HydroSimStructure):
    _pack_ = 1
    x: ctypes.c_float
    y: ctypes.c_float
    z: ctypes.c_float


@hydrosimify
class QuaternionIPC(HydroSimStructure):
    _pack_ = 1
    x: ctypes.c_float
    y: ctypes.c_float
    z: ctypes.c_float
    w: ctypes.c_float


@hydrosimify
class ImpactIPC(HydroSimStructure):
    _pack_ = 1
    position: Vec3IPC
    force: Vec3IPC
    acceleration: Vec3IPC
    velocity: Vec3IPC
    time: ctypes.c_double
    # 0 - Water
    # 1 - Land
    # 2 - Boat
    # 3 - Buoy
    impactType: (ctypes.c_byte, ImpactTypes)


@hydrosimify
class CourseSectorIPC(HydroSimStructure):
    _pack_ = 1
    innerPosition: Vec3IPC
    outerPosition: Vec3IPC
    index: ctypes.c_int
    isStartFinish: ctypes.c_bool
    isOneMinute: ctypes.c_bool


@hydrosimify
class ChatMessageIPC(HydroSimStructure):
    __pack__ = 1
    id: ctypes.c_uint
    name: ctypes.c_char * HydroSimConstants.MAX_STRING
    message: ctypes.c_char * HydroSimConstants.MAX_CHAT_MESSAGE


@hydrosimify
class BuoyIPC(HydroSimStructure):
    _pack_ = 1
    worldPosition: Vec3IPC
    worldRotation: Vec3IPC
    type: ctypes.c_uint
    dislodged: ctypes.c_bool


@hydrosimify
class AreaIPC(HydroSimStructure):
    _pack_ = 1
    top: ctypes.c_double
    bottom: ctypes.c_double
    left: ctypes.c_double
    right: ctypes.c_double
    width: ctypes.c_double
    length: ctypes.c_double
    terrainOffset: Vec3IPC


@hydrosimify
class PenaltyIPC(HydroSimStructure):
    _pack_ = 1
    lap: ctypes.c_short
    # See InfractionTypes
    infraction: (ctypes.c_byte, InfractionTypes)
    # See SeverityTypes
    severity: (ctypes.c_byte, SeverityTypes)


@hydrosimify
class SpectatorIPC(HydroSimStructure):
    _pack_ = 1
    id: ctypes.c_ubyte * HydroSimConstants.GUID_SIZE
    connectionId: ctypes.c_int
    name: ctypes.c_char * HydroSimConstants.MAX_STRING
    clientType: (ctypes.c_byte, ClientType)


@hydrosimify
class DriverIPC(HydroSimStructure):
    _pack_ = 1
    id: ctypes.c_ubyte * HydroSimConstants.GUID_SIZE
    connectionId: ctypes.c_int
    name: ctypes.c_char * HydroSimConstants.MAX_STRING
    team: ctypes.c_char * HydroSimConstants.MAX_STRING
    hull: ctypes.c_char * HydroSimConstants.MAX_STRING
    boatClass: ctypes.c_char * HydroSimConstants.MAX_STRING
    number: ctypes.c_char * HydroSimConstants.MAX_STRING
    lapTimesCount: ctypes.c_int
    lapTimes: ctypes.c_float * HydroSimConstants.MAX_LAPS
    penaltiesCount: ctypes.c_int
    penalties: PenaltyIPC * HydroSimConstants.MAX_PENALTIES
    worldPosition: Vec3IPC
    worldRotation: Vec3IPC
    trailerPosition: Vec3IPC
    trailerRotation: Vec3IPC
    velocity: Vec3IPC
    rpm: ctypes.c_float
    speed: ctypes.c_float
    throttle: ctypes.c_float
    canard: ctypes.c_float
    steer: ctypes.c_float
    distance: ctypes.c_float
    lateralDistance: ctypes.c_float
    normalizedDistance: ctypes.c_float
    gapLeader: ctypes.c_float
    gapAhead: ctypes.c_float
    totalTime: ctypes.c_float
    lapTime: ctypes.c_float
    bestLapTime: ctypes.c_float
    lastLapTime: ctypes.c_float
    timeDownLeader: ctypes.c_float
    timeDown: ctypes.c_float
    position: ctypes.c_int
    currentSector: ctypes.c_int
    lap: ctypes.c_int
    bestLap: ctypes.c_int
    lastLap: ctypes.c_int
    lapsDownLeader: ctypes.c_int
    lapsDown: ctypes.c_int
    isConnected: ctypes.c_bool
    isLocalPlayer: ctypes.c_bool
    isFinished: ctypes.c_bool
    state: (ctypes.c_byte, PlayerState)
    clientType: (ctypes.c_byte, ClientType)
    finishStatus: (ctypes.c_byte, FinishStatus)


@hydrosimify
class RulesIPC(HydroSimStructure):
    _pack_ = 1
    practiceStartTime: ctypes.c_float
    qualifyingStartTime: ctypes.c_float
    raceStartTime: ctypes.c_float
    windSpeed: ctypes.c_float
    rainProbability: ctypes.c_float
    raceLength: ctypes.c_uint
    raceStartClock: ctypes.c_uint
    qualifyingLength: ctypes.c_uint
    qualifyingTime: ctypes.c_uint
    practiceTime: ctypes.c_uint
    maxPenaltiesDQ: ctypes.c_uint
    courseLayout: ctypes.c_int
    oneMinutePin: ctypes.c_bool
    allowReset: ctypes.c_bool
    repairOnReset: ctypes.c_bool
    washdowns: ctypes.c_bool
    enableDamage: ctypes.c_bool
    drivingAids: ctypes.c_bool
    qualifyingAutoBuoyReset: ctypes.c_bool
    sessionTransition: (ctypes.c_byte, SessionTransitionTypes)
    sessionCooldown: ctypes.c_uint
    scoreUpTime: ctypes.c_uint
    scoreUpType: (ctypes.c_byte, ScoreUpTypes)
    racePenaltySeverity: (ctypes.c_byte, SeverityTypes)
    weather: (ctypes.c_byte, WeatherTypes)


@hydrosimify
class ServerSettingsIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    name: ctypes.c_char * HydroSimConstants.MAX_STRING
    description: ctypes.c_char * HydroSimConstants.MAX_DESCRIPTION
    address: ctypes.c_char * HydroSimConstants.MAX_STRING
    publicAddress: ctypes.c_char * HydroSimConstants.MAX_STRING
    # Passwords are only visible to SuperAdmin
    password: ctypes.c_char * HydroSimConstants.MAX_STRING
    adminPassword: ctypes.c_char * HydroSimConstants.MAX_STRING
    refereePassword: ctypes.c_char * HydroSimConstants.MAX_STRING
    spectatorPassword: ctypes.c_char * HydroSimConstants.MAX_STRING
    allowedBoatClasses: ctypes.c_char * HydroSimConstants.MAX_STRING
    port: ctypes.c_int
    maxClients: ctypes.c_uint
    maxSpectators: ctypes.c_uint
    tickRate: ctypes.c_uint
    passwordRequired: ctypes.c_bool
    spectatorPasswordRequired: ctypes.c_bool
    allowMismatches: ctypes.c_bool
    proposedRules: RulesIPC
    currentRules: RulesIPC
    coursesCount: ctypes.c_int
    courses: NameIPC * HydroSimConstants.MAX_COURSES
    courseLayoutsCount: ctypes.c_int
    courseLayouts: NameIPC * HydroSimConstants.MAX_LAYOUTS


@hydrosimify
class HydroSimIPC(HydroSimStructure):
    _pack_ = 1
    version: ctypes.c_char * HydroSimConstants.MAX_STRING
    apiVersion: ctypes.c_char * HydroSimConstants.MAX_STRING
    tick: ctypes.c_uint


@hydrosimify
class ChatIPC(HydroSimStructure):
    __pack__ = 1
    update: ctypes.c_uint
    messagesCount: ctypes.c_int
    messages: ChatMessageIPC * HydroSimConstants.MAX_CHAT_COUNT


@hydrosimify
class BuoysIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    buoysCount: ctypes.c_int
    buoys: BuoyIPC * HydroSimConstants.MAX_BUOYS


@hydrosimify
class TimingIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    driversCount: ctypes.c_int
    drivers: DriverIPC * HydroSimConstants.MAX_DRIVERS


@hydrosimify
class SpectatorsIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    spectatorsCount: ctypes.c_int
    spectators: SpectatorIPC * HydroSimConstants.MAX_DRIVERS


@hydrosimify
class CourseInfoIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    course: ctypes.c_char * HydroSimConstants.MAX_STRING
    courseName: ctypes.c_char * HydroSimConstants.MAX_STRING
    courseLocation: ctypes.c_char * HydroSimConstants.MAX_STRING
    layout: ctypes.c_char * HydroSimConstants.MAX_STRING
    geographicArea: AreaIPC
    courseLength: ctypes.c_float
    sectorsCount: ctypes.c_int
    sectors: CourseSectorIPC * HydroSimConstants.MAX_ANCHORS
    anchorCount: ctypes.c_int
    leftAnchors: (Vec3IPC * HydroSimConstants.MAX_ANCHORS, None, "anchorCount")
    rightAnchors: (Vec3IPC * HydroSimConstants.MAX_ANCHORS, None, "anchorCount")


@hydrosimify
class SessionIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    time: ctypes.c_double
    sessionTime: ctypes.c_double
    startClock: ctypes.c_double
    transitionTime: ctypes.c_double
    sessionLength: ctypes.c_float
    windSpeed: ctypes.c_float
    windDirection: ctypes.c_float
    totalLaps: ctypes.c_uint
    lapsComplete: ctypes.c_int
    currentSession: (ctypes.c_byte, SessionType)
    sessionStatus: (ctypes.c_byte, SessionStatus)


@hydrosimify
class TelemetryIPC(HydroSimStructure):
    _pack_ = 1
    update: ctypes.c_uint
    id: ctypes.c_ubyte * HydroSimConstants.GUID_SIZE
    position: Vec3IPC
    rotation: Vec3IPC
    rotationQuaternion: QuaternionIPC
    velocity: Vec3IPC
    angularVelocity: Vec3IPC
    acceleration: Vec3IPC
    angularAcceleration: Vec3IPC
    localVelocity: Vec3IPC
    localAngularVelocity: Vec3IPC
    localAcceleration: Vec3IPC
    localAngularAcceleration: Vec3IPC
    rpm: ctypes.c_float
    maxRPM: ctypes.c_float
    limiterRPM: ctypes.c_float
    engineTorque: ctypes.c_float
    engineMaxTorque: ctypes.c_float
    speed: ctypes.c_float
    propRPM: ctypes.c_float
    throttle: ctypes.c_float
    canard: ctypes.c_float
    rudder: ctypes.c_float
    distance: ctypes.c_float
    lateralDistance: ctypes.c_float
    normalizedDistance: ctypes.c_float
    lapTime: ctypes.c_float
    lastLapTime: ctypes.c_float
    bestLapTime: ctypes.c_float
    currentSector: ctypes.c_int
    lap: ctypes.c_int
    lastLap: ctypes.c_int
    bestLap: ctypes.c_int
    state: (ctypes.c_byte, PlayerState)
    engineIgnition: ctypes.c_bool
    engineRunning: ctypes.c_bool
    isTouchingWater: ctypes.c_bool
    isTurbine: ctypes.c_bool
    maxN2RPM: ctypes.c_float
    impactsCount: ctypes.c_int
    impacts: ImpactIPC * HydroSimConstants.MAX_IMPACTS
