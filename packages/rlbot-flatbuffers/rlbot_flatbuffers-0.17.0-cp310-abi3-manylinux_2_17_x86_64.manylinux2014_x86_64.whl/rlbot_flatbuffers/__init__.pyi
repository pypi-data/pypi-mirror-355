from __future__ import annotations

from typing import Optional, Sequence

__doc__: str
__version__: str

class InvalidFlatbuffer(ValueError): ...

class AerialGoalScoreMutator:
    One = AerialGoalScoreMutator(0)
    Zero = AerialGoalScoreMutator(1)
    Two = AerialGoalScoreMutator(2)
    Three = AerialGoalScoreMutator(3)
    Five = AerialGoalScoreMutator(4)
    Ten = AerialGoalScoreMutator(5)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: AerialGoalScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class AirState:
    OnGround = AirState(0)
    """
    All wheels are on the ground and the car is affected by wall-stickiness forces.
    """
    Jumping = AirState(1)
    """
    The car is currently affected by jumping forces of an initial jump.
    Lasts until the player lets go of jump button but at most for 0.2 seconds (240 ticks).
    The following AirState is typically InAir.
    """
    DoubleJumping = AirState(2)
    """
    The car is currently affected by jumping forces of a secondary jump (just an impulse in practice).
    Lasts for 13 ticks.
    The following AirState is typically InAir.
    """
    Dodging = AirState(3)
    """
    The car is currently affected by forces and torque of a dodges.
    This lasts for 79 ticks.
    The following AirState is typically InAir.
    """
    InAir = AirState(4)
    """
    The car is free falling.
    """

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: AirState) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class AssistGoalScoreMutator:
    Zero = AssistGoalScoreMutator(0)
    One = AssistGoalScoreMutator(1)
    Two = AssistGoalScoreMutator(2)
    Three = AssistGoalScoreMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: AssistGoalScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class AudioMutator:
    Default = AudioMutator(0)
    Haunted = AudioMutator(1)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: AudioMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallAnchor:
    """
    A RenderAnchor attached to a ball.
    The local field allows for an offset in local coordinates taking the ball's orientation into account.
    """
    index: int
    """
    The index of the ball.
    """
    local: Vector3
    """
    An offset in local coordinates.
    x is forwards, y is left, and z is up.
    """

    __match_args__ = (
        "index",
        "local",
    )

    def __new__(
        cls,
        index: int = 0,
        local: Vector3 = Vector3(),
    ): ...
    def __init__(
        self,
        index: int = 0,
        local: Vector3 = Vector3(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BallAnchor:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallBouncinessMutator:
    Default = BallBouncinessMutator(0)
    Low = BallBouncinessMutator(1)
    High = BallBouncinessMutator(2)
    SuperHigh = BallBouncinessMutator(3)
    Lowish = BallBouncinessMutator(4)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallBouncinessMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallGravityMutator:
    Default = BallGravityMutator(0)
    Low = BallGravityMutator(1)
    High = BallGravityMutator(2)
    SuperHigh = BallGravityMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallGravityMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallInfo:
    """
    Information about a ball.
    """
    physics: Physics
    """
    The physical state of the ball.
    """
    shape: CollisionShape
    """
    The collision shape of the ball.
    """

    __match_args__ = (
        "physics",
        "shape",
    )

    def __new__(
        cls,
        physics: Physics = Physics(),
        shape: BoxShape | SphereShape | CylinderShape = BoxShape(),
    ): ...
    def __init__(
        self,
        physics: Physics = Physics(),
        shape: BoxShape | SphereShape | CylinderShape = BoxShape(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BallInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallMaxSpeedMutator:
    Default = BallMaxSpeedMutator(0)
    Slow = BallMaxSpeedMutator(1)
    Fast = BallMaxSpeedMutator(2)
    SuperFast = BallMaxSpeedMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallMaxSpeedMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallPrediction:
    """
    A prediction of a ball's trajectory, assuming no collision with cars.
    """
    slices: Sequence[PredictionSlice]
    """
    A list of predicted states of the ball at specific times in the future, assuming no collision with cars.
    The beginning of the list is now, and the end is 6 seconds into the future.
    The prediction is made at 120 Hz, resulting in 720 entries.
    """

    __match_args__ = (
        "slices",
    )

    def __new__(
        cls,
        slices: Sequence[PredictionSlice] = [],
    ): ...
    def __init__(
        self,
        slices: Sequence[PredictionSlice] = [],
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BallPrediction:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallSizeMutator:
    Default = BallSizeMutator(0)
    Small = BallSizeMutator(1)
    Medium = BallSizeMutator(2)
    Large = BallSizeMutator(3)
    Gigantic = BallSizeMutator(4)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallSizeMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallTypeMutator:
    Default = BallTypeMutator(0)
    Cube = BallTypeMutator(1)
    Puck = BallTypeMutator(2)
    Basketball = BallTypeMutator(3)
    Beachball = BallTypeMutator(4)
    Anniversary = BallTypeMutator(5)
    Haunted = BallTypeMutator(6)
    Ekin = BallTypeMutator(7)
    SpookyCube = BallTypeMutator(8)
    Egg = BallTypeMutator(9)
    PlayerSeeking = BallTypeMutator(10)
    Dropshot = BallTypeMutator(11)
    ScoreAbsorb = BallTypeMutator(12)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallTypeMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BallWeightMutator:
    Default = BallWeightMutator(0)
    Light = BallWeightMutator(1)
    Heavy = BallWeightMutator(2)
    SuperLight = BallWeightMutator(3)
    CurveBall = BallWeightMutator(4)
    BeachBallCurve = BallWeightMutator(5)
    MagnusFutBall = BallWeightMutator(6)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BallWeightMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Bool:
    val: bool

    __match_args__ = (
        "val",
    )

    def __new__(
        cls,
        val: bool = False,
    ): ...
    def __init__(
        self,
        val: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Bool:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BoostAmountMutator:
    NormalBoost = BoostAmountMutator(0)
    UnlimitedBoost = BoostAmountMutator(1)
    SlowRecharge = BoostAmountMutator(2)
    RapidRecharge = BoostAmountMutator(3)
    NoBoost = BoostAmountMutator(4)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BoostAmountMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BoostPad:
    """
    Static information about a boost pad such as location and size.
    """
    location: Vector3
    """
    The location of the boost pad.
    """
    is_full_boost: bool
    """
    Whether the boost pad provides a full tank of boost.
    A big boost pad provides 100 boost and respawns in 10 seconds.
    A small boost pad provides 12 boost and respawns in 4 seconds.
    """

    __match_args__ = (
        "location",
        "is_full_boost",
    )

    def __new__(
        cls,
        location: Vector3 = Vector3(),
        is_full_boost: bool = False,
    ): ...
    def __init__(
        self,
        location: Vector3 = Vector3(),
        is_full_boost: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BoostPad:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BoostPadState:
    is_active: bool
    timer: float
    """
    The number of seconds since the boost has been picked up, or 0 if the boost is active.
    A big boost pad becomes active again after 10 seconds.
    """

    __match_args__ = (
        "is_active",
        "timer",
    )

    def __new__(
        cls,
        is_active: bool = False,
        timer: float = 0,
    ): ...
    def __init__(
        self,
        is_active: bool = False,
        timer: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BoostPadState:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BoostStrengthMutator:
    One = BoostStrengthMutator(0)
    OneAndAHalf = BoostStrengthMutator(1)
    Two = BoostStrengthMutator(2)
    Five = BoostStrengthMutator(3)
    Ten = BoostStrengthMutator(4)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: BoostStrengthMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class BoxShape:
    """
    A box with dimensions.
    Used for cars and balls with a box shapes.
    """
    length: float
    width: float
    height: float

    __match_args__ = (
        "length",
        "width",
        "height",
    )

    def __new__(
        cls,
        length: float = 0,
        width: float = 0,
        height: float = 0,
    ): ...
    def __init__(
        self,
        length: float = 0,
        width: float = 0,
        height: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> BoxShape:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CarAnchor:
    """
    A RenderAnchor attached to a car.
    The local field allows for an offset in local coordinates taking the car's orientation into account.
    """
    index: int
    """
    The index of the car.
    """
    local: Vector3
    """
    An offset in local coordinates.
    x is forwards, y is left, and z is up.
    """

    __match_args__ = (
        "index",
        "local",
    )

    def __new__(
        cls,
        index: int = 0,
        local: Vector3 = Vector3(),
    ): ...
    def __init__(
        self,
        index: int = 0,
        local: Vector3 = Vector3(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> CarAnchor:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CollisionShape:
    item: BoxShape | SphereShape | CylinderShape

    def __new__(
        cls, item: BoxShape | SphereShape | CylinderShape = BoxShape()
    ): ...
    def __init__(
        self, item: BoxShape | SphereShape | CylinderShape = BoxShape()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Color:
    r: int
    g: int
    b: int
    a: int

    __match_args__ = (
        "r",
        "g",
        "b",
        "a",
    )

    def __new__(
        cls,
        r: int = 0,
        g: int = 0,
        b: int = 0,
        a: int = 255,
    ): ...
    def __init__(
        self,
        r: int = 0,
        g: int = 0,
        b: int = 0,
        a: int = 255,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Color:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ConnectionSettings:
    """
    Sent by clients when connecting to RLBot to indicate what type of messages are desired.
    This could be sent by a bot, or a bot manager governing several bots, an
    overlay, or any other utility that connects to the RLBot process.
    """
    agent_id: str
    """
    The ID of the bot/script that is associated with the incoming connection.
    """
    wants_ball_predictions: bool
    """
    If this is set, RLBot will send BallPrediction data back to the client when available.
    """
    wants_comms: bool
    """
    If this is set, RLBot will send MatchComms to the client when available.
    """
    close_between_matches: bool
    """
    If this is set, RLBot will close the connection when a match is stopped or when a new
    match is started. The GUI and other match runners should likely not set this.
    """

    __match_args__ = (
        "agent_id",
        "wants_ball_predictions",
        "wants_comms",
        "close_between_matches",
    )

    def __new__(
        cls,
        agent_id: str = "",
        wants_ball_predictions: bool = False,
        wants_comms: bool = False,
        close_between_matches: bool = False,
    ): ...
    def __init__(
        self,
        agent_id: str = "",
        wants_ball_predictions: bool = False,
        wants_comms: bool = False,
        close_between_matches: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ConnectionSettings:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ConsoleCommand:
    """
    A console command which will be executed inside Rocket League.
    See https://wiki.rlbot.org/framework/console-commands/ for a list of known commands.
    """
    command: str

    __match_args__ = (
        "command",
    )

    def __new__(
        cls,
        command: str = "",
    ): ...
    def __init__(
        self,
        command: str = "",
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ConsoleCommand:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ControllableInfo:
    """
    Information about a car that the client can control.
    """
    index: int
    """
    The index of the bot/script.
    """
    identifier: int
    """
    The id of the bot/script.
    This value is mostly used internally to keep track of participants in the match.
    The id can be used to find the corresponding PlayerConfiguration in the MatchConfiguration.
    """

    __match_args__ = (
        "index",
        "identifier",
    )

    def __new__(
        cls,
        index: int = 0,
        identifier: int = 0,
    ): ...
    def __init__(
        self,
        index: int = 0,
        identifier: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ControllableInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ControllableTeamInfo:
    """
    Server message with information about the cars that the client can control.
    Sent to bot clients as a response to ConnectionSettings.
    There may be more than one car in case the bot is a hivemind.
    """
    team: int
    """
    The assigned team for this client.
    """
    controllables: Sequence[ControllableInfo]
    """
    The bots that RLBot will allow this client to control.
    """

    __match_args__ = (
        "team",
        "controllables",
    )

    def __new__(
        cls,
        team: int = 0,
        controllables: Sequence[ControllableInfo] = [],
    ): ...
    def __init__(
        self,
        team: int = 0,
        controllables: Sequence[ControllableInfo] = [],
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ControllableTeamInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ControllerState:
    throttle: float
    steer: float
    pitch: float
    yaw: float
    roll: float
    jump: bool
    boost: bool
    handbrake: bool
    use_item: bool

    __match_args__ = (
        "throttle",
        "steer",
        "pitch",
        "yaw",
        "roll",
        "jump",
        "boost",
        "handbrake",
        "use_item",
    )

    def __new__(
        cls,
        throttle: float = 0,
        steer: float = 0,
        pitch: float = 0,
        yaw: float = 0,
        roll: float = 0,
        jump: bool = False,
        boost: bool = False,
        handbrake: bool = False,
        use_item: bool = False,
    ): ...
    def __init__(
        self,
        throttle: float = 0,
        steer: float = 0,
        pitch: float = 0,
        yaw: float = 0,
        roll: float = 0,
        jump: bool = False,
        boost: bool = False,
        handbrake: bool = False,
        use_item: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ControllerState:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CoreMessage:
    item: DisconnectSignal | GamePacket | FieldInfo | MatchConfiguration | MatchComm | BallPrediction | ControllableTeamInfo | RenderingStatus

    def __new__(
        cls, item: DisconnectSignal | GamePacket | FieldInfo | MatchConfiguration | MatchComm | BallPrediction | ControllableTeamInfo | RenderingStatus = DisconnectSignal()
    ): ...
    def __init__(
        self, item: DisconnectSignal | GamePacket | FieldInfo | MatchConfiguration | MatchComm | BallPrediction | ControllableTeamInfo | RenderingStatus = DisconnectSignal()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CorePacket:
    """
    Packet containing a CoreMessage
    """
    message: CoreMessage

    __match_args__ = (
        "message",
    )

    def __new__(
        cls,
        message: DisconnectSignal | GamePacket | FieldInfo | MatchConfiguration | MatchComm | BallPrediction | ControllableTeamInfo | RenderingStatus = DisconnectSignal(),
    ): ...
    def __init__(
        self,
        message: DisconnectSignal | GamePacket | FieldInfo | MatchConfiguration | MatchComm | BallPrediction | ControllableTeamInfo | RenderingStatus = DisconnectSignal(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> CorePacket:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CustomBot:
    """
    A bot controlled by the RLBot framework.
    """
    name: str
    """
    Requested bot name. When match start, RLBot will ensure each bot has a unique name; bots with
    duplicate names will be renamed with a suffix like `(2)`
    """
    root_dir: str
    """
    The root directory of the bot and the working directory for the run command.
    """
    run_command: str
    """
    The console command that starts this bot.
    """
    loadout: Optional[PlayerLoadout]
    """
    The loadout of the player.
    """
    agent_id: str
    """
    A unique user-defined string that is used to connect clients to the right players/scripts.
    If a bot/script has a run command, RLBot will pass this agent id to the process using an environment variable, RLBOT_AGENT_ID.
    Upon connecting the process announces that it is responsible for this agent id and RLBot will pair the two.
    The recommended format for agent ids is "developer_name/bot_name".
    """
    hivemind: bool
    """
    Whether this player is part of a hivemind bot where all players/cars are controlled by the same process.
    Players in the hivemind must have the same name, team, run command, and agent id.
    """

    __match_args__ = (
        "name",
        "root_dir",
        "run_command",
        "loadout",
        "agent_id",
        "hivemind",
    )

    def __new__(
        cls,
        name: str = "",
        root_dir: str = "",
        run_command: str = "",
        loadout: Optional[PlayerLoadout] = None,
        agent_id: str = "",
        hivemind: bool = False,
    ): ...
    def __init__(
        self,
        name: str = "",
        root_dir: str = "",
        run_command: str = "",
        loadout: Optional[PlayerLoadout] = None,
        agent_id: str = "",
        hivemind: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> CustomBot:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class CylinderShape:
    """
    A cylinder with diameter and height.
    Used for balls with a cylindrical shape like the puck.
    """
    diameter: float
    height: float

    __match_args__ = (
        "diameter",
        "height",
    )

    def __new__(
        cls,
        diameter: float = 0,
        height: float = 0,
    ): ...
    def __init__(
        self,
        diameter: float = 0,
        height: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> CylinderShape:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DebugRendering:
    OffByDefault = DebugRendering(0)
    """
    Renders are ignored unless explicitly enabled per-agent
    """
    OnByDefault = DebugRendering(1)
    """
    Rendering is enabled for everyone by default
    """
    AlwaysOff = DebugRendering(2)
    """
    Ignore all render attempts at all times
    """

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: DebugRendering) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DemolishMutator:
    Default = DemolishMutator(0)
    Disabled = DemolishMutator(1)
    FriendlyFire = DemolishMutator(2)
    OnContact = DemolishMutator(3)
    OnContactFF = DemolishMutator(4)
    OnBallContact = DemolishMutator(5)
    OnBallContactFF = DemolishMutator(6)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: DemolishMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DemolishScoreMutator:
    Zero = DemolishScoreMutator(0)
    One = DemolishScoreMutator(1)
    Two = DemolishScoreMutator(2)
    Three = DemolishScoreMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: DemolishScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DesiredBallState:
    """
    A ball state with nullable components.
    Used for game state setting to define which part of a ball's state should change.
    """
    physics: DesiredPhysics

    __match_args__ = (
        "physics",
    )

    def __new__(
        cls,
        physics: DesiredPhysics = DesiredPhysics(),
    ): ...
    def __init__(
        self,
        physics: DesiredPhysics = DesiredPhysics(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DesiredBallState:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DesiredCarState:
    """
    A car state with nullable components.
    Used for game state setting to define which part of a car's state should change.
    """
    physics: Optional[DesiredPhysics]
    boost_amount: Optional[Float]

    __match_args__ = (
        "physics",
        "boost_amount",
    )

    def __new__(
        cls,
        physics: Optional[DesiredPhysics] = None,
        boost_amount: Optional[Float | float] = None,
    ): ...
    def __init__(
        self,
        physics: Optional[DesiredPhysics] = None,
        boost_amount: Optional[Float | float] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DesiredCarState:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DesiredGameState:
    """
    A game state with nullable subcomponents.
    Used for game state setting to define which part of the game should change.
    Values not set will not be updated.
    """
    ball_states: Sequence[DesiredBallState]
    """
    A list of desired ball states.
    """
    car_states: Sequence[DesiredCarState]
    """
    A list of desired car states.
    """
    match_info: Optional[DesiredMatchInfo]
    """
    The desired game info.
    """
    console_commands: Sequence[ConsoleCommand]
    """
    A list of console commands to execute.
    See https://wiki.rlbot.org/framework/console-commands/ for a list of known commands.
    """

    __match_args__ = (
        "ball_states",
        "car_states",
        "match_info",
        "console_commands",
    )

    def __new__(
        cls,
        ball_states: Sequence[DesiredBallState] = [],
        car_states: Sequence[DesiredCarState] = [],
        match_info: Optional[DesiredMatchInfo] = None,
        console_commands: Sequence[ConsoleCommand] = [],
    ): ...
    def __init__(
        self,
        ball_states: Sequence[DesiredBallState] = [],
        car_states: Sequence[DesiredCarState] = [],
        match_info: Optional[DesiredMatchInfo] = None,
        console_commands: Sequence[ConsoleCommand] = [],
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DesiredGameState:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DesiredMatchInfo:
    """
    Match info with nullable components.
    Used for game state setting to define which part of the match info should change.
    """
    world_gravity_z: Optional[Float]
    """
    The strength of gravity. Default is usually -650 depending on mutators.
    To set gravity to 0, use 0.0000001 instead, as 0 will set gravity back to the default.
    """
    game_speed: Optional[Float]
    """
    The game speed. Default is 1.0.
    """

    __match_args__ = (
        "world_gravity_z",
        "game_speed",
    )

    def __new__(
        cls,
        world_gravity_z: Optional[Float | float] = None,
        game_speed: Optional[Float | float] = None,
    ): ...
    def __init__(
        self,
        world_gravity_z: Optional[Float | float] = None,
        game_speed: Optional[Float | float] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DesiredMatchInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DesiredPhysics:
    """
    A physical state of an object, with nullable components.
    Used for game state setting to define which part of a physics body should change.
    If a component is null, then the component will keep its current value.
    """
    location: Optional[Vector3Partial]
    rotation: Optional[RotatorPartial]
    velocity: Optional[Vector3Partial]
    angular_velocity: Optional[Vector3Partial]

    __match_args__ = (
        "location",
        "rotation",
        "velocity",
        "angular_velocity",
    )

    def __new__(
        cls,
        location: Optional[Vector3Partial] = None,
        rotation: Optional[RotatorPartial] = None,
        velocity: Optional[Vector3Partial] = None,
        angular_velocity: Optional[Vector3Partial] = None,
    ): ...
    def __init__(
        self,
        location: Optional[Vector3Partial] = None,
        rotation: Optional[RotatorPartial] = None,
        velocity: Optional[Vector3Partial] = None,
        angular_velocity: Optional[Vector3Partial] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DesiredPhysics:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DisconnectSignal:
    """
    Sent to core to indicate that you want to disconnect.
    Sent from core to indicate that you should exit.
    """
    def __init__(self): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> DisconnectSignal:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class DodgeTimerMutator:
    OnePointTwentyFiveSeconds = DodgeTimerMutator(0)
    TwoSeconds = DodgeTimerMutator(1)
    ThreeSeconds = DodgeTimerMutator(2)
    Unlimited = DodgeTimerMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: DodgeTimerMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ExistingMatchBehavior:
    Restart = ExistingMatchBehavior(0)
    """
    Always restart the match, even if config is identical.
    """
    ContinueAndSpawn = ExistingMatchBehavior(1)
    """
    Never restart an existing match if possible, just try to remove or spawn cars to match the configuration.
    If we are not in the middle of a match, a match will be started. Handy for LAN matches.
    """
    RestartIfDifferent = ExistingMatchBehavior(2)
    """
    Restart the match if any match settings differ.
    No other otherwise.
    """

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: ExistingMatchBehavior) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class FieldInfo:
    """
    Static information about the field.
    Sent to bots, scripts, etc. upon connecting.
    Dynamic information is found in the GamePacket.
    """
    boost_pads: Sequence[BoostPad]
    """
    Static information about boost pads on the field.
    The dynamic information is found in the GamePacket
    The boost pads are ordered by y-coordinate and then x-coordinate.
    """
    goals: Sequence[GoalInfo]
    """
    Information about the goals on the field.
    """

    __match_args__ = (
        "boost_pads",
        "goals",
    )

    def __new__(
        cls,
        boost_pads: Sequence[BoostPad] = [],
        goals: Sequence[GoalInfo] = [],
    ): ...
    def __init__(
        self,
        boost_pads: Sequence[BoostPad] = [],
        goals: Sequence[GoalInfo] = [],
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> FieldInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Float:
    val: float

    __match_args__ = (
        "val",
    )

    def __new__(
        cls,
        val: float = 0,
    ): ...
    def __init__(
        self,
        val: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Float:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GameEventMutator:
    Default = GameEventMutator(0)
    Haunted = GameEventMutator(1)
    Rugby = GameEventMutator(2)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: GameEventMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GameMode:
    Soccar = GameMode(0)
    Hoops = GameMode(1)
    Dropshot = GameMode(2)
    Snowday = GameMode(3)
    Rumble = GameMode(4)
    Heatseeker = GameMode(5)
    Gridiron = GameMode(6)
    Knockout = GameMode(7)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: GameMode) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GamePacket:
    """
    A packet of data from the game.
    Is is sent every tick to bots, scripts, etc.
    Static data is found in the FieldInfo.
    """
    players: Sequence[PlayerInfo]
    """
    The current state of all players and their cars.
    """
    boost_pads: Sequence[BoostPadState]
    """
    The current state of all boost pads.
    The static information about boost pads are found in the FieldInfo.
    The boost pads are ordered by y-coordinate and then x-coordinate.
    """
    balls: Sequence[BallInfo]
    """
    The current state of all balls.
    """
    match_info: MatchInfo
    """
    The current state of the match such as timers and gravity.
    """
    teams: Sequence[TeamInfo]
    """
    The current state of teams, i.e. the team scores.
    """

    __match_args__ = (
        "players",
        "boost_pads",
        "balls",
        "match_info",
        "teams",
    )

    def __new__(
        cls,
        players: Sequence[PlayerInfo] = [],
        boost_pads: Sequence[BoostPadState] = [],
        balls: Sequence[BallInfo] = [],
        match_info: MatchInfo = MatchInfo(),
        teams: Sequence[TeamInfo] = [],
    ): ...
    def __init__(
        self,
        players: Sequence[PlayerInfo] = [],
        boost_pads: Sequence[BoostPadState] = [],
        balls: Sequence[BallInfo] = [],
        match_info: MatchInfo = MatchInfo(),
        teams: Sequence[TeamInfo] = [],
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> GamePacket:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GameSpeedMutator:
    Default = GameSpeedMutator(0)
    SloMo = GameSpeedMutator(1)
    TimeWarp = GameSpeedMutator(2)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: GameSpeedMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GoalInfo:
    """
    Static information about a goal on the field such as dimensions and location.
    More values can be found on https://wiki.rlbot.org/botmaking/useful-game-values/
    """
    team_num: int
    """
    The index of the team that this goal belongs to.
    """
    location: Vector3
    """
    The center location of the goal.
    """
    direction: Vector3
    """
    The unit direction point away from the opening of the goal.
    """
    width: float
    """
    The width of the goal. 1785 uu wide on a standard field.
    """
    height: float
    """
    The height of the goal. 643 uu tall on a standard field.
    """

    __match_args__ = (
        "team_num",
        "location",
        "direction",
        "width",
        "height",
    )

    def __new__(
        cls,
        team_num: int = 0,
        location: Vector3 = Vector3(),
        direction: Vector3 = Vector3(),
        width: float = 0,
        height: float = 0,
    ): ...
    def __init__(
        self,
        team_num: int = 0,
        location: Vector3 = Vector3(),
        direction: Vector3 = Vector3(),
        width: float = 0,
        height: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> GoalInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class GravityMutator:
    Default = GravityMutator(0)
    Low = GravityMutator(1)
    High = GravityMutator(2)
    SuperHigh = GravityMutator(3)
    Reverse = GravityMutator(4)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: GravityMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Human:
    """
    A normal human player.
    """
    def __init__(self): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Human:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class InitComplete:
    """
    Indicates that the session has finished all initialization and is ready to start receiving
    game messages without delay.
    """
    def __init__(self): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> InitComplete:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class InputRestrictionMutator:
    Default = InputRestrictionMutator(0)
    Backwards = InputRestrictionMutator(1)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: InputRestrictionMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class InterfaceMessage:
    item: DisconnectSignal | StartCommand | MatchConfiguration | PlayerInput | DesiredGameState | RenderGroup | RemoveRenderGroup | MatchComm | ConnectionSettings | StopCommand | SetLoadout | InitComplete | RenderingStatus

    def __new__(
        cls, item: DisconnectSignal | StartCommand | MatchConfiguration | PlayerInput | DesiredGameState | RenderGroup | RemoveRenderGroup | MatchComm | ConnectionSettings | StopCommand | SetLoadout | InitComplete | RenderingStatus = DisconnectSignal()
    ): ...
    def __init__(
        self, item: DisconnectSignal | StartCommand | MatchConfiguration | PlayerInput | DesiredGameState | RenderGroup | RemoveRenderGroup | MatchComm | ConnectionSettings | StopCommand | SetLoadout | InitComplete | RenderingStatus = DisconnectSignal()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class InterfacePacket:
    """
    Packet containing a InterfaceMessage
    """
    message: InterfaceMessage

    __match_args__ = (
        "message",
    )

    def __new__(
        cls,
        message: DisconnectSignal | StartCommand | MatchConfiguration | PlayerInput | DesiredGameState | RenderGroup | RemoveRenderGroup | MatchComm | ConnectionSettings | StopCommand | SetLoadout | InitComplete | RenderingStatus = DisconnectSignal(),
    ): ...
    def __init__(
        self,
        message: DisconnectSignal | StartCommand | MatchConfiguration | PlayerInput | DesiredGameState | RenderGroup | RemoveRenderGroup | MatchComm | ConnectionSettings | StopCommand | SetLoadout | InitComplete | RenderingStatus = DisconnectSignal(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> InterfacePacket:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class JumpMutator:
    Default = JumpMutator(0)
    Grounded = JumpMutator(1)
    Two = JumpMutator(2)
    Three = JumpMutator(3)
    Four = JumpMutator(4)
    Unlimited = JumpMutator(5)
    NoJumps = JumpMutator(6)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: JumpMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Launcher:
    Steam = Launcher(0)
    Epic = Launcher(1)
    Custom = Launcher(2)
    """
    E.g. if you use Legendary.
    The game path is specified in the MatchConfiguration.
    """
    NoLaunch = Launcher(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: Launcher) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Line3D:
    """
    A RenderMessage for a line in 3D space between two RenderAnchors.
    """
    start: RenderAnchor
    end: RenderAnchor
    color: Color

    __match_args__ = (
        "start",
        "end",
        "color",
    )

    def __new__(
        cls,
        start: RenderAnchor = RenderAnchor(),
        end: RenderAnchor = RenderAnchor(),
        color: Color = Color(),
    ): ...
    def __init__(
        self,
        start: RenderAnchor = RenderAnchor(),
        end: RenderAnchor = RenderAnchor(),
        color: Color = Color(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Line3D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class LoadoutPaint:
    """
    Specification for 'painted' items. See https://wiki.rlbot.org/botmaking/bot-customization/
    """
    car_paint_id: int
    decal_paint_id: int
    wheels_paint_id: int
    boost_paint_id: int
    antenna_paint_id: int
    hat_paint_id: int
    trails_paint_id: int
    goal_explosion_paint_id: int

    __match_args__ = (
        "car_paint_id",
        "decal_paint_id",
        "wheels_paint_id",
        "boost_paint_id",
        "antenna_paint_id",
        "hat_paint_id",
        "trails_paint_id",
        "goal_explosion_paint_id",
    )

    def __new__(
        cls,
        car_paint_id: int = 0,
        decal_paint_id: int = 0,
        wheels_paint_id: int = 0,
        boost_paint_id: int = 0,
        antenna_paint_id: int = 0,
        hat_paint_id: int = 0,
        trails_paint_id: int = 0,
        goal_explosion_paint_id: int = 0,
    ): ...
    def __init__(
        self,
        car_paint_id: int = 0,
        decal_paint_id: int = 0,
        wheels_paint_id: int = 0,
        boost_paint_id: int = 0,
        antenna_paint_id: int = 0,
        hat_paint_id: int = 0,
        trails_paint_id: int = 0,
        goal_explosion_paint_id: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> LoadoutPaint:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MatchComm:
    """
    A message sent to other bots and scripts through RLBot.
    Use the team_only field if the message should only be received by team mates.
    The message can also have a human-readable summary displayed in quick chat through the display field.
    """
    index: int
    """
    The index of the player that sent this message.
    For scripts, this value is the index in the match configuration instead.
    """
    team: int
    """
    The team of the player that sent this message.
    For scripts, this value is 2.
    """
    team_only: bool
    """
    True if this message is team-only, false if everyone can see it
    """
    display: Optional[str]
    """
    The message that will be displayed on the screen in quick chat.
    This is intended for communication with humans.
    Use the content field for communication with bots and scripts.
    """
    content: bytes
    """
    The contents of the message.
    Use the display field for messages in quick chat.
    """

    __match_args__ = (
        "index",
        "team",
        "team_only",
        "display",
        "content",
    )

    def __new__(
        cls,
        index: int = 0,
        team: int = 0,
        team_only: bool = False,
        display: Optional[str] = None,
        content: bytes = b"",
    ): ...
    def __init__(
        self,
        index: int = 0,
        team: int = 0,
        team_only: bool = False,
        display: Optional[str] = None,
        content: bytes = b"",
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> MatchComm:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MatchConfiguration:
    """
    Definition of a match.
    Can be sent to RLBot to request the start of a match.
    """
    launcher: Launcher
    """
    How to launch Rocket League.
    If left unset, RLBot will not launch the game.
    To use Legendary, use Custom and set launcher_arg="legendary".
    """
    launcher_arg: str
    """
    Additional configuration for the launching method.
    See launcher.
    """
    auto_start_agents: bool
    """
    If true, RLBot will start the bots and scripts that has a non-empty run command in their player/script configuration.
    """
    wait_for_agents: bool
    """
    If true, RLBot will start the match only once all bots and script have connected and are ready.
    If false, the match will start as soon as the map loads.
    """
    game_map_upk: str
    """
    The name of a upk file, like UtopiaStadium_P, which should be loaded.
    On Steam version of Rocket League this can be used to load custom map files,
    but on Epic version it only works on the Psyonix maps.
    Available maps can be found here: https://github.com/VirxEC/python-interface/blob/master/rlbot/utils/maps.py
    """
    player_configurations: Sequence[PlayerConfiguration]
    """
    The players in the match.
    """
    script_configurations: Sequence[ScriptConfiguration]
    """
    The custom scripts used in the match.
    """
    game_mode: GameMode
    """
    The game mode.
    This affects a few of the game rules although many game modes can also be recreated solely from mutators.
    See what mutators and game mode combinations make up the official modes at https://github.com/VirxEC/python-interface/tree/master/tests/gamemodes
    """
    skip_replays: bool
    """
    Whether to skip goal replays.
    """
    instant_start: bool
    """
    Whether to start without a kickoff countdown.
    """
    mutators: Optional[MutatorSettings]
    """
    Mutator settings.
    """
    existing_match_behavior: ExistingMatchBehavior
    """
    How to handle any ongoing match.
    """
    enable_rendering: DebugRendering
    """
    Whether debug rendering is displayed.
    """
    enable_state_setting: bool
    """
    Whether clients are allowed to manipulate the game state, e.g. teleporting cars and ball.
    """
    auto_save_replay: bool
    """
    Whether the match replay should be saved.
    """
    freeplay: bool
    """
    If set to true, a free play match is launched instead of an exhibition match.
    This allows the players to use training keybinds, Bakkesmod plugins, and other features that are only allowed in free play.
    """

    __match_args__ = (
        "launcher",
        "launcher_arg",
        "auto_start_agents",
        "wait_for_agents",
        "game_map_upk",
        "player_configurations",
        "script_configurations",
        "game_mode",
        "skip_replays",
        "instant_start",
        "mutators",
        "existing_match_behavior",
        "enable_rendering",
        "enable_state_setting",
        "auto_save_replay",
        "freeplay",
    )

    def __new__(
        cls,
        launcher: Launcher = Launcher(),
        launcher_arg: str = "",
        auto_start_agents: bool = False,
        wait_for_agents: bool = False,
        game_map_upk: str = "",
        player_configurations: Sequence[PlayerConfiguration] = [],
        script_configurations: Sequence[ScriptConfiguration] = [],
        game_mode: GameMode = GameMode(),
        skip_replays: bool = False,
        instant_start: bool = False,
        mutators: Optional[MutatorSettings] = None,
        existing_match_behavior: ExistingMatchBehavior = ExistingMatchBehavior(),
        enable_rendering: DebugRendering = DebugRendering(),
        enable_state_setting: bool = False,
        auto_save_replay: bool = False,
        freeplay: bool = False,
    ): ...
    def __init__(
        self,
        launcher: Launcher = Launcher(),
        launcher_arg: str = "",
        auto_start_agents: bool = False,
        wait_for_agents: bool = False,
        game_map_upk: str = "",
        player_configurations: Sequence[PlayerConfiguration] = [],
        script_configurations: Sequence[ScriptConfiguration] = [],
        game_mode: GameMode = GameMode(),
        skip_replays: bool = False,
        instant_start: bool = False,
        mutators: Optional[MutatorSettings] = None,
        existing_match_behavior: ExistingMatchBehavior = ExistingMatchBehavior(),
        enable_rendering: DebugRendering = DebugRendering(),
        enable_state_setting: bool = False,
        auto_save_replay: bool = False,
        freeplay: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> MatchConfiguration:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MatchInfo:
    """
    Information about the current match such as time and gravity.
    """
    seconds_elapsed: float
    """
    How many seconds have elapsed since the first game packet of the match.
    This value ticks up even during kickoffs, replays, pause, etc.
    """
    game_time_remaining: float
    """
    Seconds remaining of the match.
    This value ticks up instead of down during overtime or when the game duration mutator is set to Unlimited.
    I.e. it matches the in-game timer at the top.
    """
    is_overtime: bool
    """
    True if the game is in overtime.
    """
    is_unlimited_time: bool
    """
    True if the game duration is set to Unlimited.
    """
    match_phase: MatchPhase
    """
    The current phase of the match, i.e. kickoff, replay, active, etc.
    """
    world_gravity_z: float
    """
    The current strength of gravity. Default is -650.
    """
    game_speed: float
    """
    Game speed multiplier. Regular game speed is 1.0.
    """
    last_spectated: int
    """
    Index of the player who was most recently a spectated by the host.
    """
    frame_num: int
    """
    Tracks the number of physics frames the game has computed.
    May increase by more than one across consecutive packets.
    Data type will roll over after 414 days at 120Hz.
    """

    __match_args__ = (
        "seconds_elapsed",
        "game_time_remaining",
        "is_overtime",
        "is_unlimited_time",
        "match_phase",
        "world_gravity_z",
        "game_speed",
        "last_spectated",
        "frame_num",
    )

    def __new__(
        cls,
        seconds_elapsed: float = 0,
        game_time_remaining: float = 0,
        is_overtime: bool = False,
        is_unlimited_time: bool = False,
        match_phase: MatchPhase = MatchPhase(),
        world_gravity_z: float = 0,
        game_speed: float = 0,
        last_spectated: int = 0,
        frame_num: int = 0,
    ): ...
    def __init__(
        self,
        seconds_elapsed: float = 0,
        game_time_remaining: float = 0,
        is_overtime: bool = False,
        is_unlimited_time: bool = False,
        match_phase: MatchPhase = MatchPhase(),
        world_gravity_z: float = 0,
        game_speed: float = 0,
        last_spectated: int = 0,
        frame_num: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> MatchInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MatchLengthMutator:
    FiveMinutes = MatchLengthMutator(0)
    TenMinutes = MatchLengthMutator(1)
    TwentyMinutes = MatchLengthMutator(2)
    Unlimited = MatchLengthMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: MatchLengthMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MatchPhase:
    Inactive = MatchPhase(0)
    """
    Match has not been created yet.
    """
    Countdown = MatchPhase(1)
    """
    3-2-1 countdown of a kickoff.
    """
    Kickoff = MatchPhase(2)
    """
    After kickoff countdown, but before ball has been hit.
    The match automatically proceeds to Active after 2 seconds.
    """
    Active = MatchPhase(3)
    """
    The ball is in play and time is ticking.
    """
    GoalScored = MatchPhase(4)
    """
    A goal was just scored. Waiting for replay to start.
    """
    Replay = MatchPhase(5)
    """
    Goal replay is being shown.
    """
    Paused = MatchPhase(6)
    """
    The match is paused.
    """
    Ended = MatchPhase(7)
    """
    The match has ended.
    """

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: MatchPhase) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MaxScoreMutator:
    Unlimited = MaxScoreMutator(0)
    OneGoal = MaxScoreMutator(1)
    ThreeGoals = MaxScoreMutator(2)
    FiveGoals = MaxScoreMutator(3)
    SevenGoals = MaxScoreMutator(4)
    TenGoals = MaxScoreMutator(5)
    TwentyGoals = MaxScoreMutator(6)
    ThirtyGoals = MaxScoreMutator(7)
    FortyGoals = MaxScoreMutator(8)
    FiftyGoals = MaxScoreMutator(9)
    SixtyGoals = MaxScoreMutator(10)
    SeventyGoals = MaxScoreMutator(11)
    EightyGoals = MaxScoreMutator(12)
    NinetyGoals = MaxScoreMutator(13)
    HundredGoals = MaxScoreMutator(14)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: MaxScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MaxTimeMutator:
    Unlimited = MaxTimeMutator(0)
    ElevenMinutes = MaxTimeMutator(1)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: MaxTimeMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MultiBallMutator:
    One = MultiBallMutator(0)
    Two = MultiBallMutator(1)
    Four = MultiBallMutator(2)
    Six = MultiBallMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: MultiBallMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class MutatorSettings:
    """
    All mutators options.
    """
    match_length: MatchLengthMutator
    """
    Duration of the match.
    """
    max_score: MaxScoreMutator
    """
    Max score of match. If this score is reached, the team immediately wins.
    """
    multi_ball: MultiBallMutator
    """
    The number of balls.
    """
    overtime: OvertimeMutator
    """
    The overtime rules and tiebreaker.
    """
    series_length: SeriesLengthMutator
    """
    The series length.
    """
    game_speed: GameSpeedMutator
    """
    A game speed multiplier.
    """
    ball_max_speed: BallMaxSpeedMutator
    """
    Ball max speed.
    """
    ball_type: BallTypeMutator
    """
    Ball type and shape.
    """
    ball_weight: BallWeightMutator
    """
    Ball weight and how much is curves.
    """
    ball_size: BallSizeMutator
    """
    Ball size.
    """
    ball_bounciness: BallBouncinessMutator
    """
    Ball bounciness.
    """
    boost_amount: BoostAmountMutator
    """
    Boost amount/recharge.
    """
    rumble: RumbleMutator
    """
    Rumble item rules.
    """
    boost_strength: BoostStrengthMutator
    """
    Boost strength multiplier.
    """
    gravity: GravityMutator
    """
    Strength of gravity.
    """
    demolish: DemolishMutator
    """
    Demolition conditions.
    """
    respawn_time: RespawnTimeMutator
    """
    Demolition respawn time.
    """
    max_time: MaxTimeMutator
    """
    Max real-time duration of match including kickoff, replays, and more.
    If the score is tied upon time-out, the number of shots determine the winner.
    """
    game_event: GameEventMutator
    """
    Additional game behaviour for custom modes.
    """
    audio: AudioMutator
    """
    Additional audio options for custom modes.
    """
    ball_gravity: BallGravityMutator
    """
    Ball gravity.
    """
    territory: TerritoryMutator
    """
    Territory mutator.
    """
    stale_ball: StaleBallMutator
    """
    Stale ball mutator.
    """
    jump: JumpMutator
    """
    Jumps mutator.
    """
    dodge_timer: DodgeTimerMutator
    """
    Dodge timer mutator.
    """
    possession_score: PossessionScoreMutator
    """
    Possession score mutator.
    """
    demolish_score: DemolishScoreMutator
    """
    Demolish score mutator.
    """
    normal_goal_score: NormalGoalScoreMutator
    """
    Normal goal score mutator.
    """
    aerial_goal_score: AerialGoalScoreMutator
    """
    Aerial goal score mutator.
    """
    assist_goal_score: AssistGoalScoreMutator
    """
    Assist goal score mutator.
    """
    input_restriction: InputRestrictionMutator
    """
    Player input restriction mutator.
    """

    __match_args__ = (
        "match_length",
        "max_score",
        "multi_ball",
        "overtime",
        "series_length",
        "game_speed",
        "ball_max_speed",
        "ball_type",
        "ball_weight",
        "ball_size",
        "ball_bounciness",
        "boost_amount",
        "rumble",
        "boost_strength",
        "gravity",
        "demolish",
        "respawn_time",
        "max_time",
        "game_event",
        "audio",
        "ball_gravity",
        "territory",
        "stale_ball",
        "jump",
        "dodge_timer",
        "possession_score",
        "demolish_score",
        "normal_goal_score",
        "aerial_goal_score",
        "assist_goal_score",
        "input_restriction",
    )

    def __new__(
        cls,
        match_length: MatchLengthMutator = MatchLengthMutator(),
        max_score: MaxScoreMutator = MaxScoreMutator(),
        multi_ball: MultiBallMutator = MultiBallMutator(),
        overtime: OvertimeMutator = OvertimeMutator(),
        series_length: SeriesLengthMutator = SeriesLengthMutator(),
        game_speed: GameSpeedMutator = GameSpeedMutator(),
        ball_max_speed: BallMaxSpeedMutator = BallMaxSpeedMutator(),
        ball_type: BallTypeMutator = BallTypeMutator(),
        ball_weight: BallWeightMutator = BallWeightMutator(),
        ball_size: BallSizeMutator = BallSizeMutator(),
        ball_bounciness: BallBouncinessMutator = BallBouncinessMutator(),
        boost_amount: BoostAmountMutator = BoostAmountMutator(),
        rumble: RumbleMutator = RumbleMutator(),
        boost_strength: BoostStrengthMutator = BoostStrengthMutator(),
        gravity: GravityMutator = GravityMutator(),
        demolish: DemolishMutator = DemolishMutator(),
        respawn_time: RespawnTimeMutator = RespawnTimeMutator(),
        max_time: MaxTimeMutator = MaxTimeMutator(),
        game_event: GameEventMutator = GameEventMutator(),
        audio: AudioMutator = AudioMutator(),
        ball_gravity: BallGravityMutator = BallGravityMutator(),
        territory: TerritoryMutator = TerritoryMutator(),
        stale_ball: StaleBallMutator = StaleBallMutator(),
        jump: JumpMutator = JumpMutator(),
        dodge_timer: DodgeTimerMutator = DodgeTimerMutator(),
        possession_score: PossessionScoreMutator = PossessionScoreMutator(),
        demolish_score: DemolishScoreMutator = DemolishScoreMutator(),
        normal_goal_score: NormalGoalScoreMutator = NormalGoalScoreMutator(),
        aerial_goal_score: AerialGoalScoreMutator = AerialGoalScoreMutator(),
        assist_goal_score: AssistGoalScoreMutator = AssistGoalScoreMutator(),
        input_restriction: InputRestrictionMutator = InputRestrictionMutator(),
    ): ...
    def __init__(
        self,
        match_length: MatchLengthMutator = MatchLengthMutator(),
        max_score: MaxScoreMutator = MaxScoreMutator(),
        multi_ball: MultiBallMutator = MultiBallMutator(),
        overtime: OvertimeMutator = OvertimeMutator(),
        series_length: SeriesLengthMutator = SeriesLengthMutator(),
        game_speed: GameSpeedMutator = GameSpeedMutator(),
        ball_max_speed: BallMaxSpeedMutator = BallMaxSpeedMutator(),
        ball_type: BallTypeMutator = BallTypeMutator(),
        ball_weight: BallWeightMutator = BallWeightMutator(),
        ball_size: BallSizeMutator = BallSizeMutator(),
        ball_bounciness: BallBouncinessMutator = BallBouncinessMutator(),
        boost_amount: BoostAmountMutator = BoostAmountMutator(),
        rumble: RumbleMutator = RumbleMutator(),
        boost_strength: BoostStrengthMutator = BoostStrengthMutator(),
        gravity: GravityMutator = GravityMutator(),
        demolish: DemolishMutator = DemolishMutator(),
        respawn_time: RespawnTimeMutator = RespawnTimeMutator(),
        max_time: MaxTimeMutator = MaxTimeMutator(),
        game_event: GameEventMutator = GameEventMutator(),
        audio: AudioMutator = AudioMutator(),
        ball_gravity: BallGravityMutator = BallGravityMutator(),
        territory: TerritoryMutator = TerritoryMutator(),
        stale_ball: StaleBallMutator = StaleBallMutator(),
        jump: JumpMutator = JumpMutator(),
        dodge_timer: DodgeTimerMutator = DodgeTimerMutator(),
        possession_score: PossessionScoreMutator = PossessionScoreMutator(),
        demolish_score: DemolishScoreMutator = DemolishScoreMutator(),
        normal_goal_score: NormalGoalScoreMutator = NormalGoalScoreMutator(),
        aerial_goal_score: AerialGoalScoreMutator = AerialGoalScoreMutator(),
        assist_goal_score: AssistGoalScoreMutator = AssistGoalScoreMutator(),
        input_restriction: InputRestrictionMutator = InputRestrictionMutator(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> MutatorSettings:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class NormalGoalScoreMutator:
    One = NormalGoalScoreMutator(0)
    Zero = NormalGoalScoreMutator(1)
    Two = NormalGoalScoreMutator(2)
    Three = NormalGoalScoreMutator(3)
    Five = NormalGoalScoreMutator(4)
    Ten = NormalGoalScoreMutator(5)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: NormalGoalScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class OvertimeMutator:
    Unlimited = OvertimeMutator(0)
    FiveMaxFirstScore = OvertimeMutator(1)
    FiveMaxRandomTeam = OvertimeMutator(2)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: OvertimeMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Physics:
    location: Vector3
    rotation: Rotator
    velocity: Vector3
    angular_velocity: Vector3

    __match_args__ = (
        "location",
        "rotation",
        "velocity",
        "angular_velocity",
    )

    def __new__(
        cls,
        location: Vector3 = Vector3(),
        rotation: Rotator = Rotator(),
        velocity: Vector3 = Vector3(),
        angular_velocity: Vector3 = Vector3(),
    ): ...
    def __init__(
        self,
        location: Vector3 = Vector3(),
        rotation: Rotator = Rotator(),
        velocity: Vector3 = Vector3(),
        angular_velocity: Vector3 = Vector3(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Physics:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PlayerClass:
    item: Human | CustomBot | PsyonixBot

    def __new__(
        cls, item: Human | CustomBot | PsyonixBot = Human()
    ): ...
    def __init__(
        self, item: Human | CustomBot | PsyonixBot = Human()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PlayerConfiguration:
    """
    A PlayerConfiguration defines a player of a match.
    """
    variety: PlayerClass
    """
    The type of the player, i.e. human, Psyonix bot, or a custom bot.
    """
    team: int
    """
    The team of the player. Blue is 0, orange is 1.
    """
    player_id: int
    """
    The value will be set by RLBot and is always overriden.
    This value is mostly used internally to keep track of participants in the match.
    The player id can be used to find the corresponding player in the GamePacket.
    """

    __match_args__ = (
        "variety",
        "team",
        "player_id",
    )

    def __new__(
        cls,
        variety: Human | CustomBot | PsyonixBot = Human(),
        team: int = 0,
        player_id: int = 0,
    ): ...
    def __init__(
        self,
        variety: Human | CustomBot | PsyonixBot = Human(),
        team: int = 0,
        player_id: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PlayerConfiguration:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PlayerInfo:
    """
    A collection of information about a player and their car.
    """
    physics: Physics
    """
    The physical state of the player's car.
    """
    score_info: ScoreInfo
    """
    The various scores of this player, e.g. those on the leaderboard.
    """
    hitbox: BoxShape
    """
    The hitbox of the player's car.
    Note that the hitbox is not centered at the cars location.
    See the hitbox offset.
    """
    hitbox_offset: Vector3
    """
    The center of the hitbox in local coordinates.
    """
    latest_touch: Optional[Touch]
    """
    Information about the latest touch with a ball.
    Is null if the player has yet to touch the ball.
    """
    air_state: AirState
    """
    Whether the player's car is on the ground or in the air, and what jump/dodging forces currently affects the car.
    """
    dodge_timeout: float
    """
    How long until the player cannot dodge/double jump anymore.
    The value is -1 while on ground or when airborne for too long after jumping.
    A dodge/double jump is possible for 1.25 seconds after the first jump plus
    up to an additional 0.2 seconds depending how long the jump button was pressed for the first jump.
    """
    demolished_timeout: float
    """
    How long until the player is not demolished anymore.
    The value is -1 if while not demolished.
    """
    is_supersonic: bool
    """
    Whether the player's car is moving at supersonic speed and can demolish.
    """
    is_bot: bool
    """
    Whether the player is a bot or a human.
    """
    name: str
    """
    The name of the player as it appears in game, i.e. possibly appended with "(2)".
    The original name can be found in the match configuration.
    """
    team: int
    """
    The team of the player.
    """
    boost: float
    """
    The current boost, from 0 to 100.
    """
    player_id: int
    """
    The id of the player.
    This value is mostly used internally to keep track of participants in the match.
    The id can be used to find the corresponding PlayerConfiguration in the MatchConfiguration.
    """
    accolades: Sequence[str]
    """
    Events from the latest tick involving this player. Possible values include:
    Win, Loss, TimePlayed;
    Shot, Assist, Center, Clear, PoolShot;
    Goal, AerialGoal, BicycleGoal, BulletGoal, BackwardsGoal, LongGoal, OvertimeGoal, TurtleGoal;
    AerialHit, BicycleHit, BulletHit, JuggleHit, FirstTouch, BallHit;
    Save, EpicSave, FreezeSave;
    HatTrick, Savior, Playmaker, MVP;
    FastestGoal, SlowestGoal, FurthestGoal, OwnGoal;
    MostBallTouches, FewestBallTouches, MostBoostPickups, FewestBoostPickups, BoostPickups;
    CarTouches, Demolition, Demolish;
    LowFive, HighFive;
    Note that the list clears every tick.
    """
    last_input: ControllerState
    """
    The last controller input from this player.
    """
    has_jumped: bool
    """
    True if the player has jumped. See dodge_timeout to know if a dodge/secondary jump is available.
    """
    has_double_jumped: bool
    """
    True if the player has doubled jumped.
    """
    has_dodged: bool
    """
    True if the player has dodged.
    """
    dodge_elapsed: float
    """
    The time in seconds since the last dodge was initiated.
    Resets to 0 when the player lands on the ground.
    """
    dodge_dir: Vector2
    """
    The unit direction of the latest dodge.
    The value will be (0,0) if it was a stall.
    """

    __match_args__ = (
        "physics",
        "score_info",
        "hitbox",
        "hitbox_offset",
        "latest_touch",
        "air_state",
        "dodge_timeout",
        "demolished_timeout",
        "is_supersonic",
        "is_bot",
        "name",
        "team",
        "boost",
        "player_id",
        "accolades",
        "last_input",
        "has_jumped",
        "has_double_jumped",
        "has_dodged",
        "dodge_elapsed",
        "dodge_dir",
    )

    def __new__(
        cls,
        physics: Physics = Physics(),
        score_info: ScoreInfo = ScoreInfo(),
        hitbox: BoxShape = BoxShape(),
        hitbox_offset: Vector3 = Vector3(),
        latest_touch: Optional[Touch] = None,
        air_state: AirState = AirState(),
        dodge_timeout: float = 0,
        demolished_timeout: float = 0,
        is_supersonic: bool = False,
        is_bot: bool = False,
        name: str = "",
        team: int = 0,
        boost: float = 0,
        player_id: int = 0,
        accolades: Sequence[str] = [],
        last_input: ControllerState = ControllerState(),
        has_jumped: bool = False,
        has_double_jumped: bool = False,
        has_dodged: bool = False,
        dodge_elapsed: float = 0,
        dodge_dir: Vector2 = Vector2(),
    ): ...
    def __init__(
        self,
        physics: Physics = Physics(),
        score_info: ScoreInfo = ScoreInfo(),
        hitbox: BoxShape = BoxShape(),
        hitbox_offset: Vector3 = Vector3(),
        latest_touch: Optional[Touch] = None,
        air_state: AirState = AirState(),
        dodge_timeout: float = 0,
        demolished_timeout: float = 0,
        is_supersonic: bool = False,
        is_bot: bool = False,
        name: str = "",
        team: int = 0,
        boost: float = 0,
        player_id: int = 0,
        accolades: Sequence[str] = [],
        last_input: ControllerState = ControllerState(),
        has_jumped: bool = False,
        has_double_jumped: bool = False,
        has_dodged: bool = False,
        dodge_elapsed: float = 0,
        dodge_dir: Vector2 = Vector2(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PlayerInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PlayerInput:
    """
    A player index and the controller state of that player.
    Used to indicate what the player is doing this tick.
    """
    player_index: int
    controller_state: ControllerState

    __match_args__ = (
        "player_index",
        "controller_state",
    )

    def __new__(
        cls,
        player_index: int = 0,
        controller_state: ControllerState = ControllerState(),
    ): ...
    def __init__(
        self,
        player_index: int = 0,
        controller_state: ControllerState = ControllerState(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PlayerInput:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PlayerLoadout:
    """
    Defines the car type, color, and other aspects of the player's appearance.
    See https://wiki.rlbot.org/botmaking/bot-customization/
    """
    team_color_id: int
    custom_color_id: int
    car_id: int
    decal_id: int
    wheels_id: int
    boost_id: int
    antenna_id: int
    hat_id: int
    paint_finish_id: int
    custom_finish_id: int
    engine_audio_id: int
    trails_id: int
    goal_explosion_id: int
    loadout_paint: Optional[LoadoutPaint]
    primary_color_lookup: Optional[Color]
    """
    Sets the primary color of the car to the swatch that most closely matches the provided
    RGB color value. If set, this overrides teamColorId.
    """
    secondary_color_lookup: Optional[Color]
    """
    Sets the secondary color of the car to the swatch that most closely matches the provided
    RGB color value. If set, this overrides customColorId.
    """

    __match_args__ = (
        "team_color_id",
        "custom_color_id",
        "car_id",
        "decal_id",
        "wheels_id",
        "boost_id",
        "antenna_id",
        "hat_id",
        "paint_finish_id",
        "custom_finish_id",
        "engine_audio_id",
        "trails_id",
        "goal_explosion_id",
        "loadout_paint",
        "primary_color_lookup",
        "secondary_color_lookup",
    )

    def __new__(
        cls,
        team_color_id: int = 0,
        custom_color_id: int = 0,
        car_id: int = 0,
        decal_id: int = 0,
        wheels_id: int = 0,
        boost_id: int = 0,
        antenna_id: int = 0,
        hat_id: int = 0,
        paint_finish_id: int = 0,
        custom_finish_id: int = 0,
        engine_audio_id: int = 0,
        trails_id: int = 0,
        goal_explosion_id: int = 0,
        loadout_paint: Optional[LoadoutPaint] = None,
        primary_color_lookup: Optional[Color] = None,
        secondary_color_lookup: Optional[Color] = None,
    ): ...
    def __init__(
        self,
        team_color_id: int = 0,
        custom_color_id: int = 0,
        car_id: int = 0,
        decal_id: int = 0,
        wheels_id: int = 0,
        boost_id: int = 0,
        antenna_id: int = 0,
        hat_id: int = 0,
        paint_finish_id: int = 0,
        custom_finish_id: int = 0,
        engine_audio_id: int = 0,
        trails_id: int = 0,
        goal_explosion_id: int = 0,
        loadout_paint: Optional[LoadoutPaint] = None,
        primary_color_lookup: Optional[Color] = None,
        secondary_color_lookup: Optional[Color] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PlayerLoadout:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PolyLine3D:
    """
    A RenderMessage for a line in 3D space going through a series of points.
    """
    points: Sequence[Vector3]
    color: Color

    __match_args__ = (
        "points",
        "color",
    )

    def __new__(
        cls,
        points: Sequence[Vector3] = [],
        color: Color = Color(),
    ): ...
    def __init__(
        self,
        points: Sequence[Vector3] = [],
        color: Color = Color(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PolyLine3D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PossessionScoreMutator:
    Off = PossessionScoreMutator(0)
    OneSecond = PossessionScoreMutator(1)
    TwoSeconds = PossessionScoreMutator(2)
    ThreeSeconds = PossessionScoreMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: PossessionScoreMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PredictionSlice:
    game_seconds: float
    """
    The moment in game time that this prediction corresponds to.
    """
    physics: Physics

    __match_args__ = (
        "game_seconds",
        "physics",
    )

    def __new__(
        cls,
        game_seconds: float = 0,
        physics: Physics = Physics(),
    ): ...
    def __init__(
        self,
        game_seconds: float = 0,
        physics: Physics = Physics(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PredictionSlice:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PsyonixBot:
    """
    A Psyonix bot, e.g. All Star bot.
    """
    name: str
    """
    Requested bot name. When match start, RLBot will ensure each bot has a unique name; bots with
    duplicate names will be renamed with a suffix like `(2)`. For psyonix bots, a blank name will
    be replaced with one of the official names.
    """
    loadout: Optional[PlayerLoadout]
    """
    The loadout of the player.
    """
    bot_skill: PsyonixSkill

    __match_args__ = (
        "name",
        "loadout",
        "bot_skill",
    )

    def __new__(
        cls,
        name: str = "",
        loadout: Optional[PlayerLoadout] = None,
        bot_skill: PsyonixSkill = PsyonixSkill(),
    ): ...
    def __init__(
        self,
        name: str = "",
        loadout: Optional[PlayerLoadout] = None,
        bot_skill: PsyonixSkill = PsyonixSkill(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> PsyonixBot:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class PsyonixSkill:
    Beginner = PsyonixSkill(0)
    Rookie = PsyonixSkill(1)
    Pro = PsyonixSkill(2)
    AllStar = PsyonixSkill(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: PsyonixSkill) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Rect2D:
    """
    A RenderMessage for a rectangle in 2D space.
    Note that the position and size is given in screen-space coordinates.
    """
    x: float
    """
    Screen-space x coordinate such that x=0 is left edge and x=1 is right edge of window.
    """
    y: float
    """
    Screen-space y coordinate such that y=0 is top edge and y=1 is bottom edge of window.
    """
    width: float
    """
    Screen-space size such that width=0.1 is 10% of window width.
    """
    height: float
    """
    Screen-space size such that height=0.1 is 10% of window height.
    """
    color: Color
    """
    Color of the rectangle.
    """
    h_align: TextHAlign
    """
    The horizontal alignment of the rectangle.
    """
    v_align: TextVAlign
    """
    The vertical alignment of the rectangle.
    """

    __match_args__ = (
        "x",
        "y",
        "width",
        "height",
        "color",
        "h_align",
        "v_align",
    )

    def __new__(
        cls,
        x: float = 0,
        y: float = 0,
        width: float = 0,
        height: float = 0,
        color: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: float = 0,
        height: float = 0,
        color: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Rect2D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Rect3D:
    """
    A RenderMessage for a rectangle in 3D space.
    Note that the size is given in screen-space sizes.
    """
    anchor: RenderAnchor
    """
    The position of the rectangle.
    """
    width: float
    """
    Screen-space size such that width=0.1 is 10% of window width.
    """
    height: float
    """
    Screen-space size such that height=0.1 is 10% of window height.
    """
    color: Color
    """
    The color of the rectangle.
    """
    h_align: TextHAlign
    """
    The horizontal alignment of the anchor in the rectangle.
    """
    v_align: TextVAlign
    """
    The vertical alignment of the anchor in the rectangle.
    """

    __match_args__ = (
        "anchor",
        "width",
        "height",
        "color",
        "h_align",
        "v_align",
    )

    def __new__(
        cls,
        anchor: RenderAnchor = RenderAnchor(),
        width: float = 0,
        height: float = 0,
        color: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def __init__(
        self,
        anchor: RenderAnchor = RenderAnchor(),
        width: float = 0,
        height: float = 0,
        color: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Rect3D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RelativeAnchor:
    item: BallAnchor | CarAnchor

    def __new__(
        cls, item: BallAnchor | CarAnchor = BallAnchor()
    ): ...
    def __init__(
        self, item: BallAnchor | CarAnchor = BallAnchor()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RemoveRenderGroup:
    """
    A client message request removal of a RenderGroup.
    A client can only clear its own RenderGroups.
    """
    id: int

    __match_args__ = (
        "id",
    )

    def __new__(
        cls,
        id: int = 0,
    ): ...
    def __init__(
        self,
        id: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RemoveRenderGroup:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RenderAnchor:
    """
    A RenderAnchor is a point in space consisting of a world component and optionally a relative component.
    The relative component is given by a car or ball and includes a local offset that takes the orientation of the object into account.
    The RenderAnchor stays attached to the object and does not have to be updated each tick.
    Rendering that uses a RenderAnchor attached to an object disappears if the object is destroyed, i.e. the car demolished or the ball is scored.
    """
    world: Vector3
    """
    An offset in global coordinates.
    If the relative component is null, then this simply a point in 3D space.
    """
    relative: Optional[RelativeAnchor]
    """
    An optional offset given by the position of an object and includes a local offset that takes the object's orientation into account.
    """

    __match_args__ = (
        "world",
        "relative",
    )

    def __new__(
        cls,
        world: Vector3 = Vector3(),
        relative: Optional[BallAnchor | CarAnchor] = None,
    ): ...
    def __init__(
        self,
        world: Vector3 = Vector3(),
        relative: Optional[BallAnchor | CarAnchor] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RenderAnchor:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RenderGroup:
    """
    A group of RenderMessages that are drawn and cleared together.
    A RenderGroup will stay rendered until it is overriden or cleared.
    The group is identified by a unique id.
    A client can only clear its own RenderGroups.
    """
    render_messages: Sequence[RenderMessage]
    """
    The content of the RenderGroup.
    """
    id: int
    """
    The id of the RenderGroup.
    """

    __match_args__ = (
        "render_messages",
        "id",
    )

    def __new__(
        cls,
        render_messages: Sequence[RenderMessage] = [],
        id: int = 0,
    ): ...
    def __init__(
        self,
        render_messages: Sequence[RenderMessage] = [],
        id: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RenderGroup:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RenderMessage:
    """
    A RenderMessage, describing a piece of debug rendering.
    """
    variety: RenderType

    __match_args__ = (
        "variety",
    )

    def __new__(
        cls,
        variety: Line3D | PolyLine3D | String2D | String3D | Rect2D | Rect3D = Line3D(),
    ): ...
    def __init__(
        self,
        variety: Line3D | PolyLine3D | String2D | String3D | Rect2D | Rect3D = Line3D(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RenderMessage:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RenderType:
    item: Line3D | PolyLine3D | String2D | String3D | Rect2D | Rect3D

    def __new__(
        cls, item: Line3D | PolyLine3D | String2D | String3D | Rect2D | Rect3D = Line3D()
    ): ...
    def __init__(
        self, item: Line3D | PolyLine3D | String2D | String3D | Rect2D | Rect3D = Line3D()
    ): ...

    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RenderingStatus:
    """
    As an interface message, this requests for a specificed agent to have its ability to render changed.
    This changed will then be broadcasted to all current connections as a core message.
    Does nothing if rendering has been completely disabled.
    """
    index: int
    """
    If `is_bot`, this is the index of the bot in `GamePacket` that has been updated.
    Otherwise, this is the index of the script in `MatchConfiguration` that has been updated.
    """
    is_bot: bool
    """
    Identifies if the index is that of a bot or a script
    """
    status: bool
    """
    If rendering is now enabled or disabled for the specific agent
    """

    __match_args__ = (
        "index",
        "is_bot",
        "status",
    )

    def __new__(
        cls,
        index: int = 0,
        is_bot: bool = False,
        status: bool = False,
    ): ...
    def __init__(
        self,
        index: int = 0,
        is_bot: bool = False,
        status: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RenderingStatus:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RespawnTimeMutator:
    ThreeSeconds = RespawnTimeMutator(0)
    TwoSeconds = RespawnTimeMutator(1)
    OneSecond = RespawnTimeMutator(2)
    DisableGoalReset = RespawnTimeMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: RespawnTimeMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Rotator:
    pitch: float
    yaw: float
    roll: float

    __match_args__ = (
        "pitch",
        "yaw",
        "roll",
    )

    def __new__(
        cls,
        pitch: float = 0,
        yaw: float = 0,
        roll: float = 0,
    ): ...
    def __init__(
        self,
        pitch: float = 0,
        yaw: float = 0,
        roll: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Rotator:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RotatorPartial:
    """
    A rotator describing a rotation with nullable pith, yaw, and roll.
    Used for game state setting to define which part of a rotator should change.
    If a component is null, then the component will keep its current value.
    Values are in radians.
    """
    pitch: Optional[Float]
    """
    In radians with range (-pi/2,+pi/2) where 0 is flat, +pi/2 is nose straight up, -pi/2 is nose straight down.
    """
    yaw: Optional[Float]
    """
    In radians with range [-pi,+pi) where 0 is towards positive x, rotating clockwise as increased (when seen from above).
    """
    roll: Optional[Float]
    """
    In radians with range (-pi,+pi) where 0 is upright, positive is tilted right, negative is tilted left.
    """

    __match_args__ = (
        "pitch",
        "yaw",
        "roll",
    )

    def __new__(
        cls,
        pitch: Optional[Float | float] = None,
        yaw: Optional[Float | float] = None,
        roll: Optional[Float | float] = None,
    ): ...
    def __init__(
        self,
        pitch: Optional[Float | float] = None,
        yaw: Optional[Float | float] = None,
        roll: Optional[Float | float] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> RotatorPartial:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class RumbleMutator:
    Off = RumbleMutator(0)
    DefaultRumble = RumbleMutator(1)
    Slow = RumbleMutator(2)
    Civilized = RumbleMutator(3)
    DestructionDerby = RumbleMutator(4)
    SpringLoaded = RumbleMutator(5)
    SpikesOnly = RumbleMutator(6)
    SpikeRush = RumbleMutator(7)
    HauntedBallBeam = RumbleMutator(8)
    Tactical = RumbleMutator(9)
    BatmanRumble = RumbleMutator(10)
    GrapplingOnly = RumbleMutator(11)
    HaymakerOnly = RumbleMutator(12)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: RumbleMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ScoreInfo:
    score: int
    goals: int
    own_goals: int
    assists: int
    saves: int
    shots: int
    demolitions: int

    __match_args__ = (
        "score",
        "goals",
        "own_goals",
        "assists",
        "saves",
        "shots",
        "demolitions",
    )

    def __new__(
        cls,
        score: int = 0,
        goals: int = 0,
        own_goals: int = 0,
        assists: int = 0,
        saves: int = 0,
        shots: int = 0,
        demolitions: int = 0,
    ): ...
    def __init__(
        self,
        score: int = 0,
        goals: int = 0,
        own_goals: int = 0,
        assists: int = 0,
        saves: int = 0,
        shots: int = 0,
        demolitions: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ScoreInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class ScriptConfiguration:
    """
    A ScriptConfiguration defines a script of a match.
    """
    name: str
    """
    The name of the script.
    """
    root_dir: str
    """
    The root directory of the script and the working directory for the run command.
    """
    run_command: str
    """
    A console command that will start up the script.
    """
    script_id: int
    """
    The id of the script.
    This value is mostly used internally to keep track of participants in the match.
    """
    agent_id: str
    """
    A unique user-defined string that is used to connect clients to the right players/scripts.
    If a bot/script has a run command, RLBot will pass this agent id to the process using an environment variable, RLBOT_AGENT_ID.
    Upon connecting the process announces that it is responsible for this agent id and RLBot will pair the two.
    The recommended format for agent ids is "developername/botname".
    """

    __match_args__ = (
        "name",
        "root_dir",
        "run_command",
        "script_id",
        "agent_id",
    )

    def __new__(
        cls,
        name: str = "",
        root_dir: str = "",
        run_command: str = "",
        script_id: int = 0,
        agent_id: str = "",
    ): ...
    def __init__(
        self,
        name: str = "",
        root_dir: str = "",
        run_command: str = "",
        script_id: int = 0,
        agent_id: str = "",
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> ScriptConfiguration:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class SeriesLengthMutator:
    Unlimited = SeriesLengthMutator(0)
    ThreeGames = SeriesLengthMutator(1)
    FiveGames = SeriesLengthMutator(2)
    SevenGames = SeriesLengthMutator(3)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: SeriesLengthMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class SetLoadout:
    """
    A client message to change the loadout of a car.
    If sent before the ready message, this simply sets the loadout of the car.
    If sent after the ready message and if game state setting is enabled, this will respawn the car with the new loadout.
    Bots can only set the loadout of their own car(s).
    """
    index: int
    """
    The index of the car to change loadout off.
    """
    loadout: PlayerLoadout
    """
    The new loadout of the car.
    """

    __match_args__ = (
        "index",
        "loadout",
    )

    def __new__(
        cls,
        index: int = 0,
        loadout: PlayerLoadout = PlayerLoadout(),
    ): ...
    def __init__(
        self,
        index: int = 0,
        loadout: PlayerLoadout = PlayerLoadout(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> SetLoadout:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class SphereShape:
    """
    A sphere with diameter.
    Used for balls with a spherical shapes.
    """
    diameter: float

    __match_args__ = (
        "diameter",
    )

    def __new__(
        cls,
        diameter: float = 0,
    ): ...
    def __init__(
        self,
        diameter: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> SphereShape:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class StaleBallMutator:
    Unlimited = StaleBallMutator(0)
    ThirtySeconds = StaleBallMutator(1)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: StaleBallMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class StartCommand:
    """
    A client message to start a match using a path to a match config file.
    """
    config_path: str

    __match_args__ = (
        "config_path",
    )

    def __new__(
        cls,
        config_path: str = "",
    ): ...
    def __init__(
        self,
        config_path: str = "",
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> StartCommand:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class StopCommand:
    """
    A client message to stop a match and optionally the RLBot server too.
    """
    shutdown_server: bool

    __match_args__ = (
        "shutdown_server",
    )

    def __new__(
        cls,
        shutdown_server: bool = False,
    ): ...
    def __init__(
        self,
        shutdown_server: bool = False,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> StopCommand:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class String2D:
    """
    A RenderMessage for text in 2D space.
    Note that the position is given in screen-space coordinates.
    """
    text: str
    """
    The text to be displayed.
    """
    x: float
    """
    Screen-space x coordinate such that x=0 is left edge and x=1 is right edge of window.
    """
    y: float
    """
    Screen-space y coordinate such that y=0 is top edge and y=1 is bottom edge of window.
    """
    scale: float
    """
    Scale of the text.
    When scale is 1, the characters are 20 pixels tall and 10 pixels wide.
    """
    foreground: Color
    """
    The color of the text.
    """
    background: Color
    """
    The color of the background for the text.
    """
    h_align: TextHAlign
    """
    The horizontal alignment of the text.
    """
    v_align: TextVAlign
    """
    The vertical alignment of the text.
    """

    __match_args__ = (
        "text",
        "x",
        "y",
        "scale",
        "foreground",
        "background",
        "h_align",
        "v_align",
    )

    def __new__(
        cls,
        text: str = "",
        x: float = 0,
        y: float = 0,
        scale: float = 0,
        foreground: Color = Color(),
        background: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def __init__(
        self,
        text: str = "",
        x: float = 0,
        y: float = 0,
        scale: float = 0,
        foreground: Color = Color(),
        background: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> String2D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class String3D:
    """
    A RenderMessage for text in 3D space.
    """
    text: str
    """
    The text to be displayed.
    """
    anchor: RenderAnchor
    """
    The position of the text.
    """
    scale: float
    """
    The scale of the text.
    When scale is 1, the characters are 20 pixels tall and 10 pixels wide.
    """
    foreground: Color
    """
    The color of the text.
    """
    background: Color
    """
    The color of the background for the text.
    """
    h_align: TextHAlign
    """
    The horizontal alignment of the text.
    """
    v_align: TextVAlign
    """
    The vertical alignment of the text.
    """

    __match_args__ = (
        "text",
        "anchor",
        "scale",
        "foreground",
        "background",
        "h_align",
        "v_align",
    )

    def __new__(
        cls,
        text: str = "",
        anchor: RenderAnchor = RenderAnchor(),
        scale: float = 0,
        foreground: Color = Color(),
        background: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def __init__(
        self,
        text: str = "",
        anchor: RenderAnchor = RenderAnchor(),
        scale: float = 0,
        foreground: Color = Color(),
        background: Color = Color(),
        h_align: TextHAlign = TextHAlign(),
        v_align: TextVAlign = TextVAlign(),
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> String3D:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class TeamInfo:
    team_index: int
    score: int
    """
    Number of goals scored.
    Note, this value may be different than the sum of the goals scored by the current players on the team as player may join/leave the game or switch teams.
    """

    __match_args__ = (
        "team_index",
        "score",
    )

    def __new__(
        cls,
        team_index: int = 0,
        score: int = 0,
    ): ...
    def __init__(
        self,
        team_index: int = 0,
        score: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> TeamInfo:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class TerritoryMutator:
    Off = TerritoryMutator(0)
    Territory = TerritoryMutator(1)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: TerritoryMutator) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class TextHAlign:
    Left = TextHAlign(0)
    Center = TextHAlign(1)
    Right = TextHAlign(2)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: TextHAlign) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class TextVAlign:
    Top = TextVAlign(0)
    Center = TextVAlign(1)
    Bottom = TextVAlign(2)

    def __new__(cls, value: int = 0): ...
    def __init__(self, value: int = 0):
        """
        :raises ValueError: If the `value` is not a valid enum value
        """
    def __int__(self) -> int: ...
    def __eq__(self, other: TextVAlign) -> bool: ...
    def __hash__(self) -> str: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Touch:
    """
    Information about a ball touch.
    """
    game_seconds: float
    """
    Seconds that had elapsed in the game when the touch occurred.
    """
    location: Vector3
    """
    The point of contact for the touch.
    """
    normal: Vector3
    """
    The direction of the touch as a unit vector pointing from the point of contact towards the center of the ball.
    """
    ball_index: int
    """
    The index of the ball that was touched (in case there are multiple balls).
    """

    __match_args__ = (
        "game_seconds",
        "location",
        "normal",
        "ball_index",
    )

    def __new__(
        cls,
        game_seconds: float = 0,
        location: Vector3 = Vector3(),
        normal: Vector3 = Vector3(),
        ball_index: int = 0,
    ): ...
    def __init__(
        self,
        game_seconds: float = 0,
        location: Vector3 = Vector3(),
        normal: Vector3 = Vector3(),
        ball_index: int = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Touch:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Vector2:
    x: float
    y: float

    __match_args__ = (
        "x",
        "y",
    )

    def __new__(
        cls,
        x: float = 0,
        y: float = 0,
    ): ...
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Vector2:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Vector3:
    x: float
    y: float
    z: float

    __match_args__ = (
        "x",
        "y",
        "z",
    )

    def __new__(
        cls,
        x: float = 0,
        y: float = 0,
        z: float = 0,
    ): ...
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        z: float = 0,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Vector3:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

class Vector3Partial:
    """
    A 3D vector where x, y, and z can be null.
    Used for game state setting to define which part of a vector should change.
    If a component is null, then the component will keep its current value.
    """
    x: Optional[Float]
    y: Optional[Float]
    z: Optional[Float]

    __match_args__ = (
        "x",
        "y",
        "z",
    )

    def __new__(
        cls,
        x: Optional[Float | float] = None,
        y: Optional[Float | float] = None,
        z: Optional[Float | float] = None,
    ): ...
    def __init__(
        self,
        x: Optional[Float | float] = None,
        y: Optional[Float | float] = None,
        z: Optional[Float | float] = None,
    ): ...
    def pack(self) -> bytes:
        """
        Serializes this instance into a byte array
        """
    @staticmethod
    def unpack(data: bytes) -> Vector3Partial:
        """
        Deserializes the data into a new instance

        :raises InvalidFlatbuffer: If the `data` is invalid for this type
        """
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
