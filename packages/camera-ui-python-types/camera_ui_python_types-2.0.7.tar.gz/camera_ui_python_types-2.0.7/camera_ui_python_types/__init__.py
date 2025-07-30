from abc import ABCMeta, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Coroutine
from enum import Enum
from typing import Any, Callable, Generic, Optional, Union, overload, runtime_checkable

from PIL import Image
from typing_extensions import Literal, NotRequired, Protocol, TypedDict, TypeVar

from .hybrid_observer import HybridObservable

# Literals
FrameType = Literal["stream", "motion"]
CameraType = Literal["camera", "doorbell"]
ZoneType = Literal["intersect", "contain"]
ZoneFilter = Literal["include", "exclude"]
ObjectClass = Literal["person", "vehicle", "animal", "motion", "other"]
CameraRole = Literal["high-resolution", "mid-resolution", "low-resolution", "snapshot"]
StreamingRole = Literal["high-resolution", "mid-resolution", "low-resolution"]
VideoStreamingMode = Literal["auto", "webrtc", "mse", "webrtc/tcp"]
CameraAspectRatio = Literal["16:9", "8:3", "4:3", "auto"]
DecoderFormat = Literal["yuv420p", "rgb24", "nv12"]
ImageInputFormat = Literal["yuv420p", "nv12", "rgb", "rgba", "gray"]
ImageOutputFormat = Literal["rgb", "rgba", "gray"]
CameraExtension = Literal[
    "cameraController", "hub", "motionDetection", "objectDetection", "audioDetection", "ptz"
]
CameraFrameWorkerDecoder = Literal["pillow", "wasm", "rust", "gpu"]
CameraFrameWorkerResolution = Literal[
    "640x480",
    "640x360",
    "320x240",
    "320x180",
]
AudioCodec = Literal[
    "PCMU", "PCMA", "MPEG4-GENERIC", "opus", "G722", "MPA", "PCM", "FLAC", "ELD", "PCML", "L16"
]
AudioFFmpegCodec = Literal[
    "pcm_mulaw", "pcm_alaw", "aac", "libopus", "g722", "mp3", "pcm_s16be", "pcm_s16le", "flac"
]
VideoCodec = Literal["H264", "H265", "VP8", "VP9", "AV1", "JPEG", "RAW"]
VideoFFmpegCodec = Literal["h264", "hevc", "vp8", "vp9", "av1", "mjpeg", "rawvideo"]
PythonVersion = Literal["3.9", "3.10", "3.11", "3.12"]
StateNames = Literal["light", "motion", "audio", "doorbell", "siren", "battery", "object"]
# See Camera
CameraPublicProperties = Literal[
    "_id",
    "nativeId",
    "pluginInfo",
    "name",
    "disabled",
    "isCloud",
    "hasLight",
    "hasSiren",
    "hasBinarySensor",
    "hasMotionDetection",
    "hasObjectDetection",
    "hasAudioDetection",
    "hasPtz",
    "hasBattery",
    "info",
    "type",
    "snapshotTTL",
    "detectionSettings",
    "frameWorkerSettings",
    "interface",
    "recording",
    "extensions",
    "sources",
    "detectionZones",
]
DeviceManagerEventType = Literal[
    "cameraSelected",
    "cameraDeselected",
]
JsonSchemaType = Literal["string", "number", "boolean", "array", "button", "submit"]
LoggerLevel = Literal["error", "warn", "info", "debug", "trace", "attention", "success"]
APIEventType = Literal["finishLaunching", "shutdown"]
PTZMovementType = Literal["absolute", "relative", "continuous", "home", "preset", "stop"]
RTSPAudioCodec = Literal["aac", "opus", "pcma"]
ProbeAudioCodec = Literal["aac", "opus", "pcma"]
HwAccelMethod = Literal[
    "auto", "cuda", "vaapi", "videotoolbox", "qsv", "rkmpp", "v4l2m2m", "opencl", "vulkan", "amf", "jetson"
]

# Basic types
Callback = Union[
    Callable[..., Any],
    Callable[..., Coroutine[Any, Any, Any]],
]

JSONValue = Union[str, int, float, bool, dict[str, Any], list[Any]]
JSONObject = dict[str, JSONValue]
JSONArray = list[JSONValue]
Path = Union[list[Union[int, str]], int, str]


# Interfaces as TypedDict
class CameraInformation(TypedDict, total=False):
    model: str
    manufacturer: str
    hardware: str
    serialNumber: str
    firmwareVersion: str
    supportUrl: str


Point = tuple[float, float]
BoundingBox = tuple[float, float, float, float]


class Detection(TypedDict):
    id: NotRequired[str]
    label: ObjectClass
    confidence: float
    boundingBox: BoundingBox
    inputWidth: int
    inputHeight: int
    origWidth: int
    origHeight: int


class DetectionZone(TypedDict):
    name: str
    points: list[Point]
    type: ZoneType
    filter: ZoneFilter
    classes: list[ObjectClass]
    isPrivacyMask: bool
    color: str


class MotionDetectionSettings(TypedDict):
    timeout: int


class ObjectDetectionSettings(TypedDict):
    confidence: float


class CameraDetectionSettings(TypedDict):
    motion: MotionDetectionSettings
    object: ObjectDetectionSettings


class CameraFrameWorkerSettings(TypedDict):
    decoder: CameraFrameWorkerDecoder
    fps: int
    resolution: CameraFrameWorkerResolution


class CameraInput(TypedDict):
    _id: str
    name: str
    role: CameraRole
    useForSnapshot: bool
    hotMode: bool
    preload: bool
    urls: "StreamUrls"


class RTPInfo(TypedDict):
    payload: Optional[int]
    codec: str
    rate: Optional[int]
    encoding: Optional[int]
    profile: Optional[str]
    level: Optional[int]


class FMTPInfo(TypedDict):
    payload: int
    config: str


class AudioCodecProperties(TypedDict):
    sampleRate: int
    channels: int
    payloadType: int
    fmtpInfo: Optional[FMTPInfo]


class VideoCodecProperties(TypedDict):
    clockRate: int
    payloadType: int
    fmtpInfo: Optional[FMTPInfo]


class AudioStreamInfo(TypedDict):
    codec: AudioCodec
    ffmpegCodec: AudioFFmpegCodec
    properties: AudioCodecProperties
    direction: Literal["sendonly", "recvonly", "sendrecv", "inactive"]


class VideoStreamInfo(TypedDict):
    codec: VideoCodec
    ffmpegCodec: VideoFFmpegCodec
    properties: VideoCodecProperties
    direction: Literal["sendonly", "recvonly", "sendrecv", "inactive"]


class ProbeConfig(TypedDict, total=False):
    video: bool
    audio: Union[bool, Literal["all"], list[ProbeAudioCodec]]
    microphone: bool


class ProbeStream(TypedDict):
    sdp: str
    audio: list[AudioStreamInfo]
    video: list[VideoStreamInfo]


class StreamUrls(TypedDict):
    ws: "Go2RtcWSSource"
    rtsp: "Go2RtcRTSPSource"
    snapshot: "Go2RtcSnapshotSource"


class Go2RtcWSSource(TypedDict):
    webrtc: str
    mse: str


class Go2RtcRTSPSource(TypedDict):
    base: str
    default: str
    muted: str
    aac: str
    opus: str
    pcma: str
    onvif: str


class Go2RtcSnapshotSource(TypedDict):
    mp4: str
    jpeg: str
    mjpeg: str


T = TypeVar(
    "T",
    bound=Union[
        "LightStateWithoutLastEvent",
        "AudioStateWithoutLastEvent",
        "MotionStateWithoutLastEvent",
        "ObjectStateWithoutLastEvent",
        "SirenStateWithoutLastEvent",
        "BatteryStateWithoutLastEvent",
        "DoorbellStateWithoutLastEvent",
    ],
)


class BaseState(TypedDict, Generic[T]):
    timestamp: int
    lastEvent: NotRequired[Optional[T]]


class BaseStateWithoutLastEvent(TypedDict):
    timestamp: int


class MotionSetEvent(TypedDict):
    state: bool
    detections: NotRequired[Optional[list[Detection]]]


class AudioSetEvent(TypedDict):
    state: bool
    db: NotRequired[Optional[float]]


class ObjectSetEvent(TypedDict):
    detections: list[Detection]


class LightSetEvent(TypedDict):
    state: bool


class DoorbellSetEvent(TypedDict):
    state: bool


class SirenSetEvent(TypedDict):
    state: bool
    level: NotRequired[Optional[int]]


class BatterySetEvent(TypedDict):
    level: int
    lowBattery: NotRequired[Optional[bool]]
    charging: NotRequired[Optional[bool]]


class LightState(BaseState["LightStateWithoutLastEvent"], LightSetEvent):
    pass


class LightStateWithoutLastEvent(BaseStateWithoutLastEvent, LightSetEvent):
    pass


class MotionState(BaseState["MotionStateWithoutLastEvent"], MotionSetEvent):
    pass


class MotionStateWithoutLastEvent(BaseStateWithoutLastEvent, MotionSetEvent):
    pass


class AudioState(BaseState["AudioStateWithoutLastEvent"], AudioSetEvent):
    pass


class AudioStateWithoutLastEvent(BaseStateWithoutLastEvent, AudioSetEvent):
    pass


class DoorbellState(BaseState["DoorbellStateWithoutLastEvent"], DoorbellSetEvent):
    pass


class DoorbellStateWithoutLastEvent(BaseStateWithoutLastEvent, DoorbellSetEvent):
    pass


class SirenState(BaseState["SirenStateWithoutLastEvent"], SirenSetEvent):
    pass


class SirenStateWithoutLastEvent(BaseStateWithoutLastEvent, SirenSetEvent):
    pass


class ObjectState(BaseState["ObjectStateWithoutLastEvent"], ObjectSetEvent):
    pass


class ObjectStateWithoutLastEvent(BaseStateWithoutLastEvent, ObjectSetEvent):
    pass


class BatteryState(BaseState["BatteryStateWithoutLastEvent"], BatterySetEvent):
    pass


class BatteryStateWithoutLastEvent(BaseStateWithoutLastEvent, BatterySetEvent):
    pass


class StateValues(TypedDict):
    light: LightState
    motion: MotionState
    audio: AudioState
    object: ObjectState
    doorbell: DoorbellState
    siren: SirenState
    battery: BatteryState


class SetValues(TypedDict):
    light: LightSetEvent
    motion: MotionSetEvent
    audio: AudioSetEvent
    object: ObjectSetEvent
    doorbell: DoorbellSetEvent
    siren: SirenSetEvent
    battery: BatterySetEvent


class FrameData(TypedDict):
    data: bytes
    timestamp: int
    metadata: "FrameMetadata"
    info: "ImageInformation"


class FrameMetadata(TypedDict):
    format: DecoderFormat
    frameSize: Union[float, int]
    width: int
    origWidth: int
    height: int
    origHeight: int


class ImageInformation(TypedDict):
    width: int
    height: int
    channels: float
    format: ImageInputFormat


class ImageCrop(TypedDict):
    top: int
    left: int
    width: int
    height: int


class ImageResize(TypedDict):
    width: int
    height: int


class ImageFormat(TypedDict):
    to: ImageOutputFormat


class ImageOptions(TypedDict, total=False):
    format: ImageFormat
    crop: ImageCrop
    resize: ImageResize


class FrameImage(TypedDict):
    image: Image.Image
    info: ImageInformation


class FrameBuffer(TypedDict):
    image: bytes
    info: ImageInformation


class MotionDetectionFrame(TypedDict):
    frame: FrameData
    state: MotionSetEvent


class VideoFrame(Protocol):
    @property
    def data(self) -> bytes: ...
    @property
    def metadata(self) -> FrameMetadata: ...
    @property
    def info(self) -> ImageInformation: ...
    @property
    def timestamp(self) -> int: ...
    @property
    def motion(self) -> Optional[MotionSetEvent]: ...
    @property
    def input_width(self) -> int: ...
    @property
    def input_height(self) -> int: ...
    @property
    def input_format(self) -> DecoderFormat: ...

    async def to_buffer(self, options: Optional[ImageOptions] = None) -> FrameBuffer: ...
    async def to_image(self, options: Optional[ImageOptions] = None) -> FrameImage: ...
    async def save(self, path: str, options: Optional[ImageOptions] = None) -> None: ...


class CameraInputSettings(TypedDict):
    _id: str
    name: str
    role: CameraRole
    useForSnapshot: bool
    hotMode: bool
    preload: bool
    urls: list[str]


class CameraConfigInputSettings(TypedDict):
    name: str
    role: CameraRole
    useForSnapshot: bool
    hotMode: bool
    preload: bool


class BaseCameraConfig(TypedDict):
    name: str
    nativeId: Optional[str]
    isCloud: Optional[bool]
    disabled: Optional[bool]
    info: Optional[CameraInformation]


class CameraConfig(BaseCameraConfig):
    sources: list[CameraConfigInputSettings]


class PartialCameraConfig(BaseCameraConfig, total=False):
    sources: NotRequired[list[CameraConfigInputSettings]]


class RTSPUrlOptions(TypedDict, total=False):
    video: bool
    audio: Union[bool, RTSPAudioCodec, list[RTSPAudioCodec]]
    audioSingleTrack: bool
    backchannel: bool
    timeout: int


class CameraSource(Protocol):
    # from CameraInput
    id: str  # _id
    name: str
    role: CameraRole
    useForSnapshot: bool
    hotMode: bool
    preload: bool
    urls: StreamUrls
    # end CameraInput

    async def snapshot(self, force_new: Optional[bool] = None) -> Optional[bytes]: ...

    async def probe_stream(
        self, probe_config: Optional[ProbeConfig] = None, refresh: Optional[bool] = None
    ) -> Optional[ProbeStream]: ...


class CameraDeviceSource(CameraSource, Protocol):
    def generate_rtsp_url(self, options: RTSPUrlOptions) -> str: ...
    def create_webrtc_session(self, options: "WebRTCConnectionOptions") -> None: ...
    def create_rtsp_session(self, options: "RTSPConnectionOptions") -> None: ...
    def create_fmp4_session(self, options: "FMP4ConnectionOptions") -> None: ...


class WebRTCConnectionOptions(TypedDict, total=False):
    iceServers: list["IceServer"]


class RTSPConnectionOptions(TypedDict, total=False):
    url: str


class FMP4ConnectionOptions(TypedDict, total=False):
    url: str


SpawnInput = Union[str, int]


class FfmpegOptions(TypedDict):
    ffmpegPath: str
    input: Optional[list[SpawnInput]]
    video: Optional[list[SpawnInput]]
    audio: Optional[list[SpawnInput]]
    output: list[SpawnInput]
    logger: Optional[dict[str, Any]]


class ReturnAudioFFmpegOptions(TypedDict):
    ffmpegPath: str
    input: list[SpawnInput]
    logPrefix: Optional[str]


class CameraUiSettings(TypedDict):
    streamingMode: VideoStreamingMode
    streamingSource: Union[StreamingRole, Literal["auto"]]
    aspectRatio: CameraAspectRatio


class CameraRecordingSettings(TypedDict):
    enabled: bool


class Extension(TypedDict):
    id: str
    name: str


class CameraExtensions(TypedDict):
    hub: NotRequired[list[Extension]]
    cameraController: NotRequired[Extension]
    motionDetection: NotRequired[Extension]
    audioDetection: NotRequired[Extension]
    objectDetection: NotRequired[Extension]
    ptz: NotRequired[Extension]
    plugins: list[Extension]


class CameraPluginInfo(TypedDict):
    id: str
    name: str


class Camera(TypedDict):
    _id: str
    nativeId: Optional[str]
    pluginInfo: Optional[CameraPluginInfo]
    name: str
    disabled: bool
    isCloud: bool
    info: CameraInformation
    type: CameraType
    snapshotTTL: int
    detectionZones: list[DetectionZone]
    detectionSettings: CameraDetectionSettings
    frameWorkerSettings: CameraFrameWorkerSettings
    interface: CameraUiSettings
    recording: CameraRecordingSettings
    extensions: CameraExtensions
    sources: list[CameraInput]


class CameraDeviceCapability(str, Enum):
    MotionSensor = "MotionSensor"
    MotionDetector = "MotionDetector"

    AudioSensor = "AudioSensor"

    ObjectSensor = "ObjectSensor"
    ObjectDetector = "ObjectDetector"

    Light = "Light"
    Siren = "Siren"
    Doorbell = "Doorbell"

    Battery = "Battery"

    PTZ = "PTZ"
    PTZZoom = "PTZZoom"
    PTZHome = "PTZHome"
    PTZPresets = "PTZPresets"

    Snapshot = "Snapshot"
    StreamUrl = "StreamUrl"

    Reboot = "Reboot"


class PTZSpeed(TypedDict):
    pan: NotRequired[float]
    tilt: NotRequired[float]
    zoom: NotRequired[float]


class PTZBaseCommand(TypedDict):
    speed: NotRequired[PTZSpeed]


class PTZStopCommand(PTZBaseCommand):
    type: Literal["stop"]


class PTZHomeCommand(PTZBaseCommand):
    type: Literal["home"]


class PTZPresetCommand(PTZBaseCommand):
    type: Literal["preset"]
    preset: str


class PTZMoveCommand(PTZBaseCommand):
    type: Literal["absolute", "relative"]
    pan: NotRequired[float]
    tilt: NotRequired[float]
    zoom: NotRequired[float]


class PTZContinuousMoveCommand(PTZBaseCommand):
    type: Literal["continuous"]
    pan: NotRequired[float]
    tilt: NotRequired[float]
    zoom: NotRequired[float]
    timeout: NotRequired[float]


PTZCommand = Union[PTZHomeCommand, PTZPresetCommand, PTZMoveCommand, PTZContinuousMoveCommand]


class PTZInterface(Protocol):
    async def ptzCommand(self, command: PTZCommand) -> None: ...


class SnapshotInterface(Protocol):
    async def snapshot(self, source_id: str, force_new: Optional[bool] = None) -> Optional[bytes]: ...


class StreamingInterface(Protocol):
    async def streamUrl(self, source_name: str) -> str: ...


StateValue = Union[
    LightState,
    MotionState,
    AudioState,
    DoorbellState,
    SirenState,
    ObjectState,
    BatteryState,
]

SV = TypeVar("SV", bound=StateValue)


class CameraStateChangedObject(Generic[SV], TypedDict):
    old_state: SV
    new_state: SV


class CameraPropertyObservableObject(TypedDict):
    property: str
    old_state: Any
    new_state: Any


class CameraCapabilitiesObservableObject(TypedDict):
    old_capabilities: list[CameraDeviceCapability]
    new_capabilities: list[CameraDeviceCapability]


class CameraConfigInputSettingsPartial(TypedDict, total=False):
    # _id: str
    name: str
    role: CameraRole
    useForSnapshot: bool
    hotMode: bool
    preload: bool
    urls: list[str]


@runtime_checkable
class CameraDevice(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def native_id(self) -> Optional[str]: ...
    @property
    def plugin_info(self) -> Optional[CameraPluginInfo]: ...
    @property
    def connected(self) -> bool: ...
    @property
    def frameworker_connected(self) -> bool: ...
    @property
    def disabled(self) -> bool: ...
    @property
    def name(self) -> str: ...
    @property
    def type(self) -> CameraType: ...
    @property
    def snapshot_ttl(self) -> int: ...
    @property
    def info(self) -> CameraInformation: ...
    @property
    def is_cloud(self) -> bool: ...
    @property
    def has_light(self) -> bool: ...
    @property
    def has_siren(self) -> bool: ...
    @property
    def has_doorbell(self) -> bool: ...
    @property
    def has_battery(self) -> bool: ...
    @property
    def has_motion_detector(self) -> bool: ...
    @property
    def has_audio_detector(self) -> bool: ...
    @property
    def has_object_detector(self) -> bool: ...
    @property
    def has_ptz(self) -> bool: ...
    @property
    def detection_zones(self) -> list[DetectionZone]: ...
    @property
    def detection_settings(self) -> CameraDetectionSettings: ...
    @property
    def frameworker_settings(self) -> CameraFrameWorkerSettings: ...

    @property
    def sources(self) -> list[CameraDeviceSource]: ...
    @property
    def stream_source(self) -> CameraDeviceSource: ...
    @property
    def high_resolution_source(self) -> Optional[CameraDeviceSource]: ...
    @property
    def mid_resolution_source(self) -> Optional[CameraDeviceSource]: ...
    @property
    def low_resolution_source(self) -> Optional[CameraDeviceSource]: ...
    @property
    def snapshot_source(self) -> Optional[CameraSource]: ...

    on_connected: HybridObservable[bool]
    on_frameworker_connected: HybridObservable[bool]

    on_light_switched: HybridObservable[LightState]
    on_motion_detected: HybridObservable[MotionState]
    on_audio_detected: HybridObservable[AudioState]
    on_object_detected: HybridObservable[ObjectState]
    on_doorbell_pressed: HybridObservable[DoorbellState]
    on_siren_detected: HybridObservable[SirenState]
    on_battery_changed: HybridObservable[BatteryState]

    logger: "LoggerService"

    @overload
    def on_state_change(
        self, state_name: Literal["light"]
    ) -> HybridObservable[CameraStateChangedObject[LightState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["motion"]
    ) -> HybridObservable[CameraStateChangedObject[MotionState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["audio"]
    ) -> HybridObservable[CameraStateChangedObject[AudioState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["doorbell"]
    ) -> HybridObservable[CameraStateChangedObject[DoorbellState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["siren"]
    ) -> HybridObservable[CameraStateChangedObject[SirenState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["battery"]
    ) -> HybridObservable[CameraStateChangedObject[BatteryState]]: ...
    @overload
    def on_state_change(
        self, state_name: Literal["object"]
    ) -> HybridObservable[CameraStateChangedObject[ObjectState]]: ...
    def on_state_change(self, state_name: Any) -> Any: ...

    def on_property_change(
        self, property: Union[CameraPublicProperties, list[CameraPublicProperties]]
    ) -> HybridObservable[CameraPropertyObservableObject]: ...

    def on_capabilities_change(self) -> HybridObservable[CameraCapabilitiesObservableObject]: ...

    @overload
    def get_value(self, state_name: Literal["light"]) -> LightState: ...
    @overload
    def get_value(self, state_name: Literal["motion"]) -> MotionState: ...
    @overload
    def get_value(self, state_name: Literal["audio"]) -> AudioState: ...
    @overload
    def get_value(self, state_name: Literal["object"]) -> ObjectState: ...
    @overload
    def get_value(self, state_name: Literal["doorbell"]) -> DoorbellState: ...
    @overload
    def get_value(self, state_name: Literal["siren"]) -> SirenState: ...
    @overload
    def get_value(self, state_name: Literal["battery"]) -> BatteryState: ...
    def get_value(
        self, state_name: Literal["light", "motion", "audio", "object", "doorbell", "siren", "battery"]
    ) -> Union[
        LightState,
        MotionState,
        AudioState,
        ObjectState,
        DoorbellState,
        SirenState,
        BatteryState,
    ]: ...

    def extend(self, interfaces: Union[PTZInterface, SnapshotInterface, StreamingInterface]) -> None: ...

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...

    @overload
    def get_frames(
        self, frame_type: Literal["video"], options: Optional[ImageOptions] = None
    ) -> AsyncGenerator[VideoFrame, None]: ...
    @overload
    def get_frames(
        self, frame_type: Literal["motion"], options: Optional[ImageOptions] = None
    ) -> AsyncGenerator[VideoFrame, None]: ...

    @overload
    async def update_state(
        self,
        state_name: Literal["light"],
        event_data: LightSetEvent,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["motion"],
        event_data: MotionSetEvent,
        frame: Optional[VideoFrame] = None,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["audio"],
        event_data: AudioSetEvent,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["object"],
        event_data: ObjectSetEvent,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["doorbell"],
        event_data: DoorbellSetEvent,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["siren"],
        event_data: SirenSetEvent,
    ) -> None: ...
    @overload
    async def update_state(
        self,
        state_name: Literal["battery"],
        event_data: BatterySetEvent,
    ) -> None: ...

    def get_capabilities(self) -> list[CameraDeviceCapability]: ...
    def has_capability(self, capability: CameraDeviceCapability) -> bool: ...
    def add_capabilities(self, capabilities: list[CameraDeviceCapability]) -> None: ...
    def remove_capabilities(self, capabilities: list[CameraDeviceCapability]) -> None: ...


CameraSelectedCallback = Union[
    Callable[[CameraDevice, CameraExtension], None],
    Callable[[CameraDevice, CameraExtension], Coroutine[None, None, None]],
]
CameraDeselectedCallback = Union[
    Callable[[str, CameraExtension], None],
    Callable[[str, CameraExtension], Coroutine[None, None, None]],
]


@runtime_checkable
class DeviceManager(Protocol):
    async def create_camera(self, camera_config: CameraConfig) -> CameraDevice: ...
    async def update_camera(
        self, camera_id_or_name: str, camera_config: PartialCameraConfig
    ) -> CameraDevice: ...
    async def get_camera(self, camera_id_or_name: str) -> Optional[CameraDevice]: ...
    async def remove_camera(self, camera_id_or_name: str) -> None: ...

    @overload
    def on(self, event: Literal["cameraSelected"], f: CameraSelectedCallback) -> Any: ...
    @overload
    def on(self, event: Literal["cameraDeselected"], f: CameraDeselectedCallback) -> Any: ...

    @overload
    def once(self, event: Literal["cameraSelected"], f: CameraSelectedCallback) -> Any: ...
    @overload
    def once(self, event: Literal["cameraDeselected"], f: CameraDeselectedCallback) -> Any: ...

    @overload
    def remove_listener(self, event: Literal["cameraSelected"], f: CameraSelectedCallback) -> None: ...
    @overload
    def remove_listener(self, event: Literal["cameraDeselected"], f: CameraDeselectedCallback) -> None: ...

    def remove_all_listeners(self, event: Optional[DeviceManagerEventType] = None) -> None: ...


@runtime_checkable
class CoreManager(Protocol):
    async def connect_to_plugin(self, plugin_name: str) -> "Optional[CuiPlugin]": ...
    async def get_ffmpeg_path(self) -> str: ...
    async def get_hwaccel_info(self, options: "HWAccelOptions") -> "list[FfmpegArgs]": ...
    async def get_server_addresses(self) -> list[str]: ...
    async def get_ice_servers(self) -> list["IceServer"]: ...


class HWAccelScale(TypedDict):
    width: int
    height: int


class HWAccelOptions(TypedDict):
    targetCodec: Union[Literal["h264"], Literal["h265"]]
    keepOnHardware: NotRequired[Optional[bool]]
    pixelFormat: NotRequired[Optional[str]]
    scale: NotRequired[Optional[HWAccelScale]]


class FfmpegArgs(TypedDict):
    codec: str
    hwaccel: HwAccelMethod
    hwaccelArgs: list[str]
    hwaccelFilters: list[str]
    hwDeviceArgs: list[str]
    supported: bool


class IceServer(TypedDict):
    urls: list[str]
    username: Optional[str]
    credential: Optional[str]


# Schema related types and interfaces
PluginConfig = dict[str, Any]

J = TypeVar("J", bound=Union[str, list[str], float, list[float], bool, list[bool], Any])


class JsonFactorySchema(TypedDict):
    key: str
    title: str
    description: str
    group: NotRequired[str]


class JsonBaseSchmaWithoutCallbacks(JsonFactorySchema, Generic[J]):
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[J]


class JsonBaseSchema(JsonBaseSchmaWithoutCallbacks[J], Generic[J]):
    store: NotRequired[bool]
    onSet: NotRequired[
        Union[
            Callable[[Any, Any], None | Any],
            Callable[[Any, Any], Awaitable[None | Any]],
            Callable[[Any, Any], Coroutine[Any, Any, None | Any]],
        ]
    ]
    onGet: NotRequired[
        Union[
            Callable[..., Union[Any, None]],
            Callable[..., Awaitable[Union[Any, None]]],
            Callable[..., Coroutine[Any, Any, Union[Any, None]]],
        ]
    ]


class JsonStringSchema(TypedDict):
    type: Literal["string"]
    format: NotRequired[
        Literal["date-time", "date", "time", "email", "uuid", "ipv4", "ipv6", "password", "qrCode", "image"]
    ]
    minLength: NotRequired[int]
    maxLength: NotRequired[int]


class JsonNumberSchema(TypedDict):
    type: Literal["number"]
    minimum: NotRequired[int]
    maximum: NotRequired[int]
    step: NotRequired[float]


class JsonBooleanSchema(TypedDict):
    type: Literal["boolean"]


class JsonEnumSchema(TypedDict):
    type: Literal["string"]
    enum: list[str]
    multiple: NotRequired[bool]


class JsonArraySchema(TypedDict):
    type: Literal["array"]
    opened: NotRequired[bool]
    items: "JsonSchemaWithoutCallbacksAndKey"


class JsonSchemaString(JsonBaseSchema[str], JsonStringSchema):
    pass


class JsonSchemaStringWithoutCallbacks(JsonBaseSchmaWithoutCallbacks[str], JsonStringSchema):
    pass


class JsonSchemaNumber(JsonBaseSchema[float], JsonNumberSchema):
    pass


class JsonSchemaNumberWithoutCallbacks(JsonBaseSchmaWithoutCallbacks[float], JsonNumberSchema):
    pass


class JsonSchemaBoolean(JsonBaseSchema[bool], JsonBooleanSchema):
    pass


class JsonSchemaBooleanWithoutCallbacks(JsonBaseSchmaWithoutCallbacks[bool], JsonBooleanSchema):
    pass


class JsonSchemaEnum(JsonBaseSchema[Union[str, list[str]]], JsonEnumSchema):
    pass


class JsonSchemaEnumWithoutCallbacks(JsonBaseSchmaWithoutCallbacks[Union[str, list[str]]], JsonEnumSchema):
    pass


class JsonSchemaArray(JsonBaseSchema[Union[list[str], list[float], list[bool]]], JsonArraySchema):
    pass


class JsonSchemaArrayWithoutCallbacks(
    JsonBaseSchmaWithoutCallbacks[Union[list[str], list[float], list[bool]]], JsonArraySchema
):
    pass


class JsonSchemaButton(JsonFactorySchema):
    type: Literal["button"]
    color: NotRequired[Literal["success", "info", "warn", "danger"]]
    onSet: Union[
        Callable[[Any, Any], None | Any],
        Callable[[Any, Any], Awaitable[None | Any]],
        Callable[[Any, Any], Coroutine[Any, Any, None | Any]],
    ]


class JsonSchemaSubmit(JsonFactorySchema):
    type: Literal["submit"]
    color: NotRequired[Literal["success", "info", "warn", "danger"]]
    onClick: Union[
        Callable[[Any], "Optional[FormSubmitResponse]"],
        Callable[[Any], Awaitable["Optional[FormSubmitResponse]"]],
        Callable[[Any], Coroutine[Any, Any, "Optional[FormSubmitResponse]"]],
    ]


class JsonSchemaStringWithoutCallbacksAndKey(TypedDict):
    type: Literal["string"]
    title: str
    description: str
    group: NotRequired[str]
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[str]
    format: NotRequired[
        Literal["date-time", "date", "time", "email", "uuid", "ipv4", "ipv6", "password", "qrCode", "image"]
    ]
    minLength: NotRequired[int]
    maxLength: NotRequired[int]


class JsonSchemaNumberWithoutCallbacksAndKey(TypedDict):
    type: Literal["number"]
    title: str
    description: str
    group: NotRequired[str]
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[float]
    minimum: NotRequired[int]
    maximum: NotRequired[int]
    step: NotRequired[float]


class JsonSchemaBooleanWithoutCallbacksAndKey(TypedDict):
    type: Literal["boolean"]
    title: str
    description: str
    group: NotRequired[str]
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[bool]


class JsonSchemaEnumWithoutCallbacksAndKey(TypedDict):
    type: Literal["string"]
    title: str
    description: str
    group: NotRequired[str]
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[Union[str, list[str]]]
    enum: list[str]
    multiple: NotRequired[bool]


class JsonSchemaArrayWithoutCallbacksAndKey(TypedDict):
    type: Literal["array"]
    title: str
    description: str
    group: NotRequired[str]
    hidden: NotRequired[bool]
    required: NotRequired[bool]
    readonly: NotRequired[bool]
    placeholder: NotRequired[str]
    defaultValue: NotRequired[Union[list[str], list[float], list[bool]]]
    opened: NotRequired[bool]
    items: "JsonSchemaWithoutCallbacksAndKey"


JsonSchema = Union[
    JsonSchemaString,
    JsonSchemaNumber,
    JsonSchemaBoolean,
    JsonSchemaEnum,
    JsonSchemaArray,
    JsonSchemaButton,
    JsonSchemaSubmit,
]

JsonSchemaWithoutCallbacks = Union[
    JsonSchemaStringWithoutCallbacks,
    JsonSchemaNumberWithoutCallbacks,
    JsonSchemaBooleanWithoutCallbacks,
    JsonSchemaEnumWithoutCallbacks,
    JsonSchemaArrayWithoutCallbacks,
]

JsonSchemaWithoutCallbacksAndKey = Union[
    JsonSchemaStringWithoutCallbacksAndKey,
    JsonSchemaNumberWithoutCallbacksAndKey,
    JsonSchemaBooleanWithoutCallbacksAndKey,
    JsonSchemaEnumWithoutCallbacksAndKey,
    JsonSchemaArrayWithoutCallbacksAndKey,
]


class ToastMessage(TypedDict):
    type: Literal["info", "success", "warning", "error"]
    message: str


class FormSubmitSchema(TypedDict):
    config: dict[str, Any]


class FormSubmitResponse(TypedDict, total=False):
    toast: NotRequired[ToastMessage]
    schema: NotRequired[list[JsonSchemaWithoutCallbacks]]


class SchemaConfig(TypedDict):
    schema: list[JsonSchema]
    config: dict[str, Any]


# Plugin related interfaces
class ImageMetadata(TypedDict):
    width: int
    height: int


class AudioMetadata(TypedDict):
    mimeType: Literal["audio/mpeg", "audio/wav", "audio/ogg"]


class MotionDetectionPluginResponse(TypedDict):
    videoData: bytes


class ObjectDetectionPluginResponse(TypedDict):
    detections: list[Detection]


class AudioDetectionPluginResponse(TypedDict):
    detected: bool


class CuiPluginCapability(str, Enum):
    MotionDetector = "MotionDetector"
    ObjectDetector = "ObjectDetector"
    AudioDetector = "AudioDetector"


class CuiPlugin(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, logger: "LoggerService", api: "PluginAPI") -> None: ...
    @abstractmethod
    async def configureCameras(self, cameras: list[CameraDevice]) -> None: ...
    @abstractmethod
    async def getCapabilities(self) -> list[CuiPluginCapability]: ...

    async def interfaceSchema(self) -> Optional[list[JsonSchema]]:
        return None

    async def detectAudio(
        self, audio_data: bytes, metadata: AudioMetadata, config: dict[str, Any]
    ) -> Optional[AudioDetectionPluginResponse]:
        return None

    async def detectMotion(
        self, video_data: bytes, config: dict[str, Any]
    ) -> Optional[MotionDetectionPluginResponse]:
        return None

    async def detectObjects(
        self, image_data: bytes, metadata: ImageMetadata, config: dict[str, Any]
    ) -> Optional[ObjectDetectionPluginResponse]:
        return None


@runtime_checkable
class LoggerService(Protocol):
    def log(self, *args: Any) -> None: ...
    def error(self, *args: Any) -> None: ...
    def warn(self, *args: Any) -> None: ...
    def debug(self, *args: Any) -> None: ...
    def trace(self, *args: Any) -> None: ...
    def attention(self, *args: Any) -> None: ...
    def success(self, *args: Any) -> None: ...


PA = TypeVar("PA", bound="DeviceStorage[Any]", default="DeviceStorage[Any]")


@runtime_checkable
class PluginAPI(Protocol):
    core_manager: CoreManager
    device_manager: DeviceManager
    storage_controller: "StorageController"
    storage_path: str

    def on(self, event: APIEventType, f: Callback) -> Any: ...
    def once(self, event: APIEventType, f: Callback) -> Any: ...
    def remove_listener(self, event: APIEventType, f: Callback) -> None: ...
    def remove_all_listeners(self, event: Optional[APIEventType] = None) -> None: ...


V1 = TypeVar("V1", default=str)
V2 = TypeVar("V2", default=dict[str, Any])


@runtime_checkable
class DeviceStorage(Protocol, Generic[V2]):
    values: V2
    schemas: list[JsonSchema]

    @overload
    async def getValue(self, key: str) -> Union[V1, None]: ...
    @overload
    async def getValue(self, key: str, default_value: V1) -> V1: ...
    async def getValue(self, key: str, default_value: Optional[V1] = None) -> Union[V1, None]: ...
    async def setValue(self, path: str, new_value: Any) -> None: ...
    async def submitValue(self, key: str, new_value: Any) -> Union[FormSubmitResponse, None]: ...
    def hasValue(self, key: str) -> bool: ...
    async def getConfig(self) -> SchemaConfig: ...
    async def setConfig(self, new_config: V2) -> None: ...
    async def addSchema(self, schema: JsonSchema) -> None: ...
    def removeSchema(self, key: str) -> None: ...
    async def changeSchema(self, key: str, new_schema: dict[str, Any]) -> None: ...
    def getSchema(self, key: str) -> Optional[JsonSchema]: ...
    def hasSchema(self, key: str) -> bool: ...
    def save(self) -> None: ...


S = TypeVar("S", default=DeviceStorage[Any], covariant=True)


@runtime_checkable
class StorageController(Protocol[S]):
    def create_camera_storage(
        self,
        instance: Any,
        camera_id: str,
        schemas: Optional[list[JsonSchema]] = None,
    ) -> S: ...
    def create_plugin_storage(
        self,
        instance: Any,
        schemas: Optional[list[JsonSchema]] = None,
    ) -> S: ...
    def get_camera_storage(self, camera_id: str) -> Optional[S]: ...
    def get_plugin_storage(self) -> Optional[S]: ...
