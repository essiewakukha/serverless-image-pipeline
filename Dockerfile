# Official AWS Lambda Python 3.12 base image (Amazon Linux 2023)
FROM public.ecr.aws/lambda/python:3.12

# Install system fonts and clean up the package cache
RUN dnf install -y dejavu-sans-fonts && dnf clean all

# FIXED: Updated the source path to match where Amazon Linux 2023 stores the font
RUN mkdir -p ${LAMBDA_TASK_ROOT}/fonts \
    && cp /usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf ${LAMBDA_TASK_ROOT}/fonts/DejaVuSans-Bold.ttf

# Install Python dependencies first for better layer caching
COPY app/requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/handler.py ${LAMBDA_TASK_ROOT}/

# Lambda entrypoint: <filename>.<function_name>
CMD ["handler.handler"]
