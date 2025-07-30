"""
libssp: Python binding for the SSP (Streaming Signal Protocol) C++ client.
Provides a high-level wrapper (`SspClient`) and constants for
stream control, encoder types, and error codes.
"""

from . import _libssp
from .sspclient import (
    SspClient,
    STREAM_DEFAULT,
    STREAM_MAIN,
    STREAM_SEC,
    VIDEO_ENCODER_UNKNOWN,
    VIDEO_ENCODER_H264,
    VIDEO_ENCODER_H265,
    AUDIO_ENCODER_UNKNOWN,
    AUDIO_ENCODER_AAC,
    AUDIO_ENCODER_PCM,
    ERROR_SSP_PROTOCOL_VERSION_GT_SERVER,
    ERROR_SSP_PROTOCOL_VERSION_LT_SERVER,
    ERROR_SSP_CONNECTION_FAILED,
    ERROR_SSP_CONNECTION_EXIST,
    SSP_CAPABILITY_IGNORE_HEARTBEAT_DISABLE_ENC,
)

__all__ = [
    "SspClient",
    "STREAM_DEFAULT",
    "STREAM_MAIN",
    "STREAM_SEC",
    "VIDEO_ENCODER_UNKNOWN",
    "VIDEO_ENCODER_H264",
    "VIDEO_ENCODER_H265",
    "AUDIO_ENCODER_UNKNOWN",
    "AUDIO_ENCODER_AAC",
    "AUDIO_ENCODER_PCM",
    "ERROR_SSP_PROTOCOL_VERSION_GT_SERVER",
    "ERROR_SSP_PROTOCOL_VERSION_LT_SERVER",
    "ERROR_SSP_CONNECTION_FAILED",
    "ERROR_SSP_CONNECTION_EXIST",
    SSP_CAPABILITY_IGNORE_HEARTBEAT_DISABLE_ENC,
]