# Official AWS Lambda Python 3.12 base image (Amazon Linux 2023)
FROM public.ecr.aws/lambda/python:3.12

# A real TrueType font so the watermark renders cleanly instead of falling
# back to PIL's tiny bitmap default font.
RUN dnf install -y dejavu-sans-fonts && dnf clean all
RUN mkdir -p ${LAMBDA_TASK_ROOT}/fonts \
    && cp /usr/share/fonts/dejavu/DejaVuSans-Bold.ttf ${LAMBDA_TASK_ROOT}/fonts/DejaVuSans-Bold.ttf

# Install Python dependencies first for better layer caching
COPY app/requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/handler.py ${LAMBDA_TASK_ROOT}/

# Lambda entrypoint: <filename>.<function_name>
CMD ["handler.handler"]