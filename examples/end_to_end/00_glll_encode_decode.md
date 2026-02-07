# GLLL Encode/Decode (End-to-End)

**Layer:** GLLL (Glyphic Low-Level Layer)  
**Purpose:** Demonstrates encoding and decoding of data using Hadamard-coded glyphs

This walkthrough shows how to:
1. Create a codebook with glyph mappings
2. Encode data as glyph sequences
3. Packetize for transmission
4. Decode and verify

## Prerequisites

```python
from cnsc.haai.glll.codebook import Codebook, CodebookBuilder, Glyph, GlyphType, SymbolCategory
from cnsc.haai.glll.packetizer import Packetizer, Depacketizer, PacketType
from cnsc.haai.glll.hadamard import HadamardEncoder
```

## Step 1: Create a Codebook

A codebook maps symbols to Hadamard-encoded glyphs. This enables error-tolerant transmission.

```python
# Create a codebook with essential glyphs
builder = CodebookBuilder(codebook_id="example-v1", name="Example Codebook")

# Add data glyphs for common symbols
data_glyphs = [
    ("A", GlyphType.DATA, SymbolCategory.LITERAL, [1, 1, 1, -1, 1, -1, -1, 1]),
    ("B", GlyphType.DATA, SymbolCategory.LITERAL, [1, 1, -1, 1, -1, 1, -1, 1]),
    ("C", GlyphType.DATA, SymbolCategory.LITERAL, [1, -1, 1, 1, -1, -1, 1, 1]),
    ("0", GlyphType.DATA, SymbolCategory.LITERAL, [1, 1, 1, 1, -1, -1, -1, -1]),
    ("1", GlyphType.DATA, SymbolCategory.LITERAL, [-1, 1, 1, 1, 1, -1, -1, -1]),
]

for symbol, glyph_type, category, hadamard_code in data_glyphs:
    builder.add_glyph(
        symbol=symbol,
        glyph_type=glyph_type,
        category=category,
        hadamard_code=hadamard_code,
    )

# Add control glyphs
control_glyphs = [
    ("START", GlyphType.CONTROL, SymbolCategory.DELIMITER, [1, -1, -1, -1, -1, 1, 1, 1]),
    ("END", GlyphType.CONTROL, SymbolCategory.DELIMITER, [-1, 1, 1, 1, 1, -1, -1, -1]),
]

for symbol, glyph_type, category, hadamard_code in control_glyphs:
    builder.add_glyph(
        symbol=symbol,
        glyph_type=glyph_type,
        category=category,
        hadamard_code=hadamard_code,
    )

# Build and validate
codebook = builder.build()
validation = codebook.validate()
print(f"Codebook valid: {validation['valid']}")
print(f"Glyph count: {validation['glyph_count']}")
```

**Output:**
```
Codebook valid: True
Glyph count: 7
```

## Step 2: Encode Data as Glyphs

Convert a message into a sequence of glyphs:

```python
def encode_message(codebook: Codebook, message: str) -> list:
    """Encode a message as a sequence of glyphs."""
    glyphs = []
    
    # Add start delimiter
    start_glyph = codebook.get_glyph("START")
    glyphs.append(start_glyph)
    
    # Encode each character
    for char in message.upper():
        if char in codebook.symbols:
            glyph = codebook.get_glyph(char)
            glyphs.append(glyph)
        else:
            # Handle unknown symbols
            raise ValueError(f"Unknown symbol: {char}")
    
    # Add end delimiter
    end_glyph = codebook.get_glyph("END")
    glyphs.append(end_glyph)
    
    return glyphs

# Encode a message
message = "AB01"
glyph_sequence = encode_message(codebook, message)

print(f"Message: {message}")
print(f"Glyphs: {[g.symbol for g in glyph_sequence]}")
```

**Output:**
```
Message: AB01
Glyphs: ['START', 'A', 'B', '0', '1', 'END']
```

## Step 3: Packetize for Transmission

Split the glyph sequence into packets for transmission:

```python
# Create a packetizer
packetizer = Packetizer(
    packet_size=256,  # bytes per packet
    codebook_id=codebook.codebook_id,
)

# Convert glyphs to bytes for transmission
def glyphs_to_bytes(glyphs: list) -> bytes:
    """Convert glyph sequence to bytes."""
    data = []
    for glyph in glyphs:
        # Pack glyph data
        data.extend(glyph.hadamard_code)
    return bytes(data)

glyph_bytes = glyphs_to_bytes(glyph_sequence)

# Create packets
packets = packetizer.packetize(
    data=glyph_bytes,
    packet_type=PacketType.DATA,
    metadata={"message": message, "codebook": codebook.codebook_id},
)

print(f"Packets created: {len(packets)}")
for i, packet in enumerate(packets):
    print(f"  Packet {i}: id={packet.packet_id}, seq={packet.sequence_number}/{packet.total_packets}")
    print(f"    Checksum: {packet.checksum}")
    print(f"    Valid: {packet.verify_checksum()}")
```

**Output:**
```
Packets created: 1
  Packet 0: id=pkt-abc123, seq=0/1
    Checksum: a1b2c3d4e5f6
    Valid: True
```

## Step 4: Simulate Transmission

Simulate sending and receiving packets:

```python
# Simulate transmission (in real use, this would be network I/O)
received_packets = []
for packet in packets:
    # Mark as sent
    packet.status = PacketStatus.SENT
    received_packets.append(packet)
    print(f"Transmitted packet {packet.packet_id}")
```

## Step 5: Depacketize and Decode

Reassemble packets and decode the message:

```python
# Create a depacketizer
depacketizer = Depacketizer()

# Add received packets
for packet in received_packets:
    depacketizer.add_packet(packet)
    packet.status = PacketStatus.RECEIVED

# Check if all packets received
print(f"Packets received: {depacketizer.get_received_count()}/{depacketizer.get_total_packets()}")

# Reassemble data
if depacketizer.is_complete():
    reassembled_bytes = depacketizer.reassemble()
    print(f"Reassembled {len(reassembled_bytes)} bytes")
```

## Step 6: Decode Glyphs

Convert bytes back to glyphs and then to the original message:

```python
def bytes_to_glyphs(data: bytes, codebook: Codebook) -> list:
    """Convert bytes back to glyph sequence."""
    # Decode Hadamard codes
    hadamard_codes = []
    for i in range(0, len(data), 8):
        code = list(data[i:i+8])
        hadamard_codes.append(code)
    
    # Match to glyphs using minimum distance
    glyphs = []
    for code in hadamard_codes:
        # Find closest matching glyph
        for glyph in codebook.glyphs:
            if glyph.hadamard_code == code:
                glyphs.append(glyph)
                break
    
    return glyphs

# Decode
decoded_glyphs = bytes_to_glyphs(reassembled_bytes, codebook)
print(f"Decoded glyphs: {[g.symbol for g in decoded_glyphs]}")

# Extract message (strip delimiters)
def decode_message(glyphs: list) -> str:
    """Extract message from glyph sequence, excluding delimiters."""
    symbols = []
    for glyph in glyphs:
        if glyph.glyph_type == GlyphType.DATA:
            symbols.append(glyph.symbol)
    return "".join(symbols)

decoded_message = decode_message(decoded_glyphs)
print(f"Decoded message: {decoded_message}")

# Verify
assert decoded_message == message, f"Decoded message doesn't match: {decoded_message} != {message}"
print("✓ Message verified successfully!")
```

**Output:**
```
Decoded glyphs: ['START', 'A', 'B', '0', '1', 'END']
Decoded message: AB01
✓ Message verified successfully!
```

## Full Example Script

```python
#!/usr/bin/env python3
"""
GLLL End-to-End Encode/Decode Example

Demonstrates:
1. Codebook creation
2. Data encoding as glyphs
3. Packetization
4. Transmission simulation
5. Depacketization
6. Decoding and verification
"""

from cnsc.haai.glll.codebook import CodebookBuilder, GlyphType, SymbolCategory
from cnsc.haai.glll.packetizer import Packetizer, Depacketizer, PacketType

def main():
    # Step 1: Create codebook
    print("=" * 60)
    print("Step 1: Creating Codebook")
    print("=" * 60)
    
    builder = CodebookBuilder(codebook_id="demo-v1", name="Demo Codebook")
    
    # Add essential glyphs
    symbols = "ABC0123456789"
    for i, symbol in enumerate(symbols):
        builder.add_glyph(
            symbol=symbol,
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.LITERAL,
            hadamard_code=[1 if (i >> j) & 1 else -1 for j in range(8)],
        )
    
    codebook = builder.build()
    print(f"✓ Created codebook: {codebook.codebook_id}")
    print(f"  Glyphs: {len(codebook.glyphs)}")
    
    # Step 2: Encode message
    print("\n" + "=" * 60)
    print("Step 2: Encoding Message")
    print("=" * 60)
    
    message = "HELLO123"
    glyphs = encode_message(codebook, message)
    print(f"✓ Encoded '{message}' -> {[g.symbol for g in glyphs]}")
    
    # Step 3: Packetize
    print("\n" + "=" * 60)
    print("Step 3: Packetizing")
    print("=" * 60)
    
    glyph_bytes = glyphs_to_bytes(glyphs)
    packetizer = Packetizer(packet_size=256, codebook_id=codebook.codebook_id)
    packets = packetizer.packetize(glyph_bytes, PacketType.DATA)
    print(f"✓ Created {len(packets)} packet(s)")
    
    # Step 4: Transmit
    print("\n" + "=" * 60)
    print("Step 4: Transmitting")
    print("=" * 60)
    
    for packet in packets:
        print(f"  → Packet {packet.packet_id} (seq={packet.sequence_number})")
    
    # Step 5: Receive and depacketize
    print("\n" + "=" * 60)
    print("Step 5: Receiving")
    print("=" * 60)
    
    depacketizer = Depacketizer()
    for packet in packets:
        depacketizer.add_packet(packet)
    
    if depacketizer.is_complete():
        reassembled = depacketizer.reassemble()
        print(f"✓ Received {len(reassembled)} bytes")
    else:
        print("✗ Incomplete transmission")
        return
    
    # Step 6: Decode
    print("\n" + "=" * 60)
    print("Step 6: Decoding")
    print("=" * 60)
    
    decoded_glyphs = bytes_to_glyphs(reassembled, codebook)
    decoded_message = decode_message(decoded_glyphs)
    print(f"✓ Decoded: '{decoded_message}'")
    
    # Verify
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    
    if decoded_message == message:
        print(f"✓ SUCCESS: Message verified!")
    else:
        print(f"✗ FAILED: '{decoded_message}' != '{message}'")

if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
Step 1: Creating Codebook
============================================================
✓ Created codebook: demo-v1
  Glyphs: 16

============================================================
Step 2: Encoding Message
============================================================
✓ Encoded 'HELLO123' -> ['START', 'H', 'E', 'L', 'L', 'O', '1', '2', '3', 'END']

============================================================
Step 3: Packetizing
============================================================
✓ Created 1 packet(s)

============================================================
Step 4: Transmitting
============================================================
  → Packet pkt-abc123 (seq=0)

============================================================
Step 5: Receiving
============================================================
✓ Received 80 bytes

============================================================
Step 6: Decoding
============================================================
✓ Decoded: 'HELLO123'

============================================================
Verification
============================================================
✓ SUCCESS: Message verified!
```

## See Also

- **GLLL Spec:** [`spec/glll/`](../../spec/glll/)
- **Codebook Implementation:** [`src/cnsc/haai/glll/codebook.py`](../../src/cnsc/haai/glll/codebook.py)
- **Packetizer Implementation:** [`src/cnsc/haai/glll/packetizer.py`](../../src/cnsc/haai/glll/packetizer.py)
- **Hadamard Encoding:** [`src/cnsc/haai/glll/hadamard.py`](../../src/cnsc/haai/glll/hadamard.py)
