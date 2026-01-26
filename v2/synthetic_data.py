"""
Synthetic Data Generator v2.0

Generates labeled training data for specificity learning.
Creates date, time, and budget expressions with known specificity levels.
"""

import random
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SyntheticDataConfig:
    """Configuration for synthetic data generation"""
    samples_per_category: int = 100
    random_seed: int = 42


class SyntheticDataGenerator:
    """
    Generates synthetic training data for specificity clustering.

    Produces labeled examples at three specificity levels:
    - specific: Exact, unambiguous values
    - moderate: Somewhat specific, limited range
    - vague: Ambiguous, wide interpretation range
    """

    # Vague expressions (hardcoded as these don't follow patterns)
    VAGUE_DATES = [
        "soon", "later", "sometime", "in a few days", "in the future",
        "when possible", "at some point", "eventually", "one of these days",
        "in due time", "before long", "shortly", "in a while", "someday",
        "whenever", "any day", "at your convenience", "no rush",
        "when you can", "flexible on dates"
    ]

    VAGUE_TIMES = [
        "early", "late", "sometime during the day", "whenever",
        "flexible", "any time", "doesn't matter", "no preference",
        "when available", "not too early", "not too late", "reasonable hour",
        "convenient time", "suitable time", "around that time", "roughly",
        "more or less", "approximately", "ish", "flexible on timing"
    ]

    VAGUE_BUDGETS = [
        "cheap", "affordable", "reasonable", "not too expensive",
        "budget-friendly", "economical", "inexpensive", "cost-effective",
        "good value", "fair price", "decent price", "moderate price",
        "not extravagant", "within reason", "sensible", "practical",
        "money-conscious", "thrifty", "frugal", "penny-wise"
    ]

    # Moderate expressions
    MODERATE_DATE_PATTERNS = [
        "next {day}", "this {day}", "coming {day}", "upcoming {day}",
        "next week", "this week", "next month", "this weekend",
        "early next week", "late this week", "mid-week", "end of month",
        "beginning of {month}", "end of {month}", "around {day}"
    ]

    MODERATE_TIME_PATTERNS = [
        "morning", "afternoon", "evening", "night",
        "early morning", "late morning", "early afternoon", "late afternoon",
        "early evening", "late evening", "midday", "noon",
        "around {hour}", "before {hour}", "after {hour}"
    ]

    MODERATE_BUDGET_PATTERNS = [
        "under {amount}", "below {amount}", "less than {amount}",
        "around {amount}", "approximately {amount}", "about {amount}",
        "not more than {amount}", "maximum {amount}", "up to {amount}",
        "{amount} or less", "in the {amount} range", "somewhere around {amount}"
    ]

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def __init__(self, config: SyntheticDataConfig = None):
        """Initialize generator with configuration"""
        self.config = config or SyntheticDataConfig()
        random.seed(self.config.random_seed)

    def generate_all(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Generate complete synthetic dataset for all parameter types.

        Returns:
            Dict[param_type][specificity_level] = list of examples
        """
        return {
            "date": {
                "specific": self.generate_specific_dates(),
                "moderate": self.generate_moderate_dates(),
                "vague": self.generate_vague_dates()
            },
            "time": {
                "specific": self.generate_specific_times(),
                "moderate": self.generate_moderate_times(),
                "vague": self.generate_vague_times()
            },
            "budget": {
                "specific": self.generate_specific_budgets(),
                "moderate": self.generate_moderate_budgets(),
                "vague": self.generate_vague_budgets()
            }
        }

    # ========== DATE GENERATION ==========

    def generate_specific_dates(self) -> List[str]:
        """Generate specific date expressions"""
        dates = []
        n = self.config.samples_per_category

        # Format 1: "15th January 2025"
        for _ in range(n // 4):
            day = random.randint(1, 28)
            month = random.choice(self.MONTHS)
            year = random.randint(2024, 2026)
            suffix = self._get_day_suffix(day)
            dates.append(f"{day}{suffix} {month} {year}")

        # Format 2: "January 15, 2025"
        for _ in range(n // 4):
            day = random.randint(1, 28)
            month = random.choice(self.MONTHS)
            year = random.randint(2024, 2026)
            dates.append(f"{month} {day}, {year}")

        # Format 3: "15-01-2025" or "15/01/2025"
        for _ in range(n // 4):
            day = random.randint(1, 28)
            month = random.randint(1, 12)
            year = random.randint(2024, 2026)
            sep = random.choice(["-", "/"])
            dates.append(f"{day:02d}{sep}{month:02d}{sep}{year}")

        # Format 4: "Jan 15" or "15th Jan"
        for _ in range(n // 4):
            day = random.randint(1, 28)
            month = random.choice(self.MONTHS_SHORT)
            suffix = self._get_day_suffix(day)
            if random.random() > 0.5:
                dates.append(f"{month} {day}")
            else:
                dates.append(f"{day}{suffix} {month}")

        return dates[:n]

    def generate_moderate_dates(self) -> List[str]:
        """Generate moderately specific date expressions"""
        dates = []
        n = self.config.samples_per_category

        for _ in range(n):
            pattern = random.choice(self.MODERATE_DATE_PATTERNS)
            if "{day}" in pattern:
                dates.append(pattern.format(day=random.choice(self.DAYS)))
            elif "{month}" in pattern:
                dates.append(pattern.format(month=random.choice(self.MONTHS)))
            else:
                dates.append(pattern)

        return dates[:n]

    def generate_vague_dates(self) -> List[str]:
        """Generate vague date expressions"""
        n = self.config.samples_per_category
        # Repeat vague expressions to get enough samples
        multiplier = (n // len(self.VAGUE_DATES)) + 1
        return (self.VAGUE_DATES * multiplier)[:n]

    # ========== TIME GENERATION ==========

    def generate_specific_times(self) -> List[str]:
        """Generate specific time expressions"""
        times = []
        n = self.config.samples_per_category

        # Format 1: "9:30 AM"
        for _ in range(n // 3):
            hour = random.randint(1, 12)
            minute = random.choice([0, 15, 30, 45])
            period = random.choice(["AM", "PM", "am", "pm"])
            times.append(f"{hour}:{minute:02d} {period}")

        # Format 2: "14:00" (24-hour)
        for _ in range(n // 3):
            hour = random.randint(0, 23)
            minute = random.choice([0, 15, 30, 45])
            times.append(f"{hour:02d}:{minute:02d}")

        # Format 3: "6 PM sharp" / "exactly 9 AM"
        for _ in range(n // 3):
            hour = random.randint(1, 12)
            period = random.choice(["AM", "PM"])
            prefix = random.choice(["exactly ", "precisely ", ""])
            suffix = random.choice([" sharp", " exactly", ""])
            times.append(f"{prefix}{hour} {period}{suffix}".strip())

        return times[:n]

    def generate_moderate_times(self) -> List[str]:
        """Generate moderately specific time expressions"""
        times = []
        n = self.config.samples_per_category

        for _ in range(n):
            pattern = random.choice(self.MODERATE_TIME_PATTERNS)
            if "{hour}" in pattern:
                hour = random.randint(1, 12)
                period = random.choice(["AM", "PM"])
                times.append(pattern.format(hour=f"{hour} {period}"))
            else:
                times.append(pattern)

        return times[:n]

    def generate_vague_times(self) -> List[str]:
        """Generate vague time expressions"""
        n = self.config.samples_per_category
        multiplier = (n // len(self.VAGUE_TIMES)) + 1
        return (self.VAGUE_TIMES * multiplier)[:n]

    # ========== BUDGET GENERATION ==========

    def generate_specific_budgets(self) -> List[str]:
        """Generate specific budget expressions"""
        budgets = []
        n = self.config.samples_per_category

        currencies = [
            ("₹", ""),
            ("Rs ", ""),
            ("Rs. ", ""),
            ("", " rupees"),
            ("", " INR"),
            ("$", ""),
            ("USD ", ""),
        ]

        amounts = [
            1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000,
            5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500,
            10000, 12000, 15000, 20000, 25000, 30000
        ]

        for _ in range(n):
            amount = random.choice(amounts)
            prefix, suffix = random.choice(currencies)

            # Sometimes use 'k' notation
            if amount >= 1000 and random.random() > 0.5:
                amount_str = f"{amount // 1000}k"
            else:
                amount_str = str(amount)

            budgets.append(f"{prefix}{amount_str}{suffix}".strip())

        return budgets[:n]

    def generate_moderate_budgets(self) -> List[str]:
        """Generate moderately specific budget expressions"""
        budgets = []
        n = self.config.samples_per_category

        amounts = ["5000", "5k", "8000", "8k", "10000", "10k", "15000", "15k", "20k"]

        for _ in range(n):
            pattern = random.choice(self.MODERATE_BUDGET_PATTERNS)
            amount = random.choice(amounts)
            if random.random() > 0.5:
                amount = f"₹{amount}"
            budgets.append(pattern.format(amount=amount))

        return budgets[:n]

    def generate_vague_budgets(self) -> List[str]:
        """Generate vague budget expressions"""
        n = self.config.samples_per_category
        multiplier = (n // len(self.VAGUE_BUDGETS)) + 1
        return (self.VAGUE_BUDGETS * multiplier)[:n]

    # ========== HELPERS ==========

    def _get_day_suffix(self, day: int) -> str:
        """Get ordinal suffix for day number"""
        if 11 <= day <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    def get_statistics(self) -> Dict:
        """Get statistics about generated data"""
        data = self.generate_all()
        stats = {}
        for param_type, levels in data.items():
            stats[param_type] = {
                level: len(examples) for level, examples in levels.items()
            }
        return stats


# Convenience function
def generate_training_data(samples_per_category: int = 100) -> Dict[str, Dict[str, List[str]]]:
    """
    Generate synthetic training data.

    Args:
        samples_per_category: Number of samples per specificity level

    Returns:
        Dict[param_type][specificity_level] = list of examples
    """
    config = SyntheticDataConfig(samples_per_category=samples_per_category)
    generator = SyntheticDataGenerator(config)
    return generator.generate_all()


if __name__ == "__main__":
    # Test generation
    generator = SyntheticDataGenerator()
    data = generator.generate_all()

    print("Synthetic Data Statistics:")
    print("=" * 50)
    for param_type, levels in data.items():
        print(f"\n{param_type.upper()}:")
        for level, examples in levels.items():
            print(f"  {level}: {len(examples)} samples")
            print(f"    Examples: {examples[:3]}")
