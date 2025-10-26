"""
Categorizer - AI-powered expense categorization
"""
import os
import json
from typing import Dict, List, Optional
import pandas as pd
from dotenv import load_dotenv

# Try importing both AI providers
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ExpenseCategorizer:
    """Categorize expenses using AI and rule-based approaches"""

    def __init__(self, config_path: str = "config/categories.json", use_ai: bool = True,
                 cache_path: str = "merchant_cache.json", ai_provider: str = "openai"):
        """
        Initialize categorizer

        Args:
            config_path: Path to categories configuration file
            use_ai: Whether to use AI for categorization (requires API key)
            cache_path: Path to merchant cache file (to avoid repeated AI calls)
            ai_provider: AI provider to use ('openai' or 'anthropic')
        """
        # Load categories configuration
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.categories = config['categories']
        self.merchant_keywords = config['merchant_keywords']
        self.use_ai = use_ai
        self.cache_path = cache_path
        self.ai_provider = ai_provider.lower()

        # Load merchant cache
        self.merchant_cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    self.merchant_cache = cache_data.get('merchants', {})
            except:
                self.merchant_cache = {}

        # Initialize AI client if using AI
        self.client = None
        if use_ai:
            load_dotenv()

            if self.ai_provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key and HAS_OPENAI:
                    self.client = OpenAI(api_key=api_key)
                    print("Using OpenAI GPT for categorization")
                elif not HAS_OPENAI:
                    print("Warning: openai package not installed. Run: pip install openai")
                    self.use_ai = False
                else:
                    print("Warning: OPENAI_API_KEY not found. Falling back to rule-based categorization.")
                    self.use_ai = False

            elif self.ai_provider == 'anthropic':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key and HAS_ANTHROPIC:
                    self.client = Anthropic(api_key=api_key)
                    print("Using Anthropic Claude for categorization")
                elif not HAS_ANTHROPIC:
                    print("Warning: anthropic package not installed. Run: pip install anthropic")
                    self.use_ai = False
                else:
                    print("Warning: ANTHROPIC_API_KEY not found. Falling back to rule-based categorization.")
                    self.use_ai = False

            else:
                print(f"Warning: Unknown AI provider '{self.ai_provider}'. Use 'openai' or 'anthropic'.")
                self.use_ai = False

    def categorize_expense(
        self,
        merchant: str,
        amount: float,
        raw_message: Optional[str] = None,
        learned_category: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Categorize a single expense

        Args:
            merchant: Merchant name
            amount: Transaction amount
            raw_message: Original SMS message
            learned_category: Previously learned category for this merchant

        Returns:
            Dictionary with category and confidence score
        """
        # Normalize merchant name for cache lookup
        merchant_key = merchant.upper().strip()

        # First check if we have a learned category
        if learned_category:
            return {
                'category': learned_category,
                'confidence': 1.0,
                'method': 'learned'
            }

        # Check merchant cache (from previous AI categorizations)
        if merchant_key in self.merchant_cache:
            return {
                'category': self.merchant_cache[merchant_key],
                'confidence': 0.95,
                'method': 'cached'
            }

        # Try rule-based categorization
        rule_category = self._categorize_by_rules(merchant, raw_message)
        if rule_category:
            # Cache rule-based result to avoid future lookups
            if merchant_key not in self.merchant_cache:
                self.merchant_cache[merchant_key] = rule_category
                self._save_cache()

            return {
                'category': rule_category,
                'confidence': 0.8,
                'method': 'rules'
            }

        # Fall back to AI categorization if enabled
        if self.use_ai and self.client:
            ai_category = self._categorize_by_ai(merchant, amount, raw_message)
            if ai_category:
                # Cache this result for future use
                self.merchant_cache[merchant_key] = ai_category
                self._save_cache()

                return {
                    'category': ai_category,
                    'confidence': 0.9,
                    'method': 'ai'
                }

        # Default to 'Other' if nothing else works
        return {
            'category': 'Other',
            'confidence': 0.5,
            'method': 'default'
        }

    def categorize_batch(
        self,
        expenses_df: pd.DataFrame,
        merchant_category_map: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Categorize a batch of expenses

        Args:
            expenses_df: DataFrame with expense data
            merchant_category_map: Dictionary of learned merchant->category mappings

        Returns:
            DataFrame with added category and confidence columns
        """
        if merchant_category_map is None:
            merchant_category_map = {}

        results = []

        for idx, row in expenses_df.iterrows():
            learned = merchant_category_map.get(row['merchant'])

            result = self.categorize_expense(
                merchant=row['merchant'],
                amount=row['amount'],
                raw_message=row.get('raw_message'),
                learned_category=learned
            )

            results.append(result)

        expenses_df['category'] = [r['category'] for r in results]
        expenses_df['category_confidence'] = [r['confidence'] for r in results]
        expenses_df['category_method'] = [r['method'] for r in results]

        return expenses_df

    def _categorize_by_rules(self, merchant: str, raw_message: Optional[str] = None) -> Optional[str]:
        """
        Categorize using keyword matching rules

        Args:
            merchant: Merchant name
            raw_message: Original message

        Returns:
            Category name or None
        """
        search_text = f"{merchant} {raw_message or ''}".lower()

        # Check each category's keywords
        for category, keywords in self.merchant_keywords.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    return category

        return None

    def _save_cache(self):
        """Save merchant cache to file"""
        try:
            cache_data = {
                'comment': 'This file caches merchant categorizations to avoid repeated AI calls',
                'merchants': self.merchant_cache
            }
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save merchant cache: {e}")

    def _categorize_by_ai(
        self,
        merchant: str,
        amount: float,
        raw_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Categorize using AI (OpenAI or Anthropic)

        Args:
            merchant: Merchant name
            amount: Transaction amount
            raw_message: Original message

        Returns:
            Category name or None
        """
        if not self.client:
            return None

        # Build prompt
        categories_list = "\n".join([f"- {cat}" for cat in self.categories])

        prompt = f"""Categorize this expense into one of the following categories:

{categories_list}

Expense details:
- Merchant: {merchant}
- Amount: ${amount:.2f}
{f"- Original message: {raw_message}" if raw_message else ""}

Respond with ONLY the category name from the list above. Choose the most appropriate category."""

        try:
            if self.ai_provider == 'openai':
                # OpenAI API call
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Cheap and fast
                    messages=[
                        {"role": "system", "content": "You are a financial categorization assistant. Respond with only the category name."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=20,
                    temperature=0
                )
                category = response.choices[0].message.content.strip()

            elif self.ai_provider == 'anthropic':
                # Anthropic API call
                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                category = message.content[0].text.strip()

            else:
                return None

            # Validate category is in our list
            if category in self.categories:
                return category

        except Exception as e:
            print(f"AI categorization error: {e}")

        return None

    def add_category(self, category_name: str, keywords: Optional[List[str]] = None):
        """
        Add a new category

        Args:
            category_name: Name of new category
            keywords: List of keywords for rule-based matching
        """
        if category_name not in self.categories:
            self.categories.append(category_name)

        if keywords:
            if category_name not in self.merchant_keywords:
                self.merchant_keywords[category_name] = []
            self.merchant_keywords[category_name].extend(keywords)

    def get_category_summary(self, expenses_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary of expenses by category

        Args:
            expenses_df: DataFrame with categorized expenses

        Returns:
            Summary DataFrame
        """
        if expenses_df.empty or 'category' not in expenses_df.columns:
            return pd.DataFrame()

        summary = expenses_df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)

        summary.columns = ['total_amount', 'count', 'average_amount']
        summary = summary.sort_values('total_amount', ascending=False)

        return summary


def main():
    """Test categorization"""
    categorizer = ExpenseCategorizer(use_ai=False)

    test_expenses = [
        {'merchant': 'STARBUCKS', 'amount': 15.50, 'raw_message': 'Coffee purchase'},
        {'merchant': 'UBER', 'amount': 22.00, 'raw_message': 'Ride payment'},
        {'merchant': 'AMAZON', 'amount': 89.99, 'raw_message': 'Online shopping'},
        {'merchant': 'WHOLE FOODS', 'amount': 125.30, 'raw_message': 'Grocery shopping'},
        {'merchant': 'ATM WITHDRAWAL', 'amount': 100.00, 'raw_message': 'Cash withdrawal'},
    ]

    print("Testing Expense Categorization\n")
    print("=" * 80)

    for expense in test_expenses:
        result = categorizer.categorize_expense(
            merchant=expense['merchant'],
            amount=expense['amount'],
            raw_message=expense['raw_message']
        )

        print(f"\nMerchant: {expense['merchant']}")
        print(f"  Category: {result['category']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Method: {result['method']}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
