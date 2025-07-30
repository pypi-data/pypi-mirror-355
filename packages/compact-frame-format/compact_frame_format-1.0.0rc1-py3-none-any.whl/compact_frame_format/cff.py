"""
Compact Frame Format (CFF) Protocol Implementation

This module implements a minimal, length-delimited frame format that is DMA- and hardware CRC-friendly.

The protocol format:
- Preamble: 0xFA, 0xCE
- Frame Counter: 2 bytes (little endian, increments with each frame)
- Payload Size: 2 bytes (length of payload only, little endian)
- Header CRC: 2 bytes (CRC-16/CCITT-FALSE of preamble + frame counter + payload size, little endian)
- Payload: variable length
- Payload CRC: 2 bytes (CRC-16/CCITT-FALSE of payload, little endian)
"""

import struct
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Iterator

# Protocol constants
PREAMBLE = b'\xFA\xCE'
PREAMBLE_SIZE = 2
FRAME_COUNTER_SIZE = 2
PAYLOAD_SIZE_BYTES = 2
HEADER_CRC_SIZE = 2
PAYLOAD_CRC_SIZE = 2
HEADER_SIZE = PREAMBLE_SIZE + FRAME_COUNTER_SIZE + PAYLOAD_SIZE_BYTES + HEADER_CRC_SIZE
MAX_FRAME_COUNT = 65535

# Struct format strings for packing/unpacking
_HEADER_FORMAT = '<2sHH'  # preamble (2 bytes), frame_counter (H), payload_size (H)
_CRC_FORMAT = '<H'  # CRC value (H)
_HEADER_UNPACK_SIZE = struct.calcsize(_HEADER_FORMAT)
_CRC_UNPACK_SIZE = struct.calcsize(_CRC_FORMAT)

# CRC-16/CCITT-FALSE lookup table (pre-computed for performance)
_CRC_TABLE = tuple([
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
])


@dataclass(frozen=True)
class CFrame:
    """Represents a parsed frame with payload and counter."""
    frame_counter: int
    payload: bytes
    
    @property
    def frame_length(self) -> int:
        """Calculate the total frame length for this frame."""
        return HEADER_SIZE + len(self.payload) + PAYLOAD_CRC_SIZE


class ParseResultEnum(Enum):
    """Enumeration of possible parse results."""
    SUCCESS = "success"
    FRAME_TOO_SHORT = "frame_too_short"
    INVALID_PREAMBLE = "invalid_preamble"
    INCOMPLETE_FRAME = "incomplete_frame"
    HEADER_CRC_MISMATCH = "header_crc_mismatch"
    PAYLOAD_CRC_MISMATCH = "payload_crc_mismatch"
    STRUCT_ERROR = "struct_error"
    UNEXPECTED_ERROR = "unexpected_error"


class FrameError(Exception):
    """Base exception for frame-related errors."""
    pass


class Frame:
    """
    Compact Frame Format handler with automatic frame counter management.
    
    This class provides methods to create and parse frames with an internal
    frame counter that automatically increments.
    """
    
    def __init__(self, initial_frame_count: int = 0) -> None:
        """
        Initialize Frame handler with optional initial frame count.
        
        Args:
            initial_frame_count: Starting value for frame counter (0-MAX_FRAME_COUNT), defaults to 0
            
        Raises:
            FrameError: If initial_frame_count is out of range
        """
        if not (0 <= initial_frame_count <= MAX_FRAME_COUNT):
            raise FrameError(f"Initial frame count must be between 0 and {MAX_FRAME_COUNT}, got {initial_frame_count}")
        self._counter = initial_frame_count
    
    @property
    def current_counter(self) -> int:
        """Current frame counter value."""
        return self._counter
    
    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """
        Calculate CRC-16/CCITT-FALSE for given data.
        
        Args:
            data: Input bytes to calculate CRC for
            
        Returns:
            CRC-16 value as integer
        """
        crc = 0xFFFF
        for byte in data:
            tbl_idx = ((crc >> 8) ^ byte) & 0xFF
            crc = ((crc << 8) ^ _CRC_TABLE[tbl_idx]) & 0xFFFF
        return crc
    
    @staticmethod
    def frame_length(payload_length: int) -> int:
        """
        Calculate the frame length for a given payload length.
        
        Args:
            payload_length: Length of the payload in bytes
            
        Returns:
            Frame length in bytes
        """
        return HEADER_SIZE + payload_length + PAYLOAD_CRC_SIZE
    
    def create(self, payload: bytes, frame_counter: Optional[int] = None) -> bytes:
        """
        Create a frame with the given payload.
        
        Args:
            payload: Payload data as bytes
            frame_counter: Optional frame counter value (0-MAX_FRAME_COUNT). If None, uses internal counter
            
        Returns:
            Complete frame as bytes
            
        Raises:
            FrameError: If frame_counter is out of range
        """
        # Determine frame counter
        if frame_counter is not None:
            if not (0 <= frame_counter <= MAX_FRAME_COUNT):
                raise FrameError(f"Frame counter must be between 0 and {MAX_FRAME_COUNT}, got {frame_counter}")
            current_counter = frame_counter
        else:
            current_counter = self._counter
            self._counter = (self._counter + 1) % (MAX_FRAME_COUNT + 1)
        
        # Create the header
        header = struct.pack(_HEADER_FORMAT, PREAMBLE, current_counter, len(payload))
        
        # Calculate CRCs
        header_crc = self.calculate_crc(header)
        payload_crc = self.calculate_crc(payload)
        
        # Assemble the frame
        return header + struct.pack(_CRC_FORMAT, header_crc) + payload + struct.pack(_CRC_FORMAT, payload_crc)
    
    def parse(self, data: bytes) -> tuple[Optional[CFrame], ParseResultEnum]:
        """
        Parse a frame from the given data.
        
        Args:
            data: Raw frame data as bytes
            
        Returns:
            Tuple of (CFrame, ParseResultEnum) where CFrame is None if parsing failed
        """
        # Check minimum frame size
        min_frame_size = HEADER_SIZE + PAYLOAD_CRC_SIZE
        if len(data) < min_frame_size:
            return (None, ParseResultEnum.FRAME_TOO_SHORT)
        
        try:
            # Extract header fields
            preamble, frame_counter, payload_size = struct.unpack(_HEADER_FORMAT, data[:_HEADER_UNPACK_SIZE])
            
            # Verify preamble
            if preamble != PREAMBLE:
                return (None, ParseResultEnum.INVALID_PREAMBLE)
            
            # Check if we have enough data for the complete frame
            expected_total_length = self.frame_length(payload_size)
            if len(data) < expected_total_length:
                return (None, ParseResultEnum.INCOMPLETE_FRAME)
            
            # Extract header CRC
            header_crc_offset = _HEADER_UNPACK_SIZE
            header_crc = struct.unpack(_CRC_FORMAT, data[header_crc_offset:header_crc_offset + _CRC_UNPACK_SIZE])[0]
            
            # Verify header CRC
            header_data = data[:_HEADER_UNPACK_SIZE]
            calculated_header_crc = self.calculate_crc(header_data)
            if header_crc != calculated_header_crc:
                return (None, ParseResultEnum.HEADER_CRC_MISMATCH)
            
            # Extract payload and payload CRC
            payload_start = HEADER_SIZE
            payload_end = payload_start + payload_size
            payload = data[payload_start:payload_end]
            
            payload_crc = struct.unpack(_CRC_FORMAT, data[payload_end:payload_end + _CRC_UNPACK_SIZE])[0]
            
            # Verify payload CRC
            calculated_payload_crc = self.calculate_crc(payload)
            if payload_crc != calculated_payload_crc:
                return (None, ParseResultEnum.PAYLOAD_CRC_MISMATCH)
            
            cframe = CFrame(frame_counter, payload)
            return (cframe, ParseResultEnum.SUCCESS)
            
        except struct.error as e:
            return (None, ParseResultEnum.STRUCT_ERROR)
        except Exception as e:
            return (None, ParseResultEnum.UNEXPECTED_ERROR)
    
    def find(self, data: bytes) -> tuple[Optional[CFrame], Optional[int]]:
        """
        Search through the bytes until a valid frame is found.
        
        Args:
            data: Raw data that may contain one or more frames
            
        Returns: Tuple of (CFrame, frame_position) where frame_position is byte offset where frame starts or None if no
        frame was found
        """
        min_search_length = len(data) - HEADER_SIZE - PAYLOAD_CRC_SIZE + 1
        
        # Look for the preamble pattern
        search_start = 0
        while search_start < min_search_length:
            # Find next potential preamble start
            preamble_pos = data.find(PREAMBLE[0], search_start)
            if preamble_pos == -1 or preamble_pos >= min_search_length:
                break
            
            # Check if we have the full preamble
            if data[preamble_pos:preamble_pos + PREAMBLE_SIZE] == PREAMBLE:
                # Found potential frame start, try to parse it
                remaining_data = data[preamble_pos:]
                cframe, result = self.parse(remaining_data)
                if result == ParseResultEnum.SUCCESS:
                    return (cframe, preamble_pos)
            
            search_start = preamble_pos + 1
        
        return (None, None)
    
    def find_frames(self, data: bytes) -> Iterator[tuple[CFrame, int]]:
        """
        Find all frames in a byte stream.
        
        Args:
            data: Raw data that may contain multiple frames
            
        Yields:
            Tuple of (CFrame, absolute_position) for each valid frame found in the stream
        """
        remaining_data = data
        absolute_position = 0
        
        while remaining_data:
            cframe, frame_position = self.find(remaining_data)
            if not cframe:
                break
            
            # Yield CFrame and its position in the byte stream
            yield (cframe, absolute_position + frame_position)
            
            # Advance past this frame using the position and frame's length property
            next_pos = frame_position + cframe.frame_length
            if next_pos >= len(remaining_data):
                break
            absolute_position += next_pos
            remaining_data = remaining_data[next_pos:]