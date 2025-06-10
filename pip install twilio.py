from twilio.rest import Client

def enviar_sms_alerta(mensagem):
    account_sid = 'SEU_ACCOUNT_SID'
    auth_token = 'SEU_AUTH_TOKEN'
    client = Client(account_sid, auth_token)

    envio = client.messages.create(
        to='+244XXXXXXXXX',          # Número do chefe/técnico (com código do país)
        from_='+1XXXXXXXXXX',        # Número fornecido pelo Twilio
        body=mensagem
    )
    print("✅ SMS enviado com SID:", envio.sid)
