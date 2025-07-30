"""
Comprehensive tests for the Compact Frame Format library.
"""

import pytest
import struct
from compact_frame_format.cff import (
    PREAMBLE, HEADER_SIZE, PAYLOAD_CRC_SIZE, MAX_FRAME_COUNT, Frame,
    PREAMBLE_SIZE, FRAME_COUNTER_SIZE, PAYLOAD_SIZE_BYTES, HEADER_CRC_SIZE,
    FrameError, ParseResultEnum
)


class TestFrameClass:
    """Test the Frame class functionality."""
    
    def test_frame_init_default(self):
        """Test Frame initialization with default counter."""
        frame_handler = Frame()
        # Test using the new current_counter property
        assert frame_handler.current_counter == 0, "Initial counter should be 0"
        
        # We can test counter increment by creating frames
        frame1 = frame_handler.create(b"test")
        frame2 = frame_handler.create(b"test")
        
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        
        assert result1 == ParseResultEnum.SUCCESS, "First frame should parse successfully"
        assert result2 == ParseResultEnum.SUCCESS, "Second frame should parse successfully"
        assert cframe1.frame_counter == 0, "First frame should have counter 0"
        assert cframe2.frame_counter == 1, "Second frame should have counter 1"
    
    def test_frame_init_custom_counter(self):
        """Test Frame initialization with custom counter."""
        frame_handler = Frame(initial_frame_count=100)
        assert frame_handler.current_counter == 100, "Initial counter should be 100"
        
        frame1 = frame_handler.create(b"test")
        frame2 = frame_handler.create(b"test")
        
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        
        assert result1 == ParseResultEnum.SUCCESS, "First frame should parse successfully"
        assert result2 == ParseResultEnum.SUCCESS, "Second frame should parse successfully"
        assert cframe1.frame_counter == 100, "First frame should have counter 100"
        assert cframe2.frame_counter == 101, "Second frame should have counter 101"
    
    def test_frame_init_invalid_counter(self):
        """Test Frame initialization with invalid counter values."""
        with pytest.raises(FrameError, match=f"Initial frame count must be between 0 and {MAX_FRAME_COUNT}"):
            Frame(initial_frame_count=-1)
        
        with pytest.raises(FrameError, match=f"Initial frame count must be between 0 and {MAX_FRAME_COUNT}"):
            Frame(initial_frame_count=MAX_FRAME_COUNT + 1)
    
    def test_frame_create_with_explicit_counter(self):
        """Test creating frames with explicit counter values."""
        frame_handler = Frame()
        
        # Create frames with explicit counters
        frame1 = frame_handler.create(b"test", frame_counter=500)
        frame2 = frame_handler.create(b"test", frame_counter=1000)
        frame3 = frame_handler.create(b"test")  # Should use internal counter (0)
        
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        cframe3, result3 = frame_handler.parse(frame3)
        
        assert result1 == ParseResultEnum.SUCCESS, "First frame should parse successfully"
        assert result2 == ParseResultEnum.SUCCESS, "Second frame should parse successfully"
        assert result3 == ParseResultEnum.SUCCESS, "Third frame should parse successfully"
        assert cframe1.frame_counter == 500, "Explicit counter should be used"
        assert cframe2.frame_counter == 1000, "Explicit counter should be used"
        assert cframe3.frame_counter == 0, "Internal counter should not be affected by explicit counters"
    
    def test_frame_create_invalid_counter(self):
        """Test creating frames with invalid counter values."""
        frame_handler = Frame()
        
        with pytest.raises(FrameError, match=f"Frame counter must be between 0 and {MAX_FRAME_COUNT}"):
            frame_handler.create(b"test", frame_counter=-1)
        
        with pytest.raises(FrameError, match=f"Frame counter must be between 0 and {MAX_FRAME_COUNT}"):
            frame_handler.create(b"test", frame_counter=MAX_FRAME_COUNT + 1)
    
    def test_frame_counter_independence(self):
        """Test that different Frame instances have independent counters."""
        frame1 = Frame(initial_frame_count=10)
        frame2 = Frame(initial_frame_count=20)
        
        # Create frames from both handlers
        f1_frame1 = frame1.create(b"test")
        f2_frame1 = frame2.create(b"test")
        f1_frame2 = frame1.create(b"test")
        f2_frame2 = frame2.create(b"test")
        
        # Parse and check counters
        c1_1, r1_1 = frame1.parse(f1_frame1)
        c2_1, r2_1 = frame2.parse(f2_frame1)
        c1_2, r1_2 = frame1.parse(f1_frame2)
        c2_2, r2_2 = frame2.parse(f2_frame2)
        
        assert r1_1 == ParseResultEnum.SUCCESS and r1_2 == ParseResultEnum.SUCCESS, "First handler frames should parse successfully"
        assert r2_1 == ParseResultEnum.SUCCESS and r2_2 == ParseResultEnum.SUCCESS, "Second handler frames should parse successfully"
        assert c1_1.frame_counter == 10 and c1_2.frame_counter == 11, "First handler should maintain its own counter"
        assert c2_1.frame_counter == 20 and c2_2.frame_counter == 21, "Second handler should maintain its own counter"
    
    def test_frame_counter_wraparound(self):
        """Test frame counter wraparound at MAX_FRAME_COUNT."""
        frame_handler = Frame(initial_frame_count=MAX_FRAME_COUNT)
        
        frame1 = frame_handler.create(b"test")
        frame2 = frame_handler.create(b"test")
        
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        
        assert result1 == ParseResultEnum.SUCCESS, "First frame should parse successfully"
        assert result2 == ParseResultEnum.SUCCESS, "Second frame should parse successfully"
        assert cframe1.frame_counter == MAX_FRAME_COUNT, f"Counter should be {MAX_FRAME_COUNT}"
        assert cframe2.frame_counter == 0, "Counter should wrap to 0"
    
    def test_frame_parse_and_find_methods(self):
        """Test that parse and find methods work correctly."""
        frame_handler = Frame()
        
        # Create a frame
        payload = b"test payload"
        frame = frame_handler.create(payload)
        
        # Test parse method
        cframe, result = frame_handler.parse(frame)
        assert result == ParseResultEnum.SUCCESS, "Parse should be successful"
        assert cframe.payload == payload, "Parsed payload should match original"
        assert cframe.frame_counter == 0, "Parsed counter should be 0 for first frame"
        
        # Test find method with surrounding data
        data_with_frame = b"garbage" + frame + b"more garbage"
        found_cframe, frame_position = frame_handler.find(data_with_frame)
        assert found_cframe is not None, "Should have found a frame"
        assert found_cframe.payload == payload, "Found payload should match original"
        assert found_cframe.frame_counter == 0, "Found counter should be 0 for first frame"
    
    def test_frame_length_static_method(self):
        """Test the static frame_length method."""
        # Test various payload sizes
        test_sizes = [0, 1, 10, 100, 1000, MAX_FRAME_COUNT]
        
        for payload_size in test_sizes:
            expected_length = HEADER_SIZE + payload_size + PAYLOAD_CRC_SIZE
            calculated_length = Frame.frame_length(payload_size)
            assert calculated_length == expected_length, f"Frame length calculation incorrect for payload size {payload_size}"
        
        # Test that it matches actual frame creation
        frame_handler = Frame()
        for payload_size in [0, 10, 100]:
            payload = b"X" * payload_size
            frame = frame_handler.create(payload)
            expected_length = Frame.frame_length(payload_size)
            assert len(frame) == expected_length, f"Static method doesn't match actual frame length for size {payload_size}"
    
    def test_frame_length_static_method_boundary_conditions(self):
        """Test the static frame_length method with boundary conditions."""
        # Test with payload size of 0
        assert Frame.frame_length(0) == HEADER_SIZE + PAYLOAD_CRC_SIZE, "Frame length should be minimum for empty payload"
        
        # Test with maximum payload size
        max_length = Frame.frame_length(MAX_FRAME_COUNT)
        expected_max = HEADER_SIZE + MAX_FRAME_COUNT + PAYLOAD_CRC_SIZE
        assert max_length == expected_max, f"Maximum frame length should be {expected_max}"
        
        # Test with payload size 1
        assert Frame.frame_length(1) == HEADER_SIZE + 1 + PAYLOAD_CRC_SIZE, "Frame length should be correct for single byte payload"


class TestBasicFunctionality:
    """Test basic create and parse functionality using Frame class."""
    
    def test_create_and_parse_frame(self):
        """Test creating and parsing a frame."""
        frame_handler = Frame()
        payload = b"Hello, World!"
        
        # Create a frame (frame counter is automatic)
        frame = frame_handler.create(payload)
        
        # Parse the frame
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Payload mismatch"
        assert cframe.frame_counter is not None, "Frame counter should not be None for successful parse"
        assert isinstance(cframe.frame_counter, int), "Frame counter should be an integer"
        assert 0 <= cframe.frame_counter <= MAX_FRAME_COUNT, "Frame counter should be within valid range"

    def test_frame_counter_increments(self):
        """Test that frame counter automatically increments."""
        frame_handler = Frame()
        payload = b"Test payload"
        
        # Create multiple frames and verify counters increment
        frame1 = frame_handler.create(payload)
        frame2 = frame_handler.create(payload)
        frame3 = frame_handler.create(payload)
        
        # Parse all frames
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2) 
        cframe3, result3 = frame_handler.parse(frame3)
        
        assert result1 == ParseResultEnum.SUCCESS and result2 == ParseResultEnum.SUCCESS and result3 == ParseResultEnum.SUCCESS, "All frames should parse successfully"
        assert cframe2.frame_counter == (cframe1.frame_counter + 1) % (MAX_FRAME_COUNT + 1), f"Counter should increment: {cframe1.frame_counter} -> {cframe2.frame_counter}"
        assert cframe3.frame_counter == (cframe2.frame_counter + 1) % (MAX_FRAME_COUNT + 1), f"Counter should increment: {cframe2.frame_counter} -> {cframe3.frame_counter}"

    def test_empty_payload(self):
        """Test creating and parsing a frame with empty payload."""
        frame_handler = Frame()
        payload = b""
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Empty payload mismatch"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_large_payload(self):
        """Test with a larger payload."""
        frame_handler = Frame()
        payload = b"A" * 1000  # 1KB of data
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Large payload mismatch"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_maximum_payload_size(self):
        """Test with maximum possible payload size (MAX_FRAME_COUNT bytes)."""
        frame_handler = Frame()
        payload = b"X" * MAX_FRAME_COUNT
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Maximum payload mismatch"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_various_payload_sizes(self):
        """Test with various payload sizes."""
        frame_handler = Frame()
        sizes = [1, 2, 3, 4, 5, 10, 50, 100, 255, 256, 257, 1000, 10000]
        
        for size in sizes:
            payload = bytes(range(256)) * (size // 256) + bytes(range(size % 256))
            
            frame = frame_handler.create(payload)
            cframe, result = frame_handler.parse(frame)
            
            assert result == ParseResultEnum.SUCCESS, f"Parse should be successful for size {size}, got {result}"
            assert cframe.payload == payload, f"Payload size {size} mismatch"
            assert cframe.frame_counter is not None, f"Frame counter should not be None for size {size}"

    def test_binary_data_payload(self):
        """Test with binary data including all possible byte values."""
        frame_handler = Frame()
        payload = bytes(range(256))  # All possible byte values
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Binary payload mismatch"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_frame_counter_wraparound(self):
        """Test frame counter wraps around at MAX_FRAME_COUNT."""
        # Create a few frames to see the counter is working
        frame_handler = Frame()
        frames = [frame_handler.create(b"test") for _ in range(5)]
        counters = []
        
        for frame in frames:
            cframe, result = frame_handler.parse(frame)
            assert result == ParseResultEnum.SUCCESS, "Frame should parse successfully"
            counters.append(cframe.frame_counter)
        
        # Verify counters are incrementing
        for i in range(1, len(counters)):
            expected = (counters[i-1] + 1) % (MAX_FRAME_COUNT + 1)
            assert counters[i] == expected, f"Counter should increment properly: {counters[i-1]} -> {counters[i]}"

    def test_different_payloads_different_frames(self):
        """Test that different payloads produce different frames (except for counter)."""
        frame_handler = Frame()
        payload1 = b"First payload"
        payload2 = b"Second payload"
        
        frame1 = frame_handler.create(payload1)
        frame2 = frame_handler.create(payload2)
        
        assert frame1 != frame2, "Different payloads should produce different frames"
        
        # Parse both frames
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        
        assert result1 == ParseResultEnum.SUCCESS and result2 == ParseResultEnum.SUCCESS, "Both frames should parse successfully"
        assert cframe1.payload == payload1, "First payload should match"
        assert cframe2.payload == payload2, "Second payload should match"
        assert cframe2.frame_counter == (cframe1.frame_counter + 1) % (MAX_FRAME_COUNT + 1), "Counter should increment between frames"

    def test_same_payload_same_explicit_counter(self):
        """Test that same payload with same explicit counter produces identical frames."""
        frame_handler = Frame()
        payload = b"Test payload"
        
        frame1 = frame_handler.create(payload, frame_counter=100)
        frame2 = frame_handler.create(payload, frame_counter=100)
        
        assert frame1 == frame2, "Same payload with same explicit counter should produce identical frames"
        
        # Parse both frames
        cframe1, result1 = frame_handler.parse(frame1)
        cframe2, result2 = frame_handler.parse(frame2)
        
        assert result1 == ParseResultEnum.SUCCESS and result2 == ParseResultEnum.SUCCESS, "Both frames should parse successfully"
        assert cframe1.payload == cframe2.payload == payload, "Both payloads should match"
        assert cframe1.frame_counter == cframe2.frame_counter == 100, "Both counters should be 100"


class TestFrameStructure:
    """Test frame structure and format validation."""
    
    def test_frame_structure(self):
        """Test that frame has correct structure."""
        frame_handler = Frame()
        payload = b"Test"
        frame = frame_handler.create(payload)
        
        # Check frame starts with preamble
        assert frame[0:2] == PREAMBLE, "Frame should start with preamble"
        
        # Check frame counter is present and valid
        extracted_frame_counter = struct.unpack('<H', frame[2:4])[0]
        assert 0 <= extracted_frame_counter <= MAX_FRAME_COUNT, "Frame counter should be within valid range"
        
        # Check payload size is correct
        payload_size = struct.unpack('<H', frame[4:6])[0]
        assert payload_size == len(payload), "Payload size should match actual payload length"
        
        # Check total frame length
        expected_length = HEADER_SIZE + len(payload) + PAYLOAD_CRC_SIZE
        assert len(frame) == expected_length, "Frame length should match expected"

    def test_frame_minimum_size(self):
        """Test minimum frame size with empty payload."""
        frame_handler = Frame()
        payload = b""
        frame = frame_handler.create(payload)
        
        # Minimum frame size: preamble(2) + frame_counter(2) + size(2) + header_crc(2) + payload(0) + payload_crc(2) = 10
        assert len(frame) == 10, "Minimum frame size should be 10 bytes"

    def test_preamble_values(self):
        """Test that preamble values are correct."""
        assert PREAMBLE == b'\xFA\xCE', "Preamble should be 0xFA, 0xCE"


class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_parse_invalid_frame(self):
        """Test parsing an invalid frame."""
        frame_handler = Frame()
        invalid_data = b"not a valid frame"
        
        cframe, result = frame_handler.parse(invalid_data)
        
        assert cframe is None, "CFrame should be None for invalid frame"
        assert result == ParseResultEnum.INVALID_PREAMBLE, "Result should indicate invalid preamble"

    def test_frame_too_short(self):
        """Test parsing a frame that's too short."""
        frame_handler = Frame()
        short_data = b"\xFA\xCE"  # Just preamble
        
        cframe, result = frame_handler.parse(short_data)
        
        assert cframe is None, "CFrame should be None for short frame"
        assert result == ParseResultEnum.FRAME_TOO_SHORT, "Result should indicate frame too short"

    def test_incomplete_frame(self):
        """Test parsing an incomplete frame."""
        frame_handler = Frame()
        # Create a valid frame then truncate it
        complete_frame = frame_handler.create(b"Test payload")
        incomplete_frame = complete_frame[:-5]  # Remove last 5 bytes
        
        cframe, result = frame_handler.parse(incomplete_frame)
        
        assert cframe is None, "CFrame should be None for incomplete frame"
        assert result == ParseResultEnum.INCOMPLETE_FRAME, "Result should indicate incomplete frame"

    def test_invalid_preamble(self):
        """Test parsing data with invalid preamble."""
        frame_handler = Frame()
        # Create frame with wrong preamble
        invalid_frame = bytearray(frame_handler.create(b"Test"))
        invalid_frame[0] = 0x00  # Corrupt preamble
        
        cframe, result = frame_handler.parse(bytes(invalid_frame))
        
        assert cframe is None, "CFrame should be None for invalid preamble"
        assert result == ParseResultEnum.INVALID_PREAMBLE, "Result should indicate invalid preamble"

    def test_header_crc_mismatch(self):
        """Test parsing frame with corrupted header CRC."""
        frame_handler = Frame()
        valid_frame = bytearray(frame_handler.create(b"Test payload"))
        
        # Corrupt the header CRC (bytes 6-7)
        valid_frame[6] ^= 0xFF
        
        cframe, result = frame_handler.parse(bytes(valid_frame))
        
        assert cframe is None, "CFrame should be None for header CRC mismatch"
        assert result == ParseResultEnum.HEADER_CRC_MISMATCH, "Result should indicate header CRC mismatch"

    def test_payload_crc_mismatch(self):
        """Test parsing frame with corrupted payload CRC."""
        frame_handler = Frame()
        valid_frame = bytearray(frame_handler.create(b"Test payload"))
        
        # Corrupt the payload CRC (last 2 bytes)
        valid_frame[-1] ^= 0xFF
        
        cframe, result = frame_handler.parse(bytes(valid_frame))
        
        assert cframe is None, "CFrame should be None for payload CRC mismatch"
        assert result == ParseResultEnum.PAYLOAD_CRC_MISMATCH, "Result should indicate payload CRC mismatch"

    def test_corrupted_payload(self):
        """Test parsing frame with corrupted payload data."""
        frame_handler = Frame()
        payload = b"Test payload data"
        valid_frame = bytearray(frame_handler.create(payload))
        
        # Corrupt a byte in the payload
        payload_start = HEADER_SIZE
        valid_frame[payload_start + 5] ^= 0xFF
        
        cframe, result = frame_handler.parse(bytes(valid_frame))
        
        assert cframe is None, "CFrame should be None for payload CRC mismatch due to corrupted payload"
        assert result == ParseResultEnum.PAYLOAD_CRC_MISMATCH, "Result should indicate payload CRC mismatch"

    def test_corrupted_payload_size(self):
        """Test parsing frame with corrupted payload size."""
        frame_handler = Frame()
        valid_frame = bytearray(frame_handler.create(b"Test"))
        
        # Corrupt the payload size field (bytes 4-5) to indicate larger payload
        valid_frame[4] = 0xFF
        valid_frame[5] = 0xFF
        
        cframe, result = frame_handler.parse(bytes(valid_frame))
        
        assert cframe is None, "CFrame should be None for incomplete frame due to size mismatch"
        assert result == ParseResultEnum.INCOMPLETE_FRAME, "Result should indicate incomplete frame"


class TestFrameSearching:
    """Test frame searching functionality."""
    
    def test_find_frame(self):
        """Test finding a frame in a byte stream."""
        frame_handler = Frame()
        payload = b"Test data"
        frame = frame_handler.create(payload)
        
        # Add some junk data before and after
        data_with_junk = b"junk data" + frame + b"more junk"
        
        # Find the frame
        cframe, frame_position = frame_handler.find(data_with_junk)
        
        assert cframe is not None, "Should have found a frame"
        assert cframe.payload == payload, "Found payload doesn't match original"
        assert cframe.frame_counter is not None, "Found frame counter should not be None"

    def test_find_frame_no_frame(self):
        """Test find_frame returns None when no valid frame is found."""
        frame_handler = Frame()
        junk_data = b"just some random bytes with no valid frame"
        
        cframe, frame_position = frame_handler.find(junk_data)
        
        assert cframe is None, "Should return None when no frame is found"
        assert frame_position is None, "Should return None frame position when no frame is found"

    def test_find_frame_multiple_frames(self):
        """Test finding the first valid frame when multiple frames exist."""
        frame_handler = Frame()
        payload1 = b"First frame"
        payload2 = b"Second frame"
        frame1 = frame_handler.create(payload1)
        frame2 = frame_handler.create(payload2)
        
        # Combine frames with junk data
        data = b"junk" + frame1 + b"more junk" + frame2 + b"end junk"
        
        cframe, frame_position = frame_handler.find(data)
        
        assert cframe is not None, "Should have found a frame"
        assert cframe.payload == payload1, "Should find the first valid frame"
        assert cframe.frame_counter is not None, "Should find a valid frame counter"

    def test_find_frame_with_false_preamble(self):
        """Test finding frame when preamble pattern appears in junk data."""
        frame_handler = Frame()
        payload = b"Real frame"
        frame = frame_handler.create(payload)
        
        # Create junk data that contains preamble pattern but isn't a valid frame
        fake_preamble = b"\xFA\xCE\x00\x00\x00\x00"  # Preamble + invalid data
        data = fake_preamble + b"junk" + frame + b"more junk"
        
        cframe, frame_position = frame_handler.find(data)
        
        assert cframe is not None, "Should have found a frame"
        assert cframe.payload == payload, "Should find the real frame, not the fake preamble"
        assert cframe.frame_counter is not None, "Should find a valid frame counter"

    def test_find_frame_at_start(self):
        """Test finding frame at the start of data."""
        frame_handler = Frame()
        payload = b"Frame at start"
        frame = frame_handler.create(payload)
        
        data = frame + b"trailing junk"
        
        cframe, frame_position = frame_handler.find(data)
        
        assert cframe is not None, "Should have found a frame"
        assert cframe.payload == payload, "Should find frame at start"
        assert cframe.frame_counter is not None, "Should find a valid frame counter"

    def test_find_frame_at_end(self):
        """Test finding frame at the end of data."""
        frame_handler = Frame()
        payload = b"Frame at end"
        frame = frame_handler.create(payload)
        
        data = b"leading junk" + frame
        
        cframe, frame_position = frame_handler.find(data)
        
        assert cframe is not None, "Should have found a frame"
        assert cframe.payload == payload, "Should find frame at end"
        assert cframe.frame_counter is not None, "Should find a valid frame counter"

    def test_find_frame_position_and_length(self):
        """Test that find returns correct frame position and length information."""
        frame_handler = Frame()
        payload = b"Test payload for position"
        frame = frame_handler.create(payload)
        
        # Test with frame at start of data
        data = frame + b"trailing junk"
        cframe, frame_position = frame_handler.find(data)
        
        assert cframe is not None, "Should find frame"
        assert frame_position == 0, f"Frame should be at position 0, got {frame_position}"
        frame_length = cframe.frame_length
        assert frame_length == len(frame), f"Frame length should be {len(frame)}, got {frame_length}"
        
        # Test with frame after some junk data
        prefix = b"some junk data"
        data_with_prefix = prefix + frame + b"more junk"
        cframe, frame_position = frame_handler.find(data_with_prefix)
        
        assert cframe is not None, "Should find frame"
        assert frame_position == len(prefix), f"Frame should be at position {len(prefix)}, got {frame_position}"
        frame_length = cframe.frame_length
        assert frame_length == len(frame), f"Frame length should be {len(frame)}, got {frame_length}"
        
        # Test that position + length allows proper advancement
        next_position = frame_position + frame_length
        remaining_data = data_with_prefix[next_position:]
        assert remaining_data == b"more junk", "Should correctly advance past frame"

    def test_find_multiple_frames_with_positions(self):
        """Test finding multiple frames using position and length information."""
        frame_handler = Frame()
        payload1 = b"First frame payload"
        payload2 = b"Second frame payload"
        payload3 = b"Third frame payload"
        
        frame1 = frame_handler.create(payload1)
        frame2 = frame_handler.create(payload2)
        frame3 = frame_handler.create(payload3)
        
        # Create data with frames separated by junk
        data = b"start" + frame1 + b"middle1" + frame2 + b"middle2" + frame3 + b"end"
        
        found_payloads = []
        remaining = data
        absolute_position = 0
        
        while remaining:
            cframe, frame_position = frame_handler.find(remaining)
            if not cframe:
                break
                
            found_payloads.append(cframe.payload)
            
            # Use API-provided position and frame length to advance
            frame_length = cframe.frame_length
            next_pos = frame_position + frame_length
            absolute_position += next_pos
            remaining = remaining[next_pos:]
        
        assert found_payloads == [payload1, payload2, payload3], "Should find all three frames in order"


class TestCRCCalculation:
    """Test CRC calculation functionality."""
    
    def test_crc_consistency(self):
        """Test that CRC calculation is consistent."""
        test_data = b"Test data for CRC"
        
        # Calculate CRC multiple times
        crc1 = Frame.calculate_crc(test_data)
        crc2 = Frame.calculate_crc(test_data)
        crc3 = Frame.calculate_crc(test_data)
        
        assert crc1 == crc2 == crc3, "CRC calculation should be consistent"

    def test_crc_different_data(self):
        """Test that different data produces different CRCs."""
        data1 = b"First data"
        data2 = b"Second data"
        
        crc1 = Frame.calculate_crc(data1)
        crc2 = Frame.calculate_crc(data2)
        
        assert crc1 != crc2, "Different data should produce different CRCs"

    def test_crc_empty_data(self):
        """Test CRC calculation with empty data."""
        empty_data = b""
        
        crc = Frame.calculate_crc(empty_data)
        
        assert isinstance(crc, int), "CRC should be an integer"
        assert 0 <= crc <= 0xFFFF, "CRC should be a 16-bit value"

    def test_crc_single_byte_differences(self):
        """Test that single byte differences produce different CRCs."""
        base_data = b"Test data"
        
        for i in range(len(base_data)):
            modified_data = bytearray(base_data)
            modified_data[i] ^= 0x01  # Flip one bit
            
            crc_base = Frame.calculate_crc(base_data)
            crc_modified = Frame.calculate_crc(bytes(modified_data))
            
            assert crc_base != crc_modified, f"Single bit change at position {i} should change CRC"

    def test_frame_counter_affects_header_crc(self):
        """Test that automatic frame counter changes affect header CRC."""
        frame_handler = Frame()
        payload = b"Test payload"
        
        # Create two frames with same payload but different counters
        frame1 = frame_handler.create(payload)
        frame2 = frame_handler.create(payload)
        
        # Extract header CRCs
        header_crc1 = struct.unpack('<H', frame1[6:8])[0]
        header_crc2 = struct.unpack('<H', frame2[6:8])[0]
        
        assert header_crc1 != header_crc2, "Different frame counters should produce different header CRCs"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_payload_with_preamble_pattern(self):
        """Test payload containing preamble pattern."""
        frame_handler = Frame()
        payload = b"Start\xFA\xCEEnd"  # Contains preamble pattern
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Payload with preamble pattern should be preserved"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_payload_all_zeros(self):
        """Test payload with all zero bytes."""
        frame_handler = Frame()
        payload = b"\x00" * 100
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "All-zero payload should be preserved"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_payload_all_ones(self):
        """Test payload with all 0xFF bytes."""
        frame_handler = Frame()
        payload = b"\xFF" * 100
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "All-ones payload should be preserved"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_repeating_preamble_in_payload(self):
        """Test payload with repeating preamble pattern."""
        frame_handler = Frame()
        payload = b"\xFA\xCE" * 10  # Repeating preamble pattern
        
        frame = frame_handler.create(payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, f"Parse should be successful, got {result}"
        assert cframe.payload == payload, "Repeating preamble payload should be preserved"
        assert cframe.frame_counter is not None, "Frame counter should not be None"

    def test_partial_frame_data(self):
        """Test parsing various partial frame data scenarios."""
        frame_handler = Frame()
        complete_frame = frame_handler.create(b"Complete frame")
        
        # Test with different partial lengths
        for i in range(1, len(complete_frame)):
            partial_frame = complete_frame[:i]
            cframe, result = frame_handler.parse(partial_frame)
            
            assert cframe is None, f"CFrame should be None for partial frame of length {i}"
            assert result in [ParseResultEnum.FRAME_TOO_SHORT, ParseResultEnum.INCOMPLETE_FRAME], f"Should indicate frame issue for length {i}"

    def test_exact_minimum_buffer_sizes(self):
        """Test frames at exact minimum and boundary sizes."""
        frame_handler = Frame()
        
        # Test empty payload (minimum frame)
        empty_frame = frame_handler.create(b"")
        cframe, result = frame_handler.parse(empty_frame)
        
        assert result == ParseResultEnum.SUCCESS, "Empty frame should parse successfully"
        assert cframe.payload == b"", "Empty payload should be preserved"
        
        # Test single byte payload
        single_frame = frame_handler.create(b"A")
        cframe, result = frame_handler.parse(single_frame)
        
        assert result == ParseResultEnum.SUCCESS, "Single byte frame should parse successfully"
        assert cframe.payload == b"A", "Single byte payload should be preserved"

    def test_struct_error_handling(self):
        """Test handling of struct.error exceptions."""
        frame_handler = Frame()
        
        # Create malformed data that might cause struct.error
        malformed_data = b"\xFA\xCE\x00"  # Valid preamble but truncated
        
        cframe, result = frame_handler.parse(malformed_data)
        
        assert cframe is None, "CFrame should be None for malformed data"
        assert result == ParseResultEnum.FRAME_TOO_SHORT, "Should handle struct errors gracefully"

    def test_exception_handling_coverage(self):
        """Test various exception handling paths."""
        frame_handler = Frame()
        
        # Test with various invalid inputs
        test_cases = [
            b"",  # Empty data
            b"\xFA",  # Single byte
            b"\xFA\xCE",  # Just preamble
            b"\xFA\xCE\x00\x00\x00\x00\x00\x00",  # Valid header but no payload CRC
        ]
        
        for test_data in test_cases:
            cframe, result = frame_handler.parse(test_data)
            assert cframe is None, f"CFrame should be None for test data: {test_data.hex()}"
            assert result != ParseResultEnum.SUCCESS, f"Should not succeed for test data: {test_data.hex()}"

    def test_payload_size_boundary_validation(self):
        """Test payload size validation at boundaries."""
        frame_handler = Frame()
        
        # Test with maximum payload size
        max_payload = b"X" * MAX_FRAME_COUNT
        frame = frame_handler.create(max_payload)
        cframe, result = frame_handler.parse(frame)
        
        assert result == ParseResultEnum.SUCCESS, "Maximum payload size should work"
        assert cframe.payload == max_payload, "Maximum payload should be preserved"

    def test_comprehensive_frame_structure_validation(self):
        """Comprehensive validation of frame structure."""
        frame_handler = Frame()
        payload = b"Test payload for validation"
        frame = frame_handler.create(payload)
        
        # Validate complete frame structure
        assert len(frame) >= 10, "Frame should be at least 10 bytes"
        assert frame[0:2] == PREAMBLE, "Should start with preamble"
        
        # Extract and validate frame counter
        frame_counter = struct.unpack('<H', frame[2:4])[0]
        assert 0 <= frame_counter <= MAX_FRAME_COUNT, "Frame counter should be valid"
        
        # Extract and validate payload size
        payload_size = struct.unpack('<H', frame[4:6])[0]
        assert payload_size == len(payload), "Payload size should match"
        
        # Validate CRCs
        header_data = frame[:6]
        expected_header_crc = Frame.calculate_crc(header_data)
        actual_header_crc = struct.unpack('<H', frame[6:8])[0]
        assert actual_header_crc == expected_header_crc, "Header CRC should match"
        
        payload_start = 8
        payload_end = payload_start + payload_size
        extracted_payload = frame[payload_start:payload_end]
        expected_payload_crc = Frame.calculate_crc(extracted_payload)
        actual_payload_crc = struct.unpack('<H', frame[payload_end:payload_end+2])[0]
        assert actual_payload_crc == expected_payload_crc, "Payload CRC should match"

    def test_stress_test_multiple_frames(self):
        """Stress test with multiple frames of varying sizes."""
        frame_handler = Frame()
        
        # Create frames with different payload sizes
        payloads = [
            b"",  # Empty
            b"A",  # Single byte
            b"Short",  # Short
            b"Medium length payload",  # Medium
            b"X" * 1000,  # Large
            bytes(range(256)),  # Binary data
        ]
        
        frames = []
        for payload in payloads:
            frame = frame_handler.create(payload)
            frames.append((frame, payload))
        
        # Parse all frames and verify
        for i, (frame, expected_payload) in enumerate(frames):
            cframe, result = frame_handler.parse(frame)
            assert result == ParseResultEnum.SUCCESS, f"Frame {i} should parse successfully"
            assert cframe.payload == expected_payload, f"Frame {i} payload should match"
            assert cframe.frame_counter == i, f"Frame {i} counter should be {i}"

    def test_crc_comprehensive_validation(self):
        """Comprehensive CRC validation tests."""
        frame_handler = Frame()
        
        # Test CRC with various data patterns
        test_patterns = [
            b"",
            b"\x00",
            b"\xFF",
            b"\x00\xFF",
            b"\xFF\x00",
            b"ASCII text data",
            bytes(range(256)),
            b"A" * 1000,
        ]
        
        for pattern in test_patterns:
            crc1 = frame_handler.calculate_crc(pattern)
            crc2 = frame_handler.calculate_crc(pattern)
            assert crc1 == crc2, f"CRC should be consistent for pattern: {pattern[:10]!r}..."
            assert 0 <= crc1 <= 0xFFFF, f"CRC should be 16-bit for pattern: {pattern[:10]!r}..."

    def test_frame_find_edge_cases(self):
        """Test frame finding with edge cases."""
        frame_handler = Frame()
        payload = b"Test payload"
        frame = frame_handler.create(payload)
        
        # Test finding frame in various positions
        test_data = b"random" + frame + b"more data"
        
        cframe, frame_position = frame_handler.find(test_data)
        
        assert cframe is not None, "Should find frame in middle of data"
        assert cframe.payload == payload, "Found payload should match"
        assert frame_position == 6, "Frame should be found at correct position"
        
        # Test with multiple false preambles
        false_data = b"\xFA\x00\xFA\x01\xFA\xCE\x00\x00" + frame
        cframe, frame_position = frame_handler.find(false_data)
        
        assert cframe is not None, "Should find real frame despite false preambles"
        assert cframe.payload == payload, "Should find correct payload"
        
        # Test with complex data
        complex_data = b"\xFA\xCE\xFF\xFF" + b"A" * 100 + frame + b"trailing"
        cframe, frame_position = frame_handler.find(complex_data)
        
        assert cframe is not None, "Should find frame in complex data"
        assert cframe.payload == payload, "Should find correct payload in complex data"

    def test_find_frames_method(self):
        """Test the find_frames generator method."""
        frame_handler = Frame()
        
        # Create multiple frames
        payloads = [b"First", b"Second", b"Third"]
        frames = [frame_handler.create(p) for p in payloads]
        
        # Combine with separators
        stream = b"start" + frames[0] + b"sep1" + frames[1] + b"sep2" + frames[2] + b"end"
        
        # Find all frames
        found_frames = list(frame_handler.find_frames(stream))
        
        assert len(found_frames) == 3, "Should find all three frames"
        
        for i, (cframe, position) in enumerate(found_frames):
            assert cframe.payload == payloads[i], f"Frame {i} payload should match"
            assert cframe.frame_counter == i, f"Frame {i} counter should be {i}"
            assert position >= 0, f"Frame {i} position should be non-negative" 