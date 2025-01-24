# Stage 1: Build Stage
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONBUFFERED=1

# Install build dependencies (gcc, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files (only necessary files)
COPY . /app/

# Remove unnecessary files early to reduce the image size
RUN rm -rf main.py docker-compose.yaml secrets.sh script.sh test.yaml .env

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up unnecessary files to reduce image size
RUN rm -rf /root/.cache/pip  # Clean up pip cache
RUN rm -rf /app/tests  # Remove tests directory if not needed in production

# Stage 2: Final (Production) Stage
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONBUFFERED=1

# Set working directory
WORKDIR /app/

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy only necessary files from the builder stage
COPY --from=builder /app/sample.py /app/sample.py

# Set PATH for virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user and set permissions
RUN groupadd -r django && useradd -r -g django djangouser && \
    chown -R djangouser:django /app/

# Switch to non-root user
USER djangouser

# Expose port for Streamlit app
EXPOSE 8501

# Define the entrypoint for Streamlit
ENTRYPOINT ["streamlit", "run", "sample.py"]
