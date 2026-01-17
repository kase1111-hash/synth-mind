"""
SSL/TLS Utilities for Synth Mind Dashboard.

Provides certificate generation and loading for HTTPS/WSS support.
"""

import ipaddress
import os
import ssl
from datetime import datetime, timedelta
from pathlib import Path


def generate_self_signed_cert(
    cert_path: str = "certs/server.crt",
    key_path: str = "certs/server.key",
    hostname: str = "localhost",
    days_valid: int = 365,
    key_size: int = 2048
) -> tuple[str, str]:
    """
    Generate a self-signed certificate for development/testing.

    Args:
        cert_path: Path to save the certificate
        key_path: Path to save the private key
        hostname: Hostname for the certificate (default: localhost)
        days_valid: Certificate validity in days (default: 365)
        key_size: RSA key size in bits (default: 2048)

    Returns:
        Tuple of (cert_path, key_path)

    Raises:
        ImportError: If cryptography library is not installed
    """
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError as err:
        raise ImportError(
            "cryptography library required for certificate generation. "
            "Install with: pip install cryptography"
        ) from err

    # Create directories if needed
    cert_dir = Path(cert_path).parent
    key_dir = Path(key_path).parent
    cert_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Build certificate subject and issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Synth Mind"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])

    # Build certificate
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Write private key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Set secure permissions on private key (owner read-only)
    os.chmod(key_path, 0o600)

    # Write certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("Generated self-signed certificate:")
    print(f"  Certificate: {cert_path}")
    print(f"  Private key: {key_path}")
    print(f"  Valid for: {days_valid} days")
    print(f"  Hostname: {hostname}")

    return str(cert_path), str(key_path)


def create_ssl_context(
    cert_path: str,
    key_path: str,
    verify_mode: ssl.VerifyMode = ssl.CERT_NONE,
    check_hostname: bool = False
) -> ssl.SSLContext:
    """
    Create an SSL context for the HTTPS server.

    Args:
        cert_path: Path to the SSL certificate file
        key_path: Path to the private key file
        verify_mode: Client certificate verification mode
        check_hostname: Whether to check hostname in client certs

    Returns:
        Configured SSLContext

    Raises:
        FileNotFoundError: If cert or key files don't exist
        ssl.SSLError: If there's an issue with the certificate/key
    """
    # Validate paths exist
    if not Path(cert_path).exists():
        raise FileNotFoundError(f"Certificate not found: {cert_path}")
    if not Path(key_path).exists():
        raise FileNotFoundError(f"Private key not found: {key_path}")

    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(cert_path, key_path)

    # For development, we typically don't require client certificates
    ssl_context.verify_mode = verify_mode
    ssl_context.check_hostname = check_hostname

    # Use secure protocols only (TLS 1.2+)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    return ssl_context


def get_or_create_dev_certs(
    cert_dir: str = "certs",
    hostname: str = "localhost"
) -> tuple[str, str]:
    """
    Get existing development certificates or create new ones.

    Args:
        cert_dir: Directory for certificate storage
        hostname: Hostname for certificate

    Returns:
        Tuple of (cert_path, key_path)
    """
    cert_path = Path(cert_dir) / "server.crt"
    key_path = Path(cert_dir) / "server.key"

    # Check if certs already exist
    if cert_path.exists() and key_path.exists():
        # Verify they're still valid
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())

            # Check expiration
            if cert.not_valid_after > datetime.utcnow():
                print(f"Using existing certificate (expires: {cert.not_valid_after})")
                return str(cert_path), str(key_path)
            else:
                print("Certificate expired, generating new one...")
        except Exception:
            print("Could not validate existing certificate, generating new one...")

    # Generate new certificates
    return generate_self_signed_cert(
        cert_path=str(cert_path),
        key_path=str(key_path),
        hostname=hostname
    )


def print_cert_info(cert_path: str) -> None:
    """Print information about an SSL certificate."""
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend

        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())

        print("\nCertificate Information:")
        print(f"  Subject: {cert.subject.rfc4514_string()}")
        print(f"  Issuer: {cert.issuer.rfc4514_string()}")
        print(f"  Valid from: {cert.not_valid_before}")
        print(f"  Valid until: {cert.not_valid_after}")
        print(f"  Serial: {cert.serial_number}")

        # Check validity
        now = datetime.utcnow()
        if now < cert.not_valid_before:
            print("  Status: NOT YET VALID")
        elif now > cert.not_valid_after:
            print("  Status: EXPIRED")
        else:
            days_left = (cert.not_valid_after - now).days
            print(f"  Status: Valid ({days_left} days remaining)")

    except ImportError:
        print("cryptography library not installed - cannot read certificate details")
    except Exception as e:
        print(f"Error reading certificate: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SSL Certificate Utilities")
    parser.add_argument("--generate", action="store_true", help="Generate self-signed certificate")
    parser.add_argument("--info", type=str, help="Print info about a certificate")
    parser.add_argument("--cert-dir", type=str, default="certs", help="Certificate directory")
    parser.add_argument("--hostname", type=str, default="localhost", help="Hostname for certificate")
    parser.add_argument("--days", type=int, default=365, help="Certificate validity in days")

    args = parser.parse_args()

    if args.generate:
        cert_path = f"{args.cert_dir}/server.crt"
        key_path = f"{args.cert_dir}/server.key"
        generate_self_signed_cert(
            cert_path=cert_path,
            key_path=key_path,
            hostname=args.hostname,
            days_valid=args.days
        )
    elif args.info:
        print_cert_info(args.info)
    else:
        parser.print_help()
