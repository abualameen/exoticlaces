from django.apps import AppConfig

class Web3PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web3_payment'
    verbose_name = 'Web3 Payment Gateway'

    def ready(self):
        import web3_payment.signals