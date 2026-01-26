"""
Domain Configuration Module v2.0

Improved patterns that avoid false positives
"""

import re


class FlightBookingDomain:
    """Configuration for flight booking domain"""
    
    # Mandatory parameters with IMPROVED patterns
    MANDATORY_PARAMS = {
        'origin': {
            'patterns': [
                r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',      # "from Chennai"
                r'\bleaving\s+(?:from\s+)?([A-Z][a-z]+)\b',           # "leaving from Delhi"
                r'\bdeparting\s+(?:from\s+)?([A-Z][a-z]+)\b',         # "departing Mumbai"
                r'\bflying\s+(?:from\s+)?([A-Z][a-z]+)\b',            # "flying from Bangalore"
                # REMOVED: r'\b([A-Z][a-z]+)\s+to\b' - Too greedy, causes false positives
            ],
            'keywords': ['from', 'departing from', 'leaving from', 'origin']
        },
        'destination': {
            'patterns': [
                r'\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',         # "to Mumbai"
                r'\bgoing\s+to\s+([A-Z][a-z]+)\b',                     # "going to Delhi"
                r'\barriving\s+(?:at|in)\s+([A-Z][a-z]+)\b',           # "arriving in Goa"
                r'\bheaded\s+to\s+([A-Z][a-z]+)\b',                    # "headed to Pune"
            ],
            'keywords': ['to', 'going to', 'arriving at', 'destination']
        },
        'date': {
            'patterns': [
                r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\b',
                r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?)\b',
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\bon\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
                r'\b(today|tomorrow)\b',
                r'\b(next\s+(?:week|month|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))\b',
            ],
            'keywords': ['on', 'date', 'for', 'on the', 'dated']
        },
        'time_preference': {
            'patterns': [
                r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b',
                r'\b(morning|afternoon|evening|night)s?\b',
                r'\b(early|late)\s+(morning|afternoon|evening)\b',
                r'\b(?:before|after|around|by)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b',
            ],
            'keywords': ['time', 'timing', 'prefer', 'morning', 'evening', 'afternoon']
        },
        'class': {
            'patterns': [
                r'\b(economy|business|first)\s*class\b',
                r'\b(premium\s*economy)\b',
            ],
            'keywords': ['class', 'cabin', 'economy', 'business', 'first']
        },
        'budget': {
            'patterns': [
                r'\b(\d+k?)\s*(?:rupees|INR|rs|Rs)\b',
                r'\$\s*(\d+k?)\b',
                r'\b(?:not\s+)?more\s+than\s+(\d+k?)\b',
                r'\b(?:under|below|less\s+than|within)\s+(\d+k?)\b',
                r'\b(?:cost|price|budget)\s+(?:should\s+)?(?:be\s+)?(?:not\s+)?(?:more\s+than\s+)?(\d+k?)\b',
            ],
            'keywords': ['cost', 'price', 'budget', 'rupees', 'INR', 'rs', 'Rs']
        }
    }
    
    # Rest of the config remains the same...
    VAGUE_TERMS = {
        'temporal': [
            'morning', 'afternoon', 'evening', 'night', 
            'early', 'late', 'soon', 'later', 'sometime',
            'next week', 'next month', 'this weekend'
        ],
        'quantifiers': [
            'around', 'approximately', 'roughly', 'about', 
            'some', 'few', 'many', 'several', 'couple'
        ],
        'qualifiers': [
            'comfortable', 'good', 'nice', 'decent', 'reasonable',
            'cheap', 'expensive', 'better', 'best', 'prefer',
            'comfort', 'convenience'
        ],
        'indefinite': [
            'any', 'either', 'whatever', 'anything', 'somewhere',
            'not an issue', "doesn't matter", 'flexible',
            'no preference', 'open to'
        ]
    }
    
    CONSTRAINT_KEYWORDS = {
        'hard': [
            'must', 'must not', 'should not', 'cannot', "won't",
            'not more than', 'not less than', 'not later than', 'not earlier than',
            'before', 'after', 'by', 'within', 'exactly', 'only',
            'maximum', 'minimum', 'at most', 'at least', 'no more than'
        ],
        'soft': [
            'prefer', 'preferably', 'ideally', 'would like', 'like to',
            'hoping', 'if possible', 'try to', 'better if', 'wish to',
            'want to', 'hoping for'
        ]
    }
    
    SPECIFIC_PATTERNS = {
        'city': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',
        'date_specific': r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
        'time_specific': r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b',
        'amount_specific': r'\b\d+k?\b',
        'class_specific': r'\b(?:economy|business|first)\s*class\b',
    }
    
    @classmethod
    def get_param_count(cls) -> int:
        """Get total number of mandatory parameters"""
        return len(cls.MANDATORY_PARAMS)