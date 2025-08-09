FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN mkdir -p fragmentos
RUN pip install flask requests
EXPOSE 5001

CMD ["python", "nodo1.py"]
