FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 5500
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5500", "server:app"]
