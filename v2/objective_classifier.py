"""
Objective Classifier v2.0

Classifies the core objective/intent of a prompt using semantic embeddings.
This replaces rigid pattern matching with flexible intent understanding.

Key Features:
- Identifies what the user wants to achieve (booking, inquiry, comparison, etc.)
- Dynamically determines required vs optional parameters based on intent
- Supports multi-objective detection (e.g., "compare prices and book cheapest")
- Enables objective-aware vagueness scoring
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .embedding_manager import EmbeddingManager


# ============================================================
# OBJECTIVE DEFINITIONS
# ============================================================

class ObjectiveType(Enum):
    """Enumeration of supported objective types"""

    # Booking objectives
    ONE_WAY_BOOKING = "one_way_booking"
    ROUND_TRIP_BOOKING = "round_trip_booking"
    MULTI_CITY_BOOKING = "multi_city_booking"

    # Inquiry objectives
    PRICE_INQUIRY = "price_inquiry"
    SCHEDULE_INQUIRY = "schedule_inquiry"
    AVAILABILITY_CHECK = "availability_check"

    # Comparison objectives
    PRICE_COMPARISON = "price_comparison"
    OPTION_COMPARISON = "option_comparison"

    # Modification objectives
    CHANGE_BOOKING = "change_booking"
    CANCEL_BOOKING = "cancel_booking"

    # Information objectives
    GENERAL_INQUIRY = "general_inquiry"
    POLICY_QUESTION = "policy_question"


@dataclass
class ObjectiveDefinition:
    """
    Defines an objective type with its characteristics.
    """

    name: str
    type: ObjectiveType

    # Semantic anchors - example phrases that represent this objective
    anchors: List[str]

    # Parameters required for this objective
    required_params: List[str]

    # Important but not strictly required
    important_params: List[str] = field(default_factory=list)

    # Optional parameters
    optional_params: List[str] = field(default_factory=list)

    # Whether this objective requires execution (booking) or just information
    requires_execution: bool = True

    # Description for logging/debugging
    description: str = ""


@dataclass
class ObjectiveResult:
    """
    Result of objective classification.
    """

    primary_objective: ObjectiveType
    confidence: float

    # Dynamic parameter requirements based on objective
    required_params: List[str]
    important_params: List[str]
    optional_params: List[str]

    # All objective scores for debugging
    all_scores: Dict[str, float]

    # Secondary objectives (if multi-objective prompt)
    secondary_objectives: List[Tuple[ObjectiveType, float]] = field(default_factory=list)

    # Whether this objective requires action
    requires_execution: bool = True

    def __str__(self) -> str:
        return f"Objective: {self.primary_objective.value} (confidence: {self.confidence:.2f})"


# ============================================================
# OBJECTIVE CLASSIFIER
# ============================================================

class ObjectiveClassifier:
    """
    Classifies the core objective/intent of prompts using semantic similarity.

    Process:
    1. Pre-compute embeddings of objective anchor phrases
    2. Embed the input prompt
    3. Compare prompt embedding to all objective anchors
    4. Select highest-scoring objective(s)
    5. Return dynamic parameter requirements based on objective

    Example:
        classifier = ObjectiveClassifier(embedding_manager)
        result = classifier.classify("Find cheapest flights from Delhi to Mumbai")
        # result.primary_objective = PRICE_COMPARISON
        # result.required_params = ['origin', 'destination']
        # date is optional for comparison, required for booking
    """

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        domain: str = "flight_booking"
    ):
        """
        Initialize classifier with embedding manager.

        Args:
            embedding_manager: Pre-configured embedding manager
            domain: Domain name (currently only 'flight_booking')
        """
        self.embeddings = embedding_manager
        self.domain = domain

        # Load objective definitions
        self.objectives = self._load_objectives()

        # Pre-compute objective anchor embeddings
        self._precompute_objective_embeddings()

        print(f"[OK] ObjectiveClassifier initialized with {len(self.objectives)} objectives")

    def _load_objectives(self) -> Dict[ObjectiveType, ObjectiveDefinition]:
        """
        Load objective definitions for the domain.

        Returns:
            Dict mapping ObjectiveType to ObjectiveDefinition
        """
        if self.domain == "flight_booking":
            return self._load_flight_booking_objectives()
        else:
            raise ValueError(f"Unsupported domain: {self.domain}")

    def _load_flight_booking_objectives(self) -> Dict[ObjectiveType, ObjectiveDefinition]:
        """Define objectives for flight booking domain"""

        objectives = {
            ObjectiveType.ONE_WAY_BOOKING: ObjectiveDefinition(
                name="One-Way Flight Booking",
                type=ObjectiveType.ONE_WAY_BOOKING,
                anchors=[
                    "book a one-way flight from X to Y",
                    "need a single ticket from X to Y",
                    "flying from X to Y one way",
                    "book me a flight from X to Y",
                    "I need to travel from X to Y",
                    "get me a ticket from X to Y",
                    "reserve a flight from X to Y",
                    "one way journey from X to Y",
                    "traveling from X to Y not returning",
                    "single trip from X to Y"
                ],
                required_params=['origin', 'destination', 'date_outbound'],
                important_params=['time_preference', 'class'],
                optional_params=['budget'],
                requires_execution=True,
                description="User wants to book a one-way flight"
            ),

            ObjectiveType.ROUND_TRIP_BOOKING: ObjectiveDefinition(
                name="Round-Trip Flight Booking",
                type=ObjectiveType.ROUND_TRIP_BOOKING,
                anchors=[
                    "book a round trip flight from X to Y",
                    "need return tickets from X to Y",
                    "flying from X to Y and back",
                    "two-way journey from X to Y",
                    "going to Y and coming back",
                    "round trip from X to Y",
                    "book me return flights",
                    "traveling to Y and returning",
                    "need tickets for going and coming back",
                    "book return journey from X to Y"
                ],
                required_params=['origin', 'destination', 'date_outbound', 'date_return'],
                important_params=['time_preference', 'class'],
                optional_params=['budget'],
                requires_execution=True,
                description="User wants to book round-trip flights"
            ),

            ObjectiveType.MULTI_CITY_BOOKING: ObjectiveDefinition(
                name="Multi-City Flight Booking",
                type=ObjectiveType.MULTI_CITY_BOOKING,
                anchors=[
                    "book flights to multiple cities",
                    "need to visit X then Y then Z",
                    "multi-city trip from X to Y to Z",
                    "traveling to several cities",
                    "multiple destinations in one trip",
                    "flying to X then Y then Z",
                    "book complex itinerary with stops",
                    "need flights for multi-leg journey"
                ],
                required_params=['origin', 'destination'],  # Will need multiple
                important_params=['date_outbound'],
                optional_params=['class', 'budget'],
                requires_execution=True,
                description="User wants multi-city itinerary"
            ),

            ObjectiveType.PRICE_INQUIRY: ObjectiveDefinition(
                name="Price Inquiry",
                type=ObjectiveType.PRICE_INQUIRY,
                anchors=[
                    "how much does a flight from X to Y cost",
                    "what is the price of tickets from X to Y",
                    "tell me the fare from X to Y",
                    "how much to fly from X to Y",
                    "what do flights from X to Y cost",
                    "ticket prices from X to Y",
                    "how expensive are flights from X to Y",
                    "what's the cost to travel from X to Y",
                    "flight fare from X to Y",
                    "pricing for X to Y flights"
                ],
                required_params=['origin', 'destination'],
                important_params=[],
                optional_params=['date_outbound', 'class', 'time_preference'],
                requires_execution=False,
                description="User wants to know flight prices"
            ),

            ObjectiveType.PRICE_COMPARISON: ObjectiveDefinition(
                name="Price Comparison",
                type=ObjectiveType.PRICE_COMPARISON,
                anchors=[
                    "compare flight prices from X to Y",
                    "cheapest flights from X to Y",
                    "find best deals from X to Y",
                    "show me all options from X to Y",
                    "what are the different prices from X to Y",
                    "compare airlines from X to Y",
                    "find lowest fare from X to Y",
                    "best price for flights from X to Y",
                    "compare costs for X to Y",
                    "which airline is cheapest from X to Y"
                ],
                required_params=['origin', 'destination'],
                important_params=[],
                optional_params=['date_outbound', 'class', 'time_preference', 'budget'],
                requires_execution=False,
                description="User wants to compare prices/options"
            ),

            ObjectiveType.SCHEDULE_INQUIRY: ObjectiveDefinition(
                name="Schedule Inquiry",
                type=ObjectiveType.SCHEDULE_INQUIRY,
                anchors=[
                    "what time do flights depart from X to Y",
                    "show me flight schedule from X to Y",
                    "when do flights leave from X to Y",
                    "what are the timings for X to Y",
                    "departure times from X to Y",
                    "flight timings from X to Y",
                    "when can I fly from X to Y",
                    "what times are available from X to Y",
                    "show me all departures from X to Y",
                    "schedule of flights from X to Y"
                ],
                required_params=['origin', 'destination'],
                important_params=['date_outbound'],
                optional_params=['class', 'time_preference'],
                requires_execution=False,
                description="User wants flight schedule/timing information"
            ),

            ObjectiveType.AVAILABILITY_CHECK: ObjectiveDefinition(
                name="Availability Check",
                type=ObjectiveType.AVAILABILITY_CHECK,
                anchors=[
                    "are there flights from X to Y on date",
                    "is there availability from X to Y",
                    "check if flights available from X to Y",
                    "do you have seats from X to Y",
                    "are there any tickets left for X to Y",
                    "is there space on flights from X to Y",
                    "can I get a flight from X to Y on date",
                    "are flights operating from X to Y",
                    "check availability for X to Y"
                ],
                required_params=['origin', 'destination', 'date_outbound'],
                important_params=['class'],
                optional_params=['time_preference'],
                requires_execution=False,
                description="User wants to check seat/flight availability"
            ),

            ObjectiveType.CHANGE_BOOKING: ObjectiveDefinition(
                name="Change Existing Booking",
                type=ObjectiveType.CHANGE_BOOKING,
                anchors=[
                    "change my flight booking",
                    "modify my reservation",
                    "reschedule my flight",
                    "change the date of my ticket",
                    "need to change my flight from X to Y",
                    "update my booking",
                    "alter my flight details",
                    "change flight timing"
                ],
                required_params=[],  # Requires booking reference
                important_params=['date_outbound', 'time_preference'],
                optional_params=['class'],
                requires_execution=True,
                description="User wants to modify existing booking"
            ),

            ObjectiveType.GENERAL_INQUIRY: ObjectiveDefinition(
                name="General Inquiry",
                type=ObjectiveType.GENERAL_INQUIRY,
                anchors=[
                    "tell me about flights",
                    "what are my options",
                    "help me with flight booking",
                    "I need information about flights",
                    "can you help me travel",
                    "looking for flight information",
                    "need assistance with booking"
                ],
                required_params=[],
                important_params=[],
                optional_params=['origin', 'destination', 'date_outbound'],
                requires_execution=False,
                description="User has general questions, needs guidance"
            )
        }

        return objectives

    def _precompute_objective_embeddings(self):
        """Pre-compute embeddings for all objective anchors"""
        print("[INFO] Pre-computing objective anchor embeddings...")

        objective_anchors = {}
        for obj_type, obj_def in self.objectives.items():
            objective_anchors[obj_type.value] = obj_def.anchors

        self.embeddings.precompute_anchors(objective_anchors)
        print(f"[OK] Pre-computed anchors for {len(objective_anchors)} objectives")

    def classify(self, prompt: str, return_top_k: int = 1) -> ObjectiveResult:
        """
        Classify the objective of a prompt.

        Args:
            prompt: Input prompt text
            return_top_k: Number of top objectives to consider (for multi-objective)

        Returns:
            ObjectiveResult with primary objective and parameter requirements
        """
        # Embed the prompt
        prompt_embedding = self.embeddings.encode(prompt)

        # Compare to each objective's anchors
        scores = {}
        for obj_type, obj_def in self.objectives.items():
            # Get pre-computed anchor embeddings
            anchor_embeddings = self.embeddings.get_anchor_embeddings(obj_type.value)

            if anchor_embeddings is None:
                continue

            # Compute similarities to all anchors
            similarities = self.embeddings.cosine_similarity_batch(
                prompt_embedding,
                anchor_embeddings
            )

            # Use max similarity as the objective score
            max_similarity = float(np.max(similarities))
            scores[obj_type.value] = max_similarity

        # Get top-k objectives
        sorted_objectives = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:return_top_k]

        # Primary objective (highest score)
        primary_obj_name = sorted_objectives[0][0]
        primary_confidence = sorted_objectives[0][1]

        # Find ObjectiveType from name
        primary_obj_type = None
        for obj_type in ObjectiveType:
            if obj_type.value == primary_obj_name:
                primary_obj_type = obj_type
                break

        if primary_obj_type is None:
            raise ValueError(f"Unknown objective type: {primary_obj_name}")

        # Get objective definition
        obj_def = self.objectives[primary_obj_type]

        # Secondary objectives
        secondary_objectives = []
        if return_top_k > 1:
            for obj_name, score in sorted_objectives[1:]:
                for obj_type in ObjectiveType:
                    if obj_type.value == obj_name:
                        secondary_objectives.append((obj_type, score))
                        break

        return ObjectiveResult(
            primary_objective=primary_obj_type,
            confidence=primary_confidence,
            required_params=obj_def.required_params.copy(),
            important_params=obj_def.important_params.copy(),
            optional_params=obj_def.optional_params.copy(),
            all_scores=scores,
            secondary_objectives=secondary_objectives,
            requires_execution=obj_def.requires_execution
        )

    def explain_classification(self, prompt: str) -> str:
        """
        Provide human-readable explanation of classification.

        Args:
            prompt: Input prompt

        Returns:
            Formatted explanation string
        """
        result = self.classify(prompt, return_top_k=3)

        explanation = f"""
Objective Classification for: "{prompt}"

Primary Objective: {result.primary_objective.value}
Confidence: {result.confidence:.2%}
Requires Execution: {result.requires_execution}

Parameter Requirements:
  Required: {', '.join(result.required_params) if result.required_params else 'None'}
  Important: {', '.join(result.important_params) if result.important_params else 'None'}
  Optional: {', '.join(result.optional_params) if result.optional_params else 'None'}

Alternative Interpretations:
"""
        for obj_type, score in result.secondary_objectives:
            explanation += f"  - {obj_type.value}: {score:.2%}\n"

        return explanation

    def classify_batch(self, prompts: List[str]) -> List[ObjectiveResult]:
        """
        Classify multiple prompts efficiently.

        Args:
            prompts: List of prompts to classify

        Returns:
            List of ObjectiveResult objects
        """
        return [self.classify(prompt) for prompt in prompts]

    def get_objective_definition(self, objective_type: ObjectiveType) -> ObjectiveDefinition:
        """Get the definition for a specific objective type"""
        return self.objectives.get(objective_type)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_objective_summary(result: ObjectiveResult):
    """Pretty print objective classification result"""
    print("\n" + "="*70)
    print("OBJECTIVE CLASSIFICATION RESULT")
    print("="*70)
    print(f"\nPrimary Objective: {result.primary_objective.value}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Requires Execution: {'Yes' if result.requires_execution else 'No'}")

    print("\nParameter Requirements:")
    if result.required_params:
        print(f"  [Required] {', '.join(result.required_params)}")
    if result.important_params:
        print(f"  [Important] {', '.join(result.important_params)}")
    if result.optional_params:
        print(f"  [Optional] {', '.join(result.optional_params)}")

    if result.secondary_objectives:
        print("\nAlternative Interpretations:")
        for obj_type, score in result.secondary_objectives:
            print(f"  - {obj_type.value}: {score:.2%}")

    print("\nAll Scores:")
    sorted_scores = sorted(result.all_scores.items(), key=lambda x: x[1], reverse=True)
    for obj_name, score in sorted_scores[:5]:
        bar = "#" * int(score * 20)
        print(f"  {obj_name:25} {score:.3f} [{bar}]")

    print("="*70)
