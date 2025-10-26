# Guide: Categorizing "Other" Merchants

## Overview
This guide explains the best approaches to categorize merchants that are currently in the "Other" category.

## 🎯 Strategy Overview

### 1. **Enhanced Rule-Based** (FREE - Recommended First Step)
We've added 150+ Saudi-specific keywords including:
- Saudi merchants: Tamimi, Panda, Danube, Lulu, Jarir, Extra, Albaik, Kudu
- Arabic keywords: مطعم, صيدلية, بنزين, etc.
- Payment services: Careem, Hungerstation, Jahez

### 2. **Automated Recategorization Script** (FREE)
Run the `recategorize_others.py` script to automatically recategorize using enhanced rules.

### 3. **AI-Powered** (Paid but cheap)
Use OpenAI GPT-4o-mini for unknown merchants (~$0.0001 per transaction).

### 4. **Manual Merchant Cache** (FREE - Most Control)
Directly edit `merchant_cache.json` for specific merchants.

---

## 📋 Method 1: Automated Recategorization (Recommended)

### Step 1: Dry Run (Preview Changes)
```bash
python recategorize_others.py
```

This shows:
- Which merchants can be recategorized
- What category they'll move to
- How many remain in "Other"

**Example output:**
```
Found 250 expenses in 'Other' category
✓ Found 180 expenses that can be recategorized:

Groceries (45 expenses):
  📋 TAMIMI MARKETS                                    (23 txns)
  📋 PANDA                                             (15 txns)
  📋 DANUBE                                            (7 txns)

Food & Dining (32 expenses):
  📋 ALBAIK                                            (18 txns)
  📋 STARBUCKS                                         (14 txns)

⚠️ 15 unique merchants remain in 'Other':
  • UNKNOWN MERCHANT 1                                  (8 txns)
  • UNKNOWN MERCHANT 2                                  (5 txns)
```

### Step 2: Apply Changes
```bash
python recategorize_others.py --apply
```

This actually updates the database.

### Step 3: Use AI for Remaining (Optional)
```bash
# Dry run with AI
python recategorize_others.py --use-ai

# Apply with AI
python recategorize_others.py --use-ai --apply
```

**Cost:** If 50 merchants remain, cost = $0.005 (half a cent)

---

## 🤖 Method 2: Enable AI for Future Transactions

Edit `config.py`:
```python
USE_AI_CATEGORIZATION = True  # Enable AI
AI_PROVIDER = 'openai'  # Use OpenAI (cheapest)
```

Add API key to `.env`:
```
OPENAI_API_KEY=sk-...
```

Then re-run extraction:
```bash
python extract_from_txt_export.py path/to/messages.txt
```

**Cost Example:**
- 1,000 transactions with 200 unknown merchants
- Cost: 200 × $0.0001 = $0.02
- Cached merchants are FREE (0 cost on subsequent runs)

---

## ✏️ Method 3: Manual Merchant Cache

Edit `merchant_cache.json`:
```json
{
  "merchants": {
    "YOUR UNKNOWN MERCHANT": "Food & Dining",
    "ANOTHER MERCHANT": "Shopping",
    "محل غير معروف": "Groceries"
  }
}
```

Then re-run extraction or recategorize script.

---

## 🔧 Method 4: Add Custom Keywords

Edit `config/categories.json`:
```json
{
  "merchant_keywords": {
    "Food & Dining": [
      "existing keywords...",
      "your_custom_restaurant",
      "مطعمك المفضل"
    ],
    "Shopping": [
      "existing keywords...",
      "your_favorite_store"
    ]
  }
}
```

---

## 📊 New Saudi-Specific Keywords Added

### Groceries
- **Stores:** Tamimi, Panda, Danube, Lulu, Carrefour, Nesto, Othaim
- **Arabic:** التميمي, بنده, الدانوب, لولو, كارفور, العثيم

### Food & Dining
- **Restaurants:** Albaik, Kudu, Herfy
- **Arabic:** البيك, كودو, هرفي, مطعم, مقهى
- **Delivery:** Hungerstation, Jahez, Marsool, Talabat

### Transportation
- **Ride-hailing:** Careem, Uber
- **Arabic:** كريم, تاكسي
- **Fuel:** Aramco, Aldrees, بنزين, محطة

### Shopping
- **Stores:** Jarir, Extra, Saco, Centrepoint
- **Arabic:** جرير, اكسترا, ساكو, سنتربوينت
- **Online:** Noon, Shein

### Healthcare
- **Pharmacies:** Nahdi, Dawa
- **Arabic:** النهدي, الدواء, صيدلية, مستشفى

### Bills & Utilities
- **Telecom:** STC, Mobily, Zain
- **Arabic:** موبايلي, زين
- **Streaming:** Shahid, OSN, Jawwy

### Travel
- **Airlines:** Saudia, Flynas, Flyadeal
- **Arabic:** السعودية, ناس, رحلات
- **Booking:** Almosafer, Rehlat

---

## 🎯 Recommended Workflow

### For New Users:
1. ✅ Run `recategorize_others.py` (dry run) to see potential
2. ✅ Apply changes: `recategorize_others.py --apply`
3. ✅ Review remaining "Other" merchants
4. ✅ Add frequently used merchants to `merchant_cache.json`
5. ⚡ Enable AI for truly unknown merchants (optional)

### For Ongoing Use:
1. ✅ Keep AI **disabled** in config (cost savings)
2. ✅ Enhanced rules will catch 90%+ of Saudi merchants
3. ✅ Periodically run `recategorize_others.py` to catch new patterns
4. ✅ Add recurring unknown merchants to `merchant_cache.json`
5. ⚡ Enable AI only when you have many uncategorized

---

## 💡 Pro Tips

### Tip 1: Check Your Most Frequent "Other" Merchants
```bash
python recategorize_others.py | grep "remain in 'Other'"
```

### Tip 2: Add to Merchant Cache in Bulk
After seeing dry run results, add common ones to `merchant_cache.json`:
```json
{
  "TAMIMI": "Groceries",
  "ALBAIK": "Food & Dining",
  "JARIR": "Shopping"
}
```

### Tip 3: Use AI Strategically
Only enable AI when:
- You have 50+ unknown merchants
- Rules miss them consistently
- You're okay with ~$0.005 cost

### Tip 4: Review Dashboard "Other" Category
In the dashboard:
1. Filter by category = "Other"
2. See which merchants appear most
3. Add top 10 to merchant_cache.json

---

## 📊 Cost Comparison

| Method | Cost | Accuracy | Speed |
|--------|------|----------|-------|
| Enhanced Rules | FREE | 85-90% | Instant |
| Merchant Cache | FREE | 100% | Instant |
| OpenAI GPT-4o-mini | $0.0001/txn | 95-98% | ~1s per txn |
| Manual Review | FREE (your time) | 100% | Slow |

---

## 🚀 Quick Start

```bash
# 1. See what can be recategorized (FREE)
python recategorize_others.py

# 2. Apply rule-based recategorization (FREE)
python recategorize_others.py --apply

# 3. Use AI for remaining unknowns (PAID - ~$0.01 for 100 merchants)
python recategorize_others.py --use-ai --apply

# 4. Check results in dashboard
streamlit run src/dashboard.py
```

---

## 🔍 Troubleshooting

### Problem: Script says "No expenses in Other"
**Solution:** You may already have good categorization! Check dashboard.

### Problem: Many merchants still in "Other" after rules
**Solution:**
1. Check if merchant names are in English/Arabic
2. Add them to `merchant_cache.json`
3. Or enable AI: `--use-ai`

### Problem: AI costs too much
**Solution:**
1. Use rules first to reduce AI calls by 80-90%
2. Only use AI for truly unknown merchants
3. Results are cached - second run is FREE

### Problem: Wrong categorizations
**Solution:**
1. Update `merchant_cache.json` with correct category
2. Re-run: `python recategorize_others.py --apply`
3. Cache overrides everything

---

## 📝 Summary

**Best Approach:**
1. ✅ Run enhanced rules (FREE, catches 85-90%)
2. ✅ Add top unknowns to merchant_cache.json manually (FREE, 100% accurate)
3. ⚡ Use AI only for large volumes of remaining unknowns (cheap but paid)

This hybrid approach gives you the best balance of cost, accuracy, and effort!
