from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, BASE_URL

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(to, message):
    msg = twilio_client.messages.create(
        to=to,
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )
    return {"to": to, "status": msg.status, "sms_sid": msg.sid}


def make_outbound_call(to, twiml_url):
    call = twilio_client.calls.create(
        to=to,
        from_=TWILIO_PHONE_NUMBER,
        url=twiml_url,
        status_callback=f"{BASE_URL}/webhook/voice/status",
        status_callback_method="POST",
    )
    return {"call_sid": call.sid, "status": call.status}
