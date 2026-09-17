FROM python:3.13-slim
WORKDIR /app
COPY pipeline.py server.py evidence.py podcast.py ./
RUN useradd --uid 10001 --create-home lilt && mkdir /data && chown lilt:lilt /data
USER lilt
ENV LILT_DATA=/data LILT_BIND=0.0.0.0 PORT=8787 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8787
CMD ["python", "server.py"]
