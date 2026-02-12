"""Generate the ClipTray icon programmatically."""
import struct
import zlib
import os


def create_png(width, height, pixels):
    """Create a minimal PNG file from RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        for x in range(width):
            raw_data += bytes(pixels[y][x])

    idat = chunk(b'IDAT', zlib.compress(raw_data))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend


def generate_icon():
    """Generate a modern clipboard-style tray icon."""
    size = 64
    pixels = [[(0, 0, 0, 0)] * size for _ in range(size)]

    # Colors
    board_color = (100, 140, 255, 255)       # Blue clipboard board
    board_dark = (70, 110, 220, 255)         # Darker blue edge
    clip_color = (200, 210, 230, 255)        # Silver clip
    paper_color = (240, 242, 248, 255)       # White paper
    line_color = (160, 175, 210, 255)        # Text lines

    # Draw clipboard board (rounded rectangle)
    for y in range(10, 58):
        for x in range(12, 52):
            # Round corners
            corners = [
                (12, 10), (51, 10), (12, 57), (51, 57)
            ]
            is_corner = False
            for cx, cy in corners:
                dx = abs(x - cx)
                dy = abs(y - cy)
                if dx + dy <= 3 and dx > 1 and dy > 1:
                    is_corner = True
                    break
            if not is_corner:
                # Edge shading
                if x == 12 or x == 51 or y == 10 or y == 57:
                    pixels[y][x] = board_dark
                else:
                    pixels[y][x] = board_color

    # Draw clip at top
    for y in range(6, 16):
        for x in range(24, 40):
            dx_left = abs(x - 24)
            dx_right = abs(x - 39)
            if y < 10:
                if x >= 26 and x <= 37:
                    pixels[y][x] = clip_color
            else:
                if x >= 24 and x <= 39:
                    if y <= 12:
                        pixels[y][x] = clip_color

    # Draw paper area
    for y in range(17, 53):
        for x in range(17, 47):
            corners = [
                (17, 17), (46, 17), (17, 52), (46, 52)
            ]
            is_corner = False
            for cx, cy in corners:
                dx = abs(x - cx)
                dy = abs(y - cy)
                if dx + dy <= 2 and dx > 0 and dy > 0:
                    is_corner = True
                    break
            if not is_corner:
                pixels[y][x] = paper_color

    # Draw text lines on paper
    line_positions = [22, 28, 34, 40, 46]
    for ly in line_positions:
        line_width = 24 if ly != 46 else 16  # Last line shorter
        for x in range(20, 20 + line_width):
            if ly < 52:
                pixels[ly][x] = line_color
                pixels[ly + 1][x] = line_color

    # Save as PNG
    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(script_dir, 'icon.png')
    png_data = create_png(size, size, pixels)
    with open(png_path, 'wb') as f:
        f.write(png_data)
    print(f"Icon saved to {png_path}")
    return png_path


if __name__ == '__main__':
    generate_icon()
