from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

hostname = "translate-service.scratch.mit.edu"
now = datetime.now(timezone.utc)

ca_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048
)

ca_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, "ScratchGrok Local CA")
])

ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_name)
    .issuer_name(ca_name)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - timedelta(minutes=5))
    .not_valid_after(now + timedelta(days=3650))
    .add_extension(
        x509.BasicConstraints(ca=True, path_length=0),
        critical=True
    )
    .add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True
    )
    .sign(ca_key, hashes.SHA256())
)

server_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048
)

server_name = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, hostname)
])

server_cert = (
    x509.CertificateBuilder()
    .subject_name(server_name)
    .issuer_name(ca_name)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - timedelta(minutes=5))
    .not_valid_after(now + timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName(hostname)]),
        critical=False
    )
    .add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True
    )
    .add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH
        ]),
        critical=False
    )
    .sign(ca_key, hashes.SHA256())
)

with open("rootCA.cer", "wb") as f:
    f.write(ca_cert.public_bytes(serialization.Encoding.DER))

with open("cert.pem", "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))

with open("key.pem", "wb") as f:
    f.write(server_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))

print("Certificate generated successfully!")
