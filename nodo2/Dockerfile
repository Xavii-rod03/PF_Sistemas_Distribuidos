FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN mkdir -p fragmentos
RUN pip install flask requests
EXPOSE 5002

CMD ["python", "nodo2.py"]
