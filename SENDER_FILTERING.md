# Sender Filtering Guide

## Why Use Sender Filtering?

Sender filtering helps you **reduce false positives** by only processing messages from your trusted banks and payment services. This prevents personal contacts or promotional messages from being incorrectly parsed as expenses.

## How to Use

### Step 1: Find Your Senders

Run the sender analysis script to see all senders with financial messages:

```bash
python show_senders.py
```

This will show output like:

```
📊 Found 245 financial messages from 12 unique senders:

================================================================================
SENDER                                       COUNT
================================================================================
AlRajhiBank                                    156
SAIB                                            45
Barq                                            23
STC Pay                                         12
MyFriend                                         5
SomeStore                                        4
================================================================================
```

### Step 2: Configure Allowed Senders

Edit `config.py` and add your bank/payment service senders to the `ALLOWED_SENDERS` list:

```python
ALLOWED_SENDERS = [
    'AlRajhiBank',    # Your main bank
    'SAIB',           # Secondary bank
    'STC Pay',        # Payment app
    'Barq',           # Another payment service
]

# Enable the filter
ENABLE_SENDER_FILTER = True
```

**Important:** Use the **exact sender name** from the output of `show_senders.py`.

### Step 3: Extract with Filtering

Run the extraction script as normal:

```bash
python extract_from_txt_export.py
```

You'll see the filter status at the start:

```
================================================================================
Extract Expenses from iMessage TXT Export
================================================================================

🔍 Sender Filter: ENABLED
   Only processing messages from 4 allowed sender(s):
   • AlRajhiBank
   • SAIB
   • STC Pay
   • Barq
```

Now only messages from your whitelisted senders will be processed!

## Configuration Options

In `config.py`:

- **`ALLOWED_SENDERS`**: List of sender names to process
- **`ENABLE_SENDER_FILTER`**: Set to `True` to enable filtering, `False` to process all
- **`DEBUG_SENDER_FILTER`**: Set to `True` to see which senders are being skipped

## Debugging

If you want to see which senders are being filtered out, enable debug mode:

```python
DEBUG_SENDER_FILTER = True
```

Then run the extraction and you'll see:

```
🚫 Skipping message from: MyFriend
🚫 Skipping message from: SomeStore
```

## Tips

1. **Be Specific**: Only add your actual bank and payment service senders
2. **Check Names**: Sender names are case-sensitive - use exact matches
3. **Test First**: Run `show_senders.py` first to identify your bank senders
4. **Update Regularly**: If you switch banks, update the whitelist

## Disable Filtering

To disable filtering and process all senders (old behavior):

```python
ENABLE_SENDER_FILTER = False
```
