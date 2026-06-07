from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, ipaddress, os

os.makedirs('/tmp/certs', exist_ok=True)

ca_key = rsa.generate_private_key(65537, 2048, default_backend())
ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'RBAC-CA')])
ca_cert = x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).serial_number(1).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).public_key(ca_key.public_key()).sign(ca_key, hashes.SHA256(), default_backend())
with open('/tmp/certs/ca.key', 'wb') as f: f.write(ca_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
with open('/tmp/certs/ca.crt', 'wb') as f: f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

server_key = rsa.generate_private_key(65537, 2048, default_backend())
server_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
server_cert = x509.CertificateBuilder().subject_name(server_name).issuer_name(ca_name).serial_number(2).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).public_key(server_key.public_key()).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'), x509.IPAddress(ipaddress.IPv4Address('127.0.0.1'))]), False).sign(ca_key, hashes.SHA256(), default_backend())
with open('/tmp/certs/server.key', 'wb') as f: f.write(server_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
with open('/tmp/certs/server.crt', 'wb') as f: f.write(server_cert.public_bytes(serialization.Encoding.PEM))

client_key = rsa.generate_private_key(65537, 2048, default_backend())
client_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'admin-client')])
client_cert = x509.CertificateBuilder().subject_name(client_name).issuer_name(ca_name).serial_number(3).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).public_key(client_key.public_key()).sign(ca_key, hashes.SHA256(), default_backend())
with open('/tmp/certs/client.key', 'wb') as f: f.write(client_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
with open('/tmp/certs/client.crt', 'wb') as f: f.write(client_cert.public_bytes(serialization.Encoding.PEM))
print('done')
