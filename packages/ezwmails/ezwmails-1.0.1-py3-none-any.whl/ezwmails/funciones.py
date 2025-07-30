import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl
import mimetypes
import os
from email.utils import encode_rfc2231


def send_email(
    subject,
    body,
    to_email,
    server,
    sender_email,
    password,
    attachment_path=None,
    cc_emails=None,
    is_html=False,
):
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Cc"] = ", ".join(cc_emails) if cc_emails else ""  # Add CC field if provided
    msg["Subject"] = subject

    # Attach the email body
    mime_type = (
        "html" if is_html else "plain"
    )  # Determine MIME type based on is_html flag
    msg.attach(MIMEText(body, mime_type))

    # Attach a file if provided
    if attachment_path:
        try:
            mime_type, _ = mimetypes.guess_type(attachment_path)
            if mime_type is None:
                mime_type = "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            with open(attachment_path, "rb") as attachment:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(attachment.read())
            encoders.encode_base64(part)

            filename = os.path.basename(attachment_path)

            # Codificar el nombre con RFC2231 para compatibilidad máxima
            encoded_name = encode_rfc2231(filename, "utf-8")

            # Añadir encabezados usando filename* (con codificación segura)
            part.add_header(
                "Content-Disposition", f"attachment; filename*={encoded_name}"
            )
            part.add_header("Content-Type", f"{mime_type}; name*=utf-8''{encoded_name}")

            msg.attach(part)

        except Exception as e:
            print(f"Error attaching file: {e}")
            return

    # Set up the secure SSL context
    context = ssl.create_default_context()

    try:
        # Connect to the mail server using TLS encryption
        with smtplib.SMTP(f"smtp.{server}.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            text = msg.as_string()
            # Include both 'To' and 'Cc' recipients in the sendmail method
            recipients = [to_email] + (cc_emails if cc_emails else [])
            server.sendmail(sender_email, recipients, text)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


def create_env_file(user, password):
    variables = {"USER": user, "PASSWORD": password}
    contenido = "\n".join([f"{clave}={valor}" for clave, valor in variables.items()])
    with open("./.env", "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    print("[*] .env file created successfully")
