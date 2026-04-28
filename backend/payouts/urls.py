from django.urls import path

from .views import (
    BalanceView,
    BankAccountListView,
    LedgerListView,
    PayoutListCreateView,
    PayoutDetailView,
)

urlpatterns = [
    path("balance/", BalanceView.as_view(), name="balance"),
    path("payouts/", PayoutListCreateView.as_view(), name="payout-list-create"),
    path("payouts/<uuid:payout_id>/", PayoutDetailView.as_view(), name="payout-detail"),
    path("ledger/", LedgerListView.as_view(), name="ledger-list"),
    path("bank-accounts/", BankAccountListView.as_view(), name="bank-account-list"),
]
