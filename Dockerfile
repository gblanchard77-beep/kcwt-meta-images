FROM python:3.12-slim
WORKDIR /app
COPY app.py .
ENV DATA_DIR=/data
ENV PORT=8080
RUN mkdir -p /data
EXPOSE 8080
CMD ["python", "-u", "app.py"]
