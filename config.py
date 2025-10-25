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


# =============================================================================
# ACCOUNT WHITELIST (for Transfer Filtering)
# =============================================================================
# List your own account numbers/names here
# Transfers involving ONLY your accounts will be excluded (not expenses)
# Transfers to other people's accounts will be INCLUDED (those are expenses)
#
# Example account identifiers from your bank messages:
# - Account numbers: '3057', '3001', '1234'
# - Account names: 'YASSER ABDULRAHMAN ALDOSARI'
# - Partial matches work too
#
# To find your account identifiers:
# 1. Look at transfer messages in your Messages app
# 2. Find the "من:" (from) and "الى:" (to) fields
# 3. Add YOUR account numbers/names to the list below
# =============================================================================

MY_ACCOUNTS = [
    # Add your account numbers and names here
    # Bank accounts:
    # '3057',
    # '3001',
    # 'X3057',
    # 'X3001',
    # 'YASSER ABDULRAHMAN ALDOSARI',
    # 'ياسر عبدالرحمن الدوس',

    # Wallets (to exclude wallet top-ups):
    # 'Barq',
    # 'BARQ',
    # 'STC Pay',
    # 'Urpay',
]

# Set to True to enable transfer filtering (exclude transfers between your own accounts)
ENABLE_TRANSFER_FILTER = False

# Set to True to see which transfers are being filtered
DEBUG_TRANSFER_FILTER = False


# =============================================================================
# AI CATEGORIZATION
# =============================================================================
# Use AI (Claude) to categorize expenses intelligently
# - True: Uses Claude API for smart categorization (requires ANTHROPIC_API_KEY)
# - False: Uses simple rule-based categorization (less accurate but free)
#
# Note: AI categorization costs ~$0.001 per expense (very cheap but not free)
# Make sure you have ANTHROPIC_API_KEY in your .env file to enable
# =============================================================================

USE_AI_CATEGORIZATION = False  # Set to True to enable AI categorization
