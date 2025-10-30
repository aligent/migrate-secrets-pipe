FROM alpine:latest

# Install required dependencies
RUN apk add --no-cache \
    python3 \
    curl \
    git \
    github-cli

# Copy the migration script
COPY migrate-secrets.py /migrate-secrets.py

# Make the script executable
RUN chmod +x /migrate-secrets.py

# Set the entrypoint
ENTRYPOINT ["/migrate-secrets.py"]
