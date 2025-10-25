"""
Configuration for expense tracker
"""

# =============================================================================
# SENDER WHITELIST
# =============================================================================
# Only process messages from these senders
# Add or remove senders as needed. Use the exact sender name from iMessage.
#
# Common Saudi bank senders:
# - AlRajhiBank
# - SAIB (Saudi Investment Bank)
# - STC Pay
# - Barq
# - KFHONLINE
# - BankAlbilad
# - etc.
#
# To find sender names in your messages:
# 1. Run: python show_senders.py
# 2. Copy the exact sender names you want to include
# =============================================================================

ALLOWED_SENDERS = [
    # Saudi Banks
    'AlRajhiBank',
    'SAIB',
    'RJHI',

    # Payment Services
    'STC Pay',
    'Barq',

    # Add your bank/payment service senders here
    # 'YourBankName',
]

# Set to True to enable sender filtering
# Set to False to process all senders (old behavior)
ENABLE_SENDER_FILTER = True

# Set to True to see which senders are being filtered out
DEBUG_SENDER_FILTER = False
