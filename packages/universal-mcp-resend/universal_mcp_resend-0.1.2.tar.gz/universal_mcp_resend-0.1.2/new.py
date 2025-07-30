import resend

resend.api_key = "re_2WGxQXRQ_Uc2EagExrPvqa9C4M3YUyigR"

params: resend.Emails.SendParams = {
  "from": "Ankit <ankit@agentr.dev>",
  "to": ["arstejas7@gmail.com","ankit21102@iiitnr.edu.in"],
  "subject": "Testing Resend testinggggg",
  "html": "<p>This is a test email, please ignore this</p>"
}

email = resend.Emails.send(params)
print(email)