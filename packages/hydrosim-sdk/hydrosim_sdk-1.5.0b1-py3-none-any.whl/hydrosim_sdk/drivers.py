from uuid import UUID
from typing import Callable, List
from hydrosim_sdk.hydrosim_structs import DriverIPC, TimingIPC


class Driver:
    id: UUID
    connectionId: int
    name: str
    team: str
    hull: str
    boatClass: str
    number: str
    lapTimesCount: int
    lapTimes: List[float]
    penaltiesCount: int
    penalties: List[PenaltyIPC]
    worldPosition: Vec3IPC
    worldRotation: Vec3IPC
    trailerPosition: Vec3IPC
    trailerRotation: Vec3IPC
    velocity: Vec3IPC
    rpm: float
    speed: float
    throttle: float
    canard: float
    steer: float
    distance: float
    lateralDistance: float
    normalizedDistance: float
    gapLeader: float
    gapAhead: float
    totalTime: float
    lapTime: float
    bestLapTime: float
    lastLapTime: float
    timeDownLeader: float
    timeDown: float
    position: int
    currentSector: int
    lap: int
    bestLap: int
    lastLap: int
    lapsDownLeader: int
    lapsDown: int
    isConnected: bool
    isLocalPlayer: bool
    isFinished: bool
    state: PlayerState
    clientType: ClientType
    finishStatus: FinishStatus

    def update(self, other: DriverIPC):
        changes = {}
        if self.id != other.id:
            self.id = other.id
            changes["id"] = self.id
        if self.connectionId != other.connectionId:
            self.connectionId = other.connectionId
            changes["connectionId"] = self.id
        if self.name != other.name:
            self.name = other.name
            changes["name"] = self.id
        if self.team != other.team:
            self.team = other.team
            changes["team"] = self.id
        if self.hull != other.hull:
            self.hull = other.hull
            changes["hull"] = self.id
        if self.boatClass != other.boatClass:
            self.boatClass = other.boatClass
            changes["boatClass"] = self.id
        if self.number != other.number:
            self.number = other.number
            changes["number"] = self.id
        if self.lapTimesCount != other.lapTimesCount:
            self.lapTimesCount = other.lapTimesCount
            changes["lapTimesCount"] = self.id
        if self.lapTimes != other.lapTimes:
            self.lapTimes = other.lapTimes
            changes["lapTimes"] = self.id
        if self.penaltiesCount != other.penaltiesCount:
            self.penaltiesCount = other.penaltiesCount
            changes["penaltiesCount"] = self.id
        if self.penalties != other.penalties:
            self.penalties = other.penalties
            changes["penalties"] = self.id
        if self.worldPosition != other.worldPosition:
            self.worldPosition = other.worldPosition
            changes["worldPosition"] = self.id
        if self.worldRotation != other.worldRotation:
            self.worldRotation = other.worldRotation
            changes["worldRotation"] = self.id
        if self.trailerPosition != other.trailerPosition:
            self.trailerPosition = other.trailerPosition
            changes["trailerPosition"] = self.id
        if self.trailerRotation != other.trailerRotation:
            self.trailerRotation = other.trailerRotation
            changes["trailerRotation"] = self.id
        if self.velocity != other.velocity:
            self.velocity = other.velocity
            changes["velocity"] = self.id
        if self.rpm != other.rpm:
            self.rpm = other.rpm
            changes["rpm"] = self.id
        if self.speed != other.speed:
            self.speed = other.speed
            changes["speed"] = self.id
        if self.throttle != other.throttle:
            self.throttle = other.throttle
            changes["throttle"] = self.id
        if self.canard != other.canard:
            self.canard = other.canard
            changes["canard"] = self.id
        if self.steer != other.steer:
            self.steer = other.steer
            changes["steer"] = self.id
        if self.distance != other.distance:
            self.distance = other.distance
            changes["distance"] = self.id
        if self.lateralDistance != other.lateralDistance:
            self.lateralDistance = other.lateralDistance
            changes["lateralDistance"] = self.id
        if self.normalizedDistance != other.normalizedDistance:
            self.normalizedDistance = other.normalizedDistance
            changes["normalizedDistance"] = self.id
        if self.gapLeader != other.gapLeader:
            self.gapLeader = other.gapLeader
            changes["gapLeader"] = self.id
        if self.gapAhead != other.gapAhead:
            self.gapAhead = other.gapAhead
            changes["gapAhead"] = self.id
        if self.totalTime != other.totalTime:
            self.totalTime = other.totalTime
            changes["totalTime"] = self.id
        if self.lapTime != other.lapTime:
            self.lapTime = other.lapTime
            changes["lapTime"] = self.id
        if self.bestLapTime != other.bestLapTime:
            self.bestLapTime = other.bestLapTime
            changes["bestLapTime"] = self.id
        if self.lastLapTime != other.lastLapTime:
            self.lastLapTime = other.lastLapTime
            changes["lastLapTime"] = self.id
        if self.timeDownLeader != other.timeDownLeader:
            self.timeDownLeader = other.timeDownLeader
            changes["timeDownLeader"] = self.id
        if self.timeDown != other.timeDown:
            self.timeDown = other.timeDown
            changes["timeDown"] = self.id
        if self.position != other.position:
            self.position = other.position
            changes["position"] = self.id
        if self.currentSector != other.currentSector:
            self.currentSector = other.currentSector
            changes["currentSector"] = self.id
        if self.lap != other.lap:
            self.lap = other.lap
            changes["lap"] = self.id
        if self.bestLap != other.bestLap:
            self.bestLap = other.bestLap
            changes["bestLap"] = self.id
        if self.lastLap != other.lastLap:
            self.lastLap = other.lastLap
            changes["lastLap"] = self.id
        if self.lapsDownLeader != other.lapsDownLeader:
            self.lapsDownLeader = other.lapsDownLeader
            changes["lapsDownLeader"] = self.id
        if self.lapsDown != other.lapsDown:
            self.lapsDown = other.lapsDown
            changes["lapsDown"] = self.id
        if self.isConnected != other.isConnected:
            self.isConnected = other.isConnected
            changes["isConnected"] = self.id
        if self.isLocalPlayer != other.isLocalPlayer:
            self.isLocalPlayer = other.isLocalPlayer
            changes["isLocalPlayer"] = self.id
        if self.isFinished != other.isFinished:
            self.isFinished = other.isFinished
            changes["isFinished"] = self.id
        if self.state != other.state:
            self.state = other.state
            changes["state"] = self.id
        if self.clientType != other.clientType:
            self.clientType = other.clientType
            changes["clientType"] = self.id
        if self.finishStatus != other.finishStatus:
            self.finishStatus = other.finishStatus
            changes["finishStatus"] = self.id

        return changes


class Drivers:

    drivers = {}
    driver_added_cb: Callable[["Driver"], None] = None
    driver_changed_cb: Callable[["Driver"], None] = None
    driver_removed_cb: Callable[["Driver"], None] = None

    def __init__(
        self,
        driver_added_cb: Callable[["Driver"], None] = None,
        driver_changed_cb: Callable[["Driver"], None] = None,
        driver_removed_cb: Callable[["Driver"], None] = None,
    ):
        self.driver_added_cb = driver_added_cb
        self.driver_changed_cb = driver_changed_cb
        self.driver_removed_cb = driver_removed_cb

    def update(self, timing: TimingIPC):
        count = timing.driversCount
        for i in range(count):
            drv: DriverIPC = timing.drivers[i]
            if drv.id in self.drivers:
                driver = self.drivers[drv.id]
                changes = driver.update(drv)
                if changes:
                    if self.driver_changed_cb:
                        self.driver_changed_cb(driver, changes)
            else:
                self.drivers[drv.id] = Driver(drv)
                if self.driver_added_cb:
                    self.driver_added_cb(driver)

        drivers_to_remove = []
        for key in self.drivers.keys():
            driver_found = False
            for i in range(count):
                if timing.drivers[i].id == key:
                    driver_found = True
                    break

            if not driver_found:
                drivers_to_remove.append(key)

        for rm_drv in drivers_to_remove:
            drv = self.drivers.pop(rm_drv)
            if self.driver_removed_cb:
                self.driver_removed_cb(driver)
