# SSL Certificates

Untuk development, generate self-signed cert:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj "/C=ID/ST=Jakarta/L=Jakarta/O=KasirPro/CN=localhost"
```

Untuk production, gunakan Let's Encrypt:

```bash
certbot certonly --standalone -d yourdomain.com
# Lalu copy:
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem key.pem
```

File yang dibutuhkan di folder ini:
- cert.pem
- key.pem
