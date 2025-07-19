import smtplib

SMTP_USER = "support@micin.id"
SMTP_PASS = "Micinid100###"

try:
    server = smtplib.SMTP_SSL("mail.micin.id", 465)
    server.login(SMTP_USER, SMTP_PASS)
    print("✅ Login berhasil")
    server.quit()
except Exception as e:
    print("❌ Gagal login:", e)

