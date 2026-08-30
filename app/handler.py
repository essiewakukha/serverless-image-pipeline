"""
AWS Lambda handler for the Serverless Image Processing Pipeline.

Trigger:  S3 ObjectCreated event on the INPUT bucket
Action:   Downloads the image, creates a resized thumbnail, applies a
          text watermark, and uploads the result to the OUTPUT bucket.
Notify:   Publishes a success/failure message to an SNS topic.

Environment variables (set via Terraform):
    OUTPUT_BUCKET     - name of the S3 bucket to write processed images to
    SNS_TOPIC_ARN     - ARN of the SNS topic for notifications
    THUMBNAIL_SIZE    - "WIDTHxHEIGHT", e.g. "300x300"  (optional, default 300x300)
    WATERMARK_TEXT    - text to stamp on the image        (optional, default "PROCESSED")
"""

import os
import io
import logging
import urllib.parse
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")

OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "PROCESSED")

_raw_size = os.environ.get("THUMBNAIL_SIZE", "300x300")
try:
    THUMB_W, THUMB_H = (int(x) for x in _raw_size.lower().split("x"))
except ValueError:
    THUMB_W, THUMB_H = 300, 300

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def handler(event, context):
    """Entry point invoked by Lambda for each S3 event record."""
    results = []

    for record in event.get("Records", []):
        try:
            result = _process_record(record)
            results.append(result)
        except Exception as exc:  # noqa: BLE001 - we want to notify on any failure
            logger.exception("Failed to process record")
            _notify_failure(record, exc)
            results.append({"status": "error", "error": str(exc)})

    return {"statusCode": 200, "results": results}


def _process_record(record):
    input_bucket = record["s3"]["bucket"]["name"]
    # S3 keys in event notifications are URL-encoded (e.g. spaces become '+')
    input_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    logger.info("Processing s3://%s/%s", input_bucket, input_key)

    ext = os.path.splitext(input_key)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        logger.info("Skipping unsupported file type: %s", input_key)
        return {"status": "skipped", "key": input_key, "reason": "unsupported extension"}

    # 1. Download original image into memory
    original_bytes = _download_image(input_bucket, input_key)

    # 2. Resize + watermark
    processed_bytes, output_format = _process_image(original_bytes)

    # 3. Upload to output bucket
    output_key = _build_output_key(input_key)
    _upload_image(processed_bytes, output_key, output_format)

    # 4. Notify success
    _notify_success(input_bucket, input_key, output_key)

    return {"status": "success", "input_key": input_key, "output_key": output_key}


def _download_image(bucket: str, key: str) -> bytes:
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    except ClientError as exc:
        raise RuntimeError(f"Could not download s3://{bucket}/{key}: {exc}") from exc


def _process_image(image_bytes: bytes):
    """Resize to a thumbnail and stamp a watermark. Returns (bytes, format)."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img_format = (img.format or "JPEG").upper()

        # Normalize mode so PNG/RGBA sources still save fine as JPEG etc.
        if img.mode in ("RGBA", "P") and img_format == "JPEG":
            img = img.convert("RGB")

        # Preserve aspect ratio within the bounding box
        img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)

        img = _apply_watermark(img)

        buffer = io.BytesIO()
        save_kwargs = {"quality": 85} if img_format == "JPEG" else {}
        img.save(buffer, format=img_format, **save_kwargs)
        buffer.seek(0)
        return buffer.getvalue(), img_format


def _apply_watermark(img: Image.Image) -> Image.Image:
    """Draw semi-transparent watermark text in the bottom-right corner."""
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Scale font size relative to the thumbnail so it stays legible but unobtrusive
    font_size = max(12, int(min(base.size) * 0.08))
    try:
        font = ImageFont.truetype("/var/task/fonts/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    text = WATERMARK_TEXT
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    margin = 8
    position = (base.width - text_w - margin, base.height - text_h - margin)

    # subtle shadow, then the text itself, both semi-transparent
    draw.text((position[0] + 1, position[1] + 1), text, font=font, fill=(0, 0, 0, 140))
    draw.text(position, text, font=font, fill=(255, 255, 255, 200))

    watermarked = Image.alpha_composite(base, overlay)

    if img.mode != "RGBA":
        watermarked = watermarked.convert(img.mode if img.mode != "P" else "RGB")

    return watermarked


def _build_output_key(input_key: str) -> str:
    name, ext = os.path.splitext(input_key)
    return f"{name}-thumbnail{ext}"


def _upload_image(image_bytes: bytes, key: str, img_format: str):
    content_type = f"image/{img_format.lower() if img_format != 'JPEG' else 'jpeg'}"
    try:
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )
    except ClientError as exc:
        raise RuntimeError(f"Could not upload s3://{OUTPUT_BUCKET}/{key}: {exc}") from exc


def _notify_success(input_bucket, input_key, output_key):
    if not SNS_TOPIC_ARN:
        logger.info("SNS_TOPIC_ARN not set, skipping notification")
        return
    message = (
        f"Image processed successfully.\n\n"
        f"Source:      s3://{input_bucket}/{input_key}\n"
        f"Thumbnail:   s3://{OUTPUT_BUCKET}/{output_key}\n"
        f"Timestamp:   {datetime.now(timezone.utc).isoformat()}\n"
    )
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Image Processing Complete",
            Message=message,
        )
    except ClientError:
        logger.exception("Failed to publish success notification")


def _notify_failure(record, exc):
    if not SNS_TOPIC_ARN:
        return
    try:
        key = record.get("s3", {}).get("object", {}).get("key", "unknown")
        message = f"Image processing FAILED for key: {key}\n\nError: {exc}"
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Image Processing Failed",
            Message=message,
        )
    except ClientError:
        logger.exception("Failed to publish failure notification")