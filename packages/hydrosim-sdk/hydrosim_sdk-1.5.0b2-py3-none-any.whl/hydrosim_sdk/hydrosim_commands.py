import sys
import ctypes

from .hydrosim_command_structs import (
    ChatCommandIPC,
    ClientTypes,
    CommandTypes,
    CourseChangeCommandIPC,
    MakeAdminCommandIPC,
    PenaltyCommandIPC,
    RuleCommandIPC,
    ServerSettingsCommandIPC,
    SessionChangeCommandIPC,
    SuperAdminCommandIPC,
)

if sys.platform == "win32":
    import win32file
else:
    import socket

import asyncio
from .hydrosim_structs import (
    InfractionTypes,
    SessionType,
    SeverityTypes,
)


class HydroSimCommands:
    pipe = None
    pipe_name = ""
    mmap_name = ""
    shutdown = False

    def __init__(self, pipe_name, mmap_name=""):
        self.pipe_name = pipe_name
        self.mmap_name = mmap_name

    async def connect(self):
        while not self.shutdown:
            self.init_pipe()

            # Need to send a ping due to issues with closing
            # the named pipe server.
            if self.pipe:
                self._send_ping()
            else:
                print("Failed to connect to named pipe.")

            await asyncio.sleep(1)

    def init_pipe(self):
        if self.pipe:
            return

        mmap_name = ""
        if self.mmap_name:
            mmap_name = f".{self.mmap_name}"
        pipe_name = self.pipe_name + mmap_name
        print(f"Connecting to named pipe: {pipe_name}")
        try:
            if sys.platform == "win32":
                self.pipe = win32file.CreateFile(
                    pipe_name,
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_ATTRIBUTE_NORMAL,
                    None,
                )
            else:
                self.pipe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.pipe.connect(pipe_name)

        except Exception as ex:
            print(ex)
            self.pipe = None

    def stop(self):
        self.shutdown = True
        if self.pipe:
            if sys.platform == "win32":
                self.pipe.Close()
            else:
                self.pipe.close()
        self.pipe = None

    def _send_ping(self):
        ping_buffer = int.to_bytes(4, 4, sys.byteorder) + int.to_bytes(
            0, 4, sys.byteorder
        )
        self._send_buffer(ping_buffer)

    def send_chat(self, message: str, targetId=-1):
        chat = ChatCommandIPC()
        chat.message = message
        chat.targetId = targetId
        self._send(CommandTypes.CHAT, chat)

    def change_course(self, course: str):
        course_change = CourseChangeCommandIPC()
        course_change.course = course
        self._send(CommandTypes.COURSE, course_change)

    def change_session(self, session: SessionType):
        session_change = SessionChangeCommandIPC()
        session_change.session = session
        self._send(CommandTypes.SESSION, session_change)

    def set_server_settings(self, server_settings: ServerSettingsCommandIPC):
        self._send(CommandTypes.SERVER_SETTINGS, server_settings)

    def set_rules(self, rules: RuleCommandIPC):
        self._send(CommandTypes.RULES, rules)

    def reset_buoys(self):
        self._send(CommandTypes.RESET_BUOYS)

    def add_penalty(
        self,
        connectionId: int,
        infraction: InfractionTypes,
        severity: SeverityTypes,
        lap: int,
    ):
        self._penalty(connectionId, infraction, severity, lap)

    def remove_penalty(
        self,
        connectionId: int,
        infraction: InfractionTypes,
        severity: SeverityTypes,
        lap: int,
    ):
        self._penalty(connectionId, infraction, severity, lap, remove=True)

    def revoke_admin(self, connectionId: int):
        self._super_admin(connectionId, revoke_admin=True)

    def leave_water(self, connectionId: int):
        self._super_admin(connectionId, leave_water=True)

    def kick(self, connectionId: int):
        self._super_admin(connectionId, kick=True)

    def make_admin(self, connectionId: int, admin_type: ClientTypes):
        mk_admin = MakeAdminCommandIPC()
        mk_admin.connectionId = connectionId
        mk_admin.adminType = admin_type
        self._send(CommandTypes.MAKE_ADMIN, mk_admin)

    def _penalty(
        self,
        connectionId: int,
        infraction: InfractionTypes,
        severity: SeverityTypes,
        lap: int,
        remove: bool = False,
    ):
        pc = PenaltyCommandIPC()
        pc.remove = remove
        pc.connectionId = connectionId
        pc.penalty.infraction = infraction
        pc.penalty.severity = severity
        pc.lap = lap
        self._send(CommandTypes.PENALTY, pc)

    def _super_admin(
        self,
        connectionId: int,
        kick=False,
        ban=False,
        leave_water=False,
        revoke_admin=False,
    ):
        sac = SuperAdminCommandIPC()
        sac.connectionId = connectionId
        sac.ban = ban
        sac.kick = kick
        sac.leaveWater = leave_water
        sac.revokeAdmin = revoke_admin
        self._send(CommandTypes.SUPER_ADMIN, sac)

    def _send(self, command_type, command=None):
        if command:
            cmd_len = ctypes.sizeof(command) + 4
            cmd_buffer = (
                int.to_bytes(cmd_len, 4, sys.byteorder)
                + int.to_bytes(command_type, 4, sys.byteorder)
                + bytes(command)
            )
        else:
            cmd_len = 4
            cmd_buffer = int.to_bytes(cmd_len, 4, sys.byteorder) + int.to_bytes(
                command_type, 4, sys.byteorder
            )
        self._send_buffer(cmd_buffer)

    def _send_buffer(self, cmd_buffer):
        try:
            if sys.platform == "win32":
                win32file.WriteFile(self.pipe, cmd_buffer)
            else:
                self.pipe.send(cmd_buffer)
        except Exception as ex:
            print(ex)
            self.pipe = None
