import ctypes
from enum import IntEnum

from hydrosim_sdk.hydrosim_structs import (
    SessionTransitionTypes,
    ScoreUpTypes,
    SeverityTypes,
    WeatherTypes,
    HydroSimConstants,
    PenaltyIPC,
    RulesIPC,
    ServerSettingsIPC,
)

from .hydrosim_struct_base import HydroSimStructure, hydrosimify


class CommandTypes:
    PING = 0
    SERVER_SETTINGS = 1
    RULES = 2
    CHAT = 3
    COURSE = 4
    SESSION = 5
    PENALTY = 6
    SUPER_ADMIN = 7
    MAKE_ADMIN = 8
    RESET_BUOYS = 9


class ClientTypes(IntEnum):
    User = 0
    Admin = 1
    Referee = 2
    SuperAdmin = 3


@hydrosimify
class ServerSettingsCommandIPC(HydroSimStructure):
    _pack_ = 1
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

    def from_settings(self, settings: ServerSettingsIPC):
        self._name = settings._name
        self._description = settings._description
        self._address = settings._address
        self._publicAddress = settings._publicAddress
        self._password = settings._password
        self._adminPassword = settings._adminPassword
        self._refereePassword = settings._refereePassword
        self._spectatorPassword = settings._spectatorPassword
        self._allowedBoatClasses = settings._allowedBoatClasses
        self._port = settings._port
        self._maxClients = settings._maxClients
        self._maxSpectators = settings._maxSpectators
        self._tickRate = settings._tickRate
        self._spectatorPasswordRequired = settings._spectatorPasswordRequired
        self._passwordRequired = settings._passwordRequired
        self._allowMismatches = settings._allowMismatches


@hydrosimify
class RuleCommandIPC(HydroSimStructure):
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
    weather: (cytpes.c_byte, WeatherTypes)

    def from_rules(self, rules: RulesIPC):
        self._practiceStartTime = rules._practiceStartTime
        self._qualifyingStartTime = rules._qualifyingStartTime
        self._raceStartTime = rules._raceStartTime
        self._windSpeed = rules._windSpeed
        self._raceLength = rules._raceLength
        self._raceStartClock = rules._raceStartClock
        self._qualifyingLength = rules._qualifyingLength
        self._qualifyingTime = rules._qualifyingTime
        self._practiceTime = rules._practiceTime
        self._maxPenaltiesDQ = rules._maxPenaltiesDQ
        self._courseLayout = rules._courseLayout
        self._oneMinutePin = rules._oneMinutePin
        self._allowReset = rules._allowReset
        self._washdowns = rules._washdowns
        self._drivingAids = rules._drivingAids
        self._qualifyingAutoBuoyReset = rules._qualifyingAutoBuoyReset
        self._sessionTransition = rules._sessionTransition
        self._sessionCooldown = rules._sessionCooldown
        self._scoreUpTime = rules._scoreUpTime
        self._scoreUpType = rules._scoreUpType
        self._racePenaltySeverity = rules._racePenaltySeverity


@hydrosimify
class ChatCommandIPC(HydroSimStructure):
    _pack_ = 1
    targetId: ctypes.c_int
    message: ctypes.c_char * HydroSimConstants.MAX_CHAT_MESSAGE


@hydrosimify
class SessionChangeCommandIPC(HydroSimStructure):
    _pack_ = 1
    session: ctypes.c_byte


@hydrosimify
class CourseChangeCommandIPC(HydroSimStructure):
    _pack_ = 1
    course: ctypes.c_char * HydroSimConstants.MAX_STRING


@hydrosimify
class SuperAdminCommandIPC(HydroSimStructure):
    _pack_ = 1
    connectionId: ctypes.c_uint
    kick: ctypes.c_bool
    ban: ctypes.c_bool
    revokeAdmin: ctypes.c_bool
    leaveWater: ctypes.c_bool


@hydrosimify
class PenaltyCommandIPC(HydroSimStructure):
    _pack_ = 1
    connectionId: ctypes.c_int
    penalty: PenaltyIPC
    remove: ctypes.c_bool


@hydrosimify
class MakeAdminCommandIPC(HydroSimStructure):
    _pack_ = 1
    connectionId: ctypes.c_int
    adminType: (ctypes.c_byte, ClientTypes)
