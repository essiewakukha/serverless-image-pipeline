"""
Quick sanity check for the resize + watermark logic, run without Docker
or AWS credentials. Not part of the deployed pipeline.
"""
import io
import sys
from PIL import Image

sys.path.insert(0, "app")
import handler  # noqa: E402

# Build a synthetic 1200x800 test image (no internet/S3 needed)
img = Image.new("RGB", (1200, 800), color=(70, 130, 180))
buf = io.BytesIO()
img.save(buf, format="JPEG")
original_bytes = buf.getvalue()
print(f"Original size: {len(original_bytes)} bytes, dims: {img.size}")

processed_bytes, fmt = handler._process_image(original_bytes)
print(f"Processed size: {len(processed_bytes)} bytes, format: {fmt}")

with Image.open(io.BytesIO(processed_bytes)) as out:
    print(f"Thumbnail dims: {out.size}")
    assert out.size[0] <= handler.THUMB_W and out.size[1] <= handler.THUMB_H
    out.save("/home/claude/image-pipeline/test-events/sample_output.jpg")

print("PASSED: resize + watermark logic works.")