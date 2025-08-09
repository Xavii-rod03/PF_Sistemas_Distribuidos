
FROM python:3.11-slim
WORKDIR /app
COPY api_gestor.py /api_gestor
RUN pip install flask requests
EXPOSE 5000
CMD ["python", "api_gestor.py"]
