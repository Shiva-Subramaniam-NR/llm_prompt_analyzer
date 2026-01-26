"""
Domain Configuration v2.0

Embedding-based domain configuration using semantic anchors
instead of regex patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DomainConfigV2:
    """
    Domain configuration for embedding-based analysis.

    Instead of regex patterns, uses semantic anchor phrases that
    describe each parameter. Embeddings of these anchors are compared
    against extracted entities to determine parameter matches.
    """

    name: str

    # Anchor phrases for each parameter (used for semantic similarity)
    # These describe what each parameter means conceptually
    parameter_anchors: Dict[str, List[str]]

    # Entity types from spaCy NER that map to each parameter
    # This helps filter which entities to consider for each param
    entity_type_mapping: Dict[str, List[str]]

    # Threshold for parameter detection confidence (0-1)
    confidence_threshold: float = 0.60

    # Weights for vagueness calculation
    weights: Dict[str, float] = field(default_factory=lambda: {
        "completeness": 0.5,
        "specificity": 0.3,
        "ambiguity": 0.2
    })

    # Parameter criticality (for penalty calculation)
    critical_params: List[str] = field(default_factory=list)

    # Parameter type mapping (for specificity calculation)
    # Maps parameter to specificity category (date, time, budget, location, etc.)
    param_specificity_type: Dict[str, str] = field(default_factory=dict)

    def get_param_count(self) -> int:
        """Get total number of parameters"""
        return len(self.parameter_anchors)

    def is_critical(self, param: str) -> bool:
        """Check if parameter is critical"""
        return param in self.critical_params


# ============================================================
# FLIGHT BOOKING DOMAIN CONFIGURATION
# ============================================================

FLIGHT_BOOKING_V2 = DomainConfigV2(
    name="flight_booking",

    # Semantic anchor phrases for each parameter
    # The embedding model will match entities to these concepts
    parameter_anchors={
        "origin": [
            "departure city",
            "flying from",
            "leaving from",
            "starting point",
            "departing from",
            "source airport",
            "origin city",
            "from where",
            "starting location",
            "point of departure"
        ],
        "destination": [
            "arrival city",
            "going to",
            "flying to",
            "landing at",
            "destination airport",
            "target city",
            "reaching",
            "arriving at",
            "ending point",
            "where to go"
        ],
        "date_outbound": [
            "departure date",
            "travel date",
            "date of journey",
            "flying on",
            "traveling on",
            "outbound date",
            "date of travel",
            "when to fly",
            "journey date",
            "on which date"
        ],
        "date_return": [
            "return date",
            "coming back on",
            "return journey",
            "returning on",
            "back on",
            "inbound date",
            "return travel date",
            "date of return"
        ],
        "time_preference": [
            "departure time",
            "flight timing",
            "preferred time",
            "time of day",
            "when during day",
            "what time",
            "timing preference",
            "time slot",
            "preferred hours"
        ],
        "class": [
            "cabin class",
            "seat class",
            "travel class",
            "economy or business",
            "seating type",
            "flight class",
            "class preference",
            "economy business first"
        ],
        "budget": [
            "maximum price",
            "cost limit",
            "budget constraint",
            "price range",
            "spending limit",
            "ticket cost",
            "fare limit",
            "maximum cost",
            "price cap",
            "budget amount"
        ]
    },

    # Map spaCy entity types to parameters
    # This helps filter which entities might match which parameters
    entity_type_mapping={
        "origin": ["GPE", "LOC", "FAC", "ORG"],  # Geo-political, Location, Facility
        "destination": ["GPE", "LOC", "FAC", "ORG"],
        "date_outbound": ["DATE", "TIME"],
        "date_return": ["DATE", "TIME"],
        "time_preference": ["TIME", "DATE"],
        "class": [],  # Will match noun chunks
        "budget": ["MONEY", "CARDINAL", "QUANTITY"]
    },

    # Confidence threshold for semantic matching
    confidence_threshold=0.55,

    # Critical parameters (missing these incurs extra penalty)
    critical_params=["origin", "destination", "date_outbound"],

    # Map parameters to specificity types
    param_specificity_type={
        "date_outbound": "date",
        "date_return": "date",
        "time_preference": "time",
        "budget": "budget",
        "origin": "location",
        "destination": "location",
        "class": "class"
    },

    # Weights for vagueness calculation
    weights={
        "completeness": 0.5,   # Missing parameters
        "specificity": 0.35,  # How specific the values are
        "ambiguity": 0.15     # Ambiguous language
    }
)


# ============================================================
# CONTEXT PATTERNS FOR PARAMETER DETECTION
# ============================================================
# These help identify which parameter an entity belongs to
# based on surrounding words

CONTEXT_PATTERNS = {
    "origin": [
        "from", "departing", "leaving", "starting", "flying from",
        "out of", "depart from", "originating"
    ],
    "destination": [
        "to", "going", "arriving", "reaching", "landing",
        "headed to", "bound for", "flying to"
    ],
    "date_outbound": [
        "on", "dated", "for", "traveling", "departing on",
        "leaving on", "outbound"
    ],
    "date_return": [
        "return", "returning", "back", "coming back", "inbound"
    ],
    "time_preference": [
        "at", "around", "by", "before", "after", "timing",
        "time", "during"
    ],
    "class": [
        "class", "cabin", "seat", "seating"
    ],
    "budget": [
        "budget", "cost", "price", "fare", "spend", "maximum",
        "under", "less than", "not more than", "within"
    ]
}


# ============================================================
# CLASS KEYWORDS (for explicit class detection)
# ============================================================

CLASS_KEYWORDS = {
    "economy": ["economy", "economy class", "coach", "standard"],
    "premium_economy": ["premium economy", "premium"],
    "business": ["business", "business class"],
    "first": ["first", "first class"]
}


def get_domain_config(domain_name: str) -> DomainConfigV2:
    """
    Get domain configuration by name.

    Args:
        domain_name: Name of the domain

    Returns:
        Domain configuration object
    """
    domains = {
        "flight_booking": FLIGHT_BOOKING_V2
    }

    if domain_name not in domains:
        raise ValueError(f"Unknown domain: {domain_name}. Available: {list(domains.keys())}")

    return domains[domain_name]
