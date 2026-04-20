FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip==24.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint and set permissions BEFORE transferring ownership
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Now transfer ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--no-access-log"]