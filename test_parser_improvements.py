#!/usr/bin/env python3
"""
Test parser improvements for incoming/OTP exclusion
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from expense_parser import ExpenseParser

print("=" * 80)
print("Testing Parser Improvements")
print("=" * 80)

# Test with account configuration (including wallets)
MY_TEST_ACCOUNTS = [
    '3057', '3001',
    'YASSER ABDULRAHMAN ALDOSARI',
    'ياسر عبدالرحمن الدوس',
    'Barq',  # Wallet
    'BARQ',  # Alternative capitalization
]
parser = ExpenseParser(my_accounts=MY_TEST_ACCOUNTS)
print(f"\n🔧 Test Configuration:")
print(f"   My Accounts: {MY_TEST_ACCOUNTS}\n")

# Test cases
test_messages = [
    {
        'description': 'Incoming transfer (should be EXCLUDED)',
        'message': """حوالة محلية واردة
عبر:SAIB
مبلغ:SAR 10000
الى:3057
من:YASSER ABDULRAHMAN ALDOSARI
من:3001
في:25-10-25 23:14""",
        'expected': None
    },
    {
        'description': 'Outgoing purchase (should be INCLUDED)',
        'message': """شراء إنترنت بطاقة:0086 ;فيزا مبلغ:783.30 SAR لدى:Amazon SA رصيد:SAR 75,438.24 في:25-10-25 09:04""",
        'expected': 'expense'
    },
    {
        'description': 'OTP message (should be EXCLUDED)',
        'message': "Your OTP code is 123456. Do not share this code with anyone.",
        'expected': None
    },
    {
        'description': 'Arabic OTP (should be EXCLUDED)',
        'message': "رمز التحقق الخاص بك: 123456. لا تشارك هذا الرمز مع أي شخص.",
        'expected': None
    },
    {
        'description': 'Regular purchase (should be INCLUDED)',
        'message': """شراء بطاقة:9206 مبلغ:SAR 114.38 لدى:SASCO رصيد:SAR 1,234.56""",
        'expected': 'expense'
    },
    {
        'description': 'Deposit/Credit (should be EXCLUDED)',
        'message': "إيداع مبلغ SAR 5000 في حسابك",
        'expected': None
    },
    {
        'description': 'Internal transfer - between own accounts (should be EXCLUDED)',
        'message': """حوالة محلية
عبر:SAIB
مبلغ:SAR 5000
من:3057
الى:3001""",
        'expected': None
    },
    {
        'description': 'External transfer - to friend (should be INCLUDED as expense)',
        'message': """حوالة محلية
عبر:SAIB
مبلغ:SAR 1000
من:3057
الى:أحمد الغامدي""",
        'expected': 'transfer'
    },
    {
        'description': 'Internal transfer - real RJHI format (should be EXCLUDED)',
        'message': """حوالة محلية
المصرفRJHI
المبلغSAR 10,000.00
منX3001
الى:ياسر عبدالرحمن الدوس
الىX3057
الرسوم SAR 0.00
في10-25 23:13""",
        'expected': None
    },
    {
        'description': 'Wallet top-up - Bank to Barq (should be EXCLUDED)',
        'message': """شراء انترنت
بطاقة:9206;مدى-ابل باي
من:3057
مبلغ:SAR 100
لدى:Barq
في:25-10-26 02:29""",
        'expected': None
    },
    {
        'description': 'Real purchase at merchant (should be INCLUDED)',
        'message': """شراء انترنت
بطاقة:9206;مدى-ابل باي
من:3057
مبلغ:SAR 50
لدى:Amazon
في:25-10-26 02:29""",
        'expected': 'expense'
    },
]

print("\n📋 Running Tests:\n")

passed = 0
failed = 0

for i, test in enumerate(test_messages, 1):
    print(f"\n[Test {i}] {test['description']}")
    print(f"Message: {test['message'][:80]}...")

    result = parser.parse_message(test['message'])

    if test['expected'] is None:
        if result is None:
            print("✓ PASS - Correctly excluded")
            passed += 1
        else:
            print(f"✗ FAIL - Should be excluded but got: {result}")
            failed += 1
    else:
        if result is not None:
            print(f"✓ PASS - Correctly parsed as {result['transaction_type']}")
            print(f"  Amount: {result['currency']} {result['amount']:.2f}")
            print(f"  Merchant: {result['merchant']}")
            passed += 1
        else:
            print(f"✗ FAIL - Should be included but was excluded")
            failed += 1

print("\n" + "=" * 80)
print(f"📊 Test Results: {passed} passed, {failed} failed out of {len(test_messages)} tests")
print("=" * 80)

if failed == 0:
    print("✓ All tests passed!")
else:
    print(f"⚠ {failed} test(s) failed")
    sys.exit(1)
