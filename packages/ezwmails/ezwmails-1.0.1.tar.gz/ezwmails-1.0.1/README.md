# Ezwmails, easy solution with stmp and tls
 Ready to go implementation for sending emails with python, a simple wrapper for stmp

## Install 
```python3
pip install ezwmails
```
## Examples

```python3
from ezwmails import *
import os
from dotenv import load_dotenv

user="your_mail_address"
password="ypur_mail_password"
create_env_file(user,password)
load_dotenv()

subject = " Nice subject"
body = "a great body this can have html"
server = "mail service, gmail, outlook, etc"
sender_email = os.getenv("USER")
receiver_email = "receiver_email"
password = os.getenv("PASSWORD")

send_email(subject, body, receiver_email, server, sender_email, password)
```



