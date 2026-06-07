FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ flask-appbuilder flask-sqlalchemy watchdog pymysql cryptography pyopenssl
COPY ./app /app/app
COPY ./config.py /app/config.py
COPY ./certs /app/certs
EXPOSE 5000
CMD ["python3", "-c", "import ssl; from app import app; ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain('/app/certs/server.crt', '/app/certs/server.key'); app.run(host='0.0.0.0', port=5000, ssl_context=ctx)"]
