from payment.models import Payment, Transaction, DepositTransaction
from payment.consts import CONFIRMED_PAYMENT, EXPIRED_PAYMENT
from payment.utils import get_usdt_transaction_on_trc20_info, calculate_user_wallet, create_vpn_for_payment
from tgbot.handlers.broadcast_message.utils import send_one_message
from payment.utils import can_transaction_be_confirmed
from dtb.celery import app


@app.task(ignore_result=True)
def update_deposit_transactions_status():
    deposits_trx = DepositTransaction.objects.filter(status__in=[DepositTransaction.DepositTransactionStatus.PAYED])
    for d in deposits_trx:
        trx_info = get_usdt_transaction_on_trc20_info(d.trx_hash)
        if can_transaction_be_confirmed(trx_info) and trx_info.confirmed:
            d.status = DepositTransaction.DepositTransactionStatus.PAYED_AND_CONFIRMED
            d.save()
            send_one_message(
                text=CONFIRMED_PAYMENT,
                user_id=d.user.user_id,
            )


@app.task(ignore_result=True)
def update_payment_status():
    payments = Payment.objects.filter(
        status__in=[Payment.PaymentStatus.IN_PROGRESS])
    for p in payments:
        user_wallet = calculate_user_wallet(p.user)
        if user_wallet < p.amount_after_discount:
            if p.expired_after <= 0:
                p.status = Payment.PaymentStatus.FAILURE
                p.save()
                send_one_message(
                    text=EXPIRED_PAYMENT,
                    user_id=p.user.user_id,
                )
            continue

        Transaction.objects.create(payment=p, amount=p.amount)
        p.status = Payment.PaymentStatus.SUCCESS
        p.save()
        create_vpn_for_payment(p)
        send_one_message(
            text=CONFIRMED_PAYMENT,
            user_id=p.user.user_id,
        )
        # if p.status == Payment.PaymentStatus.WAIT_FOR_CONFIRMED:
        #     trx_info = get_usdt_transaction_on_trc20_info(p.trx_hash)
        #     if trx_info.confirmed and trx_info.is_success:
        #         p.status = Payment.PaymentStatus.SUCCESS
        #         p.save()
        #         vpn = create_vpn_for_payment(p)
        #         send_one_message(
        #             text=CONFIRMED_PAYMENT,
        #             user_id=p.user.user_id,
        #         )
        #     continue
