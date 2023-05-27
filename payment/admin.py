from django.contrib import admin
from payment.models import Payment, Transaction, DepositTransaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount"]


@admin.register(DepositTransaction)
class DepositTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "amount", "to_address", "trx_hash"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "amount", "amount_after_discount"]
