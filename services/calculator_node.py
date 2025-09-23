# # mental_health_calculator.py

# """
# PROOF OF CONCEPT - NOT FOR CLINICAL USE
# This system is for demonstration purposes only.
# Mental health assessment requires professional evaluation.
# """

# from datetime import datetime
# from typing import Dict, List, Any, Optional, Tuple


# class MentalHealthCalculator:
#     """
#     A comprehensive calculator for tracking mental health scores with decay mechanisms.
    
#     Supports 7 mental health labels with configurable weights, decay rates, 
#     sentiment-based adjustments, and context filtering.
#     """
    
#     MENTAL_HEALTH_LABELS = [
#         "Normal", "Depression", "Suicidal", "Anxiety", 
#         "Stress", "Bi-Polar", "Personality Disorder"
#     ]
    
#     DEFAULT_DECAY_SCORES = {
#         "Normal": 2.0, "Depression": 1.5, "Suicidal": 3.0, "Anxiety": 2.2,
#         "Stress": 2.8, "Bi-Polar": 1.2, "Personality Disorder": 1.0
#     }
    
#     # this all is tunable
#     DEFAULT_CONFIG = {
#         "daily_decay_rate": 0.02, # 2% daily reduction - conservative decay
#         "query_decay_rate": 0.3,  # Moderate sentiment influence - tunable
#         "seven_day_retention": 0.7, # 7-day retention - tunable
#         "similarity_weight": 1.0,
#         "sentiment_weight": 0.8,
#         "evidence_boost": {"1": 0.7, "2-3": 1.0, "4+": 1.2},
#         "sentiment_impact": 2.0,
#         "similarity_threshold": 0.3,
#         "sentiment_threshold": 0.5,
#         "context_dampening": {
#             "personal": 1.0,      # Full impact for personal experiences 
#             "general": 0.3,       # Reduced impact for general discussions
#             "question": 0.4,      # Increased - questions can indicate concern
#             "academic": 0.2      # Almost no impact for academic queries
#         }
#     }
    
#     def __init__(self, config: Optional[Dict[str, Any]] = None):
#         """Initialize calculator with optional configuration."""
#         self.config = {**self.DEFAULT_CONFIG, **(config or {})}
    
#     def _validate_inputs(self, intensity_score, personal_relevance):
#         """Validate and fix input parameters"""
#         if not 0 <= personal_relevance <= 1:
#             personal_relevance = 1.0
#         if "pos" not in intensity_score:
#             intensity_score = {"pos": 0.33, "neg": 0.33, "neu": 0.34, "context_type": "personal", "personal_relevance": 1.0}
#         return intensity_score, personal_relevance
    
#     def calculate_scores(
#         self,
#         user_id: str,
#         top_k_results: List[Dict[str, Any]], 
#         intensity_score: Dict[str, Any],
#         current_scores: Optional[Dict[str, float]] = None,
#         decay_scores: Optional[Dict[str, float]] = None,
#         last_update_timestamp: Optional[str] = None
#     ) -> Tuple[Dict[str, float], Dict[str, float], str, float]:
#         """
#         Calculate updated mental health scores for a user.
        
#         Args:
#             user_id: Unique identifier for the user
#             top_k_results: List of filtered search results with similarity scores and labels
#             intensity_score: Sentiment scores (pos, neg, neu) + context info
#             current_scores: Current scores for all labels (0-100)
#             decay_scores: Decay rates for each label
#             last_update_timestamp: ISO timestamp of last update
            
#         Returns:
#             Tuple containing:
#             - Updated scores dict
#             - Updated decay scores dict  
#             - Current timestamp
#             - Overall risk score (calc_result)
#         """
#          # Validate inputs first
#         personal_relevance = intensity_score.get("personal_relevance", 1.0)
#         intensity_score, personal_relevance = self._validate_inputs(intensity_score, personal_relevance)
        
#         # Initialize defaults
#         current_scores = current_scores or {label: 0.0 for label in self.MENTAL_HEALTH_LABELS}
#         decay_scores = decay_scores or self.DEFAULT_DECAY_SCORES.copy()
        
#         # Apply time-based decay
#         current_scores = self._apply_time_decay(current_scores, last_update_timestamp)
        
#         # Apply per-query decay
#         current_scores = self._apply_query_decay(current_scores)
        
#         # Calculate evidence strength
#         evidence_strength = self._calculate_evidence_strength(len(top_k_results))
        
#         # Calculate context dampening factor
#         context_dampening = self._calculate_context_dampening(intensity_score)
        
#         # Process search results or sentiment-only updates
#         if top_k_results:
#             current_scores = self._process_search_results(
#                 current_scores, top_k_results, intensity_score, evidence_strength, context_dampening
#             )
#         else:
#             # Sentiment-only updates when no search results
#             current_scores = self._apply_sentiment_only_updates(current_scores, intensity_score, context_dampening)
        
#         # Apply normal score balancing
#         current_scores = self._balance_normal_score(current_scores)
        
#         # Cap all scores at 0-100
#         current_scores = self._cap_scores(current_scores)
        
#         # Update adaptive decay scores
#         decay_scores = self._update_decay_scores(decay_scores, current_scores)
        
#         # Calculate overall risk score (all negative labels)
#         negative_labels = ["Depression", "Suicidal", "Anxiety", "Stress", "Bi-Polar", "Personality Disorder"]
#         calc_result = sum(current_scores[label] for label in negative_labels) / len(negative_labels)
        
#         # Current timestamp
#         current_time = datetime.now().isoformat()
        
#         return current_scores, decay_scores, current_time, calc_result
    
#     def _calculate_context_dampening(self, intensity_score: Dict[str, Any]) -> float:
#         """Calculate context dampening factor based on query type and personal relevance."""
#         context_type = intensity_score.get("context_type", "personal")
#         personal_relevance = intensity_score.get("personal_relevance", 1.0)
        
#         # Get base dampening for context type
#         base_dampening = self.config["context_dampening"].get(context_type, 1.0)
        
#         # Apply personal relevance multiplier
#         final_dampening = base_dampening * personal_relevance
        
#         return final_dampening
    
#     def _apply_time_decay(self, scores: Dict[str, float], last_update: Optional[str]) -> Dict[str, float]:
#         """Apply time-based decay (daily + 7-day retention)."""
#         if not last_update:
#             return scores
            
#         try:
#             last_time = datetime.fromisoformat(last_update)
#             current_time = datetime.now()
#             days_passed = (current_time - last_time).days
            
#             if days_passed > 0:
#                 for label in self.MENTAL_HEALTH_LABELS:
#                     # Daily decay
#                     daily_decay = scores[label] * self.config["daily_decay_rate"] * days_passed
                    
#                     # 7-day retention decay
#                     if days_passed >= 7:
#                         retention_decay = scores[label] * (1 - self.config["seven_day_retention"])
#                         scores[label] = max(0, scores[label] - daily_decay - retention_decay)
#                     else:
#                         scores[label] = max(0, scores[label] - daily_decay)
#         except (ValueError, TypeError):
#             # Invalid timestamp, skip time decay
#             pass
            
#         return scores
    
#     def _apply_query_decay(self, scores: Dict[str, float]) -> Dict[str, float]:
#         """Apply per-query decay."""
#         decay_rate = self.config["query_decay_rate"]
#         return {label: score * (1 - decay_rate) for label, score in scores.items()}
    
#     def _calculate_evidence_strength(self, result_count: int) -> float:
#         """Calculate evidence strength multiplier based on result count."""
#         if result_count == 1:
#             return self.config["evidence_boost"]["1"]
#         elif 2 <= result_count <= 3:
#             return self.config["evidence_boost"]["2-3"]
#         elif result_count >= 4:
#             return self.config["evidence_boost"]["4+"]
#         return 1.0
    
#     def _process_search_results(
#         self, 
#         scores: Dict[str, float], 
#         results: List[Dict[str, Any]], 
#         sentiment: Dict[str, Any],
#         evidence_strength: float,
#         context_dampening: float
#     ) -> Dict[str, float]:
#         """Process search results and update scores based on similarity, sentiment, and context."""
#         label_impacts = {label: 0.0 for label in self.MENTAL_HEALTH_LABELS}
        
#         for result in results:
#             similarity = result.get("similarity_score", 0.0)
#             label = result.get("label", "")
            
#             # Skip low similarity results
#             if similarity < self.config["similarity_threshold"]:
#                 continue
                
#             if label in self.MENTAL_HEALTH_LABELS:
#                 # Calculate base impact
#                 base_impact = similarity * self.config["similarity_weight"] * evidence_strength
                
#                 # Apply sentiment modifier
#                 if label == "Normal":
#                     # Positive sentiment boosts Normal score
#                     sentiment_modifier = (sentiment["pos"] + sentiment["neu"] * 0.5) * self.config["sentiment_weight"]
#                 else:
#                     # Negative sentiment boosts negative mental health labels
#                     sentiment_modifier = sentiment["neg"] * self.config["sentiment_weight"]
                
#                 # FIXED: Less aggressive context dampening
#                 final_impact = base_impact * sentiment_modifier * min(1.0, context_dampening + 0.5) * 15
#                 label_impacts[label] += final_impact
        
#         # Update scores with calculated impacts
#         for label, impact in label_impacts.items():
#             scores[label] = min(100.0, scores[label] + impact)
            
#         return scores
    
#     def _apply_sentiment_only_updates(
#         self, 
#         scores: Dict[str, float], 
#         sentiment: Dict[str, Any],
#         context_dampening: float
#     ) -> Dict[str, float]:
#         """Apply sentiment-based updates when no search results available."""
#         sentiment_impact = self.config["sentiment_impact"] * context_dampening
#         threshold = self.config["sentiment_threshold"]
        
#         if sentiment["pos"] > threshold:  # Positive sentiment
#             # Boost Normal score
#             scores["Normal"] = min(100.0, scores["Normal"] + sentiment_impact)
#             # Reduce negative labels slightly
#             for label in ["Depression", "Anxiety", "Stress", "Suicidal"]:  # ← Added Suicidal
#                 scores[label] = max(0.0, scores[label] - sentiment_impact * 0.3)
                
#         elif sentiment["neg"] > threshold:  # Negative sentiment
#             # FIXED: Include Suicidal in negative sentiment updates
#             for label in ["Depression", "Anxiety", "Stress", "Suicidal"]:  # ← Added Suicidal
#                 scores[label] = min(100.0, scores[label] + sentiment_impact * 0.5)
#             # Reduce Normal score
#             scores["Normal"] = max(0.0, scores["Normal"] - sentiment_impact * 0.2)
        
#         return scores
    
#     def _balance_normal_score(self, scores: Dict[str, float]) -> Dict[str, float]:
#         """Balance Normal score based on negative label totals."""
#         negative_labels = [label for label in self.MENTAL_HEALTH_LABELS if label != "Normal"]
#         negative_total = sum(scores[label] for label in negative_labels)
        
#         # Adjusted thresholds based on 6 negative labels (max 600 total)
#         if negative_total < 100:  # Low negative labels -> boost Normal
#             normal_boost = (100 - negative_total) * 0.1
#             scores["Normal"] = min(100.0, scores["Normal"] + normal_boost)
#         elif negative_total > 300:  # High negative labels -> reduce Normal
#             normal_reduction = (negative_total - 300) * 0.05
#             scores["Normal"] = max(0.0, scores["Normal"] - normal_reduction)
        
#         return scores
    
#     def _cap_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
#         """Cap all scores between 0 and 100."""
#         return {label: max(0.0, min(100.0, score)) for label, score in scores.items()}
    
#     def _update_decay_scores(
#         self, 
#         decay_scores: Dict[str, float], 
#         current_scores: Dict[str, float]
#     ) -> Dict[str, float]:
#         """Update decay scores adaptively based on current values."""
#         updated_decay = decay_scores.copy()
        
#         for label in self.MENTAL_HEALTH_LABELS:
#             if current_scores[label] > 80:  # High scores decay slower (persistent conditions)
#                 updated_decay[label] = decay_scores[label] * 0.8
#             elif current_scores[label] < 20:  # Low scores decay faster (quick recovery)
#                 updated_decay[label] = decay_scores[label] * 1.2
                
#         return updated_decay

# mental_health_calculator.py

"""
PROOF OF CONCEPT - NOT FOR CLINICAL USE
This system is for demonstration purposes only.
Mental health assessment requires professional evaluation.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class MentalHealthCalculator:
    """
    A comprehensive calculator for tracking mental health scores with decay mechanisms.
    
    Supports 7 mental health labels with configurable weights, decay rates, 
    sentiment-based adjustments, and context filtering.
    """
    
    MENTAL_HEALTH_LABELS = [
        "Normal", "Depression", "Suicidal", "Anxiety", 
        "Stress", "Bi-Polar", "Personality Disorder"
    ]
    
    DEFAULT_DECAY_SCORES = {
        "Normal": 2.0, "Depression": 1.5, "Suicidal": 3.0, "Anxiety": 2.2,
        "Stress": 2.8, "Bi-Polar": 1.2, "Personality Disorder": 1.0
    }
    
    # FIXED: More balanced configuration
    DEFAULT_CONFIG = {
        "daily_decay_rate": 0.02,     # 2% daily reduction - conservative decay
        "query_decay_rate": 0.15,     # REDUCED from 0.3 - less aggressive decay
        "seven_day_retention": 0.7,   # 7-day retention - tunable
        "similarity_weight": 1.0,
        "sentiment_weight": 1.2,      # INCREASED from 0.8 - higher sentiment impact
        "evidence_boost": {"1": 0.7, "2-3": 1.0, "4+": 1.2},
        "sentiment_impact": 3.0,      # INCREASED from 2.0
        "similarity_threshold": 0.2,  # REDUCED from 0.3 - more inclusive
        "sentiment_threshold": 0.4,   # REDUCED from 0.5
        "context_dampening": {
            "personal": 1.0,          # Full impact for personal experiences 
            "general": 0.6,           # INCREASED from 0.3
            "question": 0.7,          # INCREASED from 0.4 - questions indicate concern
            "academic": 0.3           # INCREASED from 0.2
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize calculator with optional configuration."""
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
    
    def _validate_inputs(self, intensity_score, personal_relevance):
        """IMPROVED: Better input validation"""
        # Fix personal_relevance
        if not 0 <= personal_relevance <= 1:
            personal_relevance = 1.0
        
        # Fix intensity_score structure
        if "pos" not in intensity_score:
            intensity_score = {
                "pos": 0.33, "neg": 0.33, "neu": 0.34, 
                "context_type": "personal", "personal_relevance": 1.0
            }
        
        # Ensure sentiment scores are valid
        pos = intensity_score.get("pos", 0.33)
        neg = intensity_score.get("neg", 0.33)
        neu = intensity_score.get("neu", 0.34)
        
        # Validate sentiment scores
        total_sentiment = pos + neg + neu
        if abs(total_sentiment - 1.0) > 0.1:  # Allow small tolerance
            print(f"WARNING: Sentiment scores sum to {total_sentiment}, not 1.0")
            # Normalize if needed
            if total_sentiment > 0:
                intensity_score["pos"] = pos / total_sentiment
                intensity_score["neg"] = neg / total_sentiment
                intensity_score["neu"] = neu / total_sentiment
        
        # Set default context if missing
        if "context_type" not in intensity_score:
            intensity_score["context_type"] = "personal"
        if "personal_relevance" not in intensity_score:
            intensity_score["personal_relevance"] = personal_relevance
        
        return intensity_score, personal_relevance
    
    def calculate_scores(
        self,
        user_id: str,
        top_k_results: List[Dict[str, Any]], 
        intensity_score: Dict[str, Any],
        current_scores: Optional[Dict[str, float]] = None,
        decay_scores: Optional[Dict[str, float]] = None,
        last_update_timestamp: Optional[str] = None
    ) -> Tuple[Dict[str, float], Dict[str, float], str, float]:
        """
        FIXED: Calculate updated mental health scores for a user.
        
        Args:
            user_id: Unique identifier for the user
            top_k_results: List of filtered search results with similarity scores and labels
            intensity_score: Sentiment scores (pos, neg, neu) + context info
            current_scores: Current scores for all labels (0-100)
            decay_scores: Decay rates for each label
            last_update_timestamp: ISO timestamp of last update
            
        Returns:
            Tuple containing:
            - Updated scores dict
            - Updated decay scores dict  
            - Current timestamp
            - Overall risk score (calc_result)
        """
        # Validate inputs first
        personal_relevance = intensity_score.get("personal_relevance", 1.0)
        intensity_score, personal_relevance = self._validate_inputs(intensity_score, personal_relevance)
        
        # Initialize defaults
        current_scores = current_scores or {label: 0.0 for label in self.MENTAL_HEALTH_LABELS}
        decay_scores = decay_scores or self.DEFAULT_DECAY_SCORES.copy()
        
        print(f"BEFORE processing - scores: {current_scores}")
        
        # Apply time-based decay
        current_scores = self._apply_time_decay(current_scores, last_update_timestamp)
        print(f"AFTER time decay - scores: {current_scores}")
        
        # FIXED: Process search results BEFORE applying query decay
        if top_k_results:
            # Calculate context dampening and evidence strength
            evidence_strength = self._calculate_evidence_strength(len(top_k_results))
            context_dampening = self._calculate_context_dampening(intensity_score)
            
            print(f"Evidence strength: {evidence_strength}")
            print(f"Context dampening: {context_dampening}")
            
            # Process search results first
            current_scores = self._process_search_results(
                current_scores, top_k_results, intensity_score, evidence_strength, context_dampening
            )
            print(f"AFTER search results - scores: {current_scores}")
        
        # FIXED: Apply query decay AFTER processing results (and make it gentler)
        current_scores = self._apply_query_decay(current_scores)
        print(f"AFTER query decay - scores: {current_scores}")
        
        # Sentiment-only updates when no search results
        if not top_k_results:
            context_dampening = self._calculate_context_dampening(intensity_score)
            current_scores = self._apply_sentiment_only_updates(current_scores, intensity_score, context_dampening)
            print(f"AFTER sentiment-only - scores: {current_scores}")
        
        # Apply normal score balancing
        current_scores = self._balance_normal_score(current_scores)
        
        # Cap all scores at 0-100
        current_scores = self._cap_scores(current_scores)
        
        # Update adaptive decay scores
        decay_scores = self._update_decay_scores(decay_scores, current_scores)
        
        # Calculate overall risk score (all negative labels)
        negative_labels = ["Depression", "Suicidal", "Anxiety", "Stress", "Bi-Polar", "Personality Disorder"]
        calc_result = sum(current_scores[label] for label in negative_labels) / len(negative_labels)
        
        print(f"FINAL scores: {current_scores}")
        print(f"FINAL calc_result: {calc_result}")
        
        # Current timestamp
        current_time = datetime.now().isoformat()
        
        return current_scores, decay_scores, current_time, calc_result
    
    def _calculate_context_dampening(self, intensity_score: Dict[str, Any]) -> float:
        """FIXED: Less aggressive context dampening"""
        context_type = intensity_score.get("context_type", "personal")
        personal_relevance = intensity_score.get("personal_relevance", 1.0)
        
        print(f"Context type: {context_type}, Personal relevance: {personal_relevance}")
        
        # Get base dampening for context type
        base_dampening = self.config["context_dampening"].get(context_type, 1.0)
        
        # FIXED: Apply personal relevance more gently
        final_dampening = base_dampening * personal_relevance
        
        # FIXED: Minimum dampening to ensure some impact always gets through
        final_dampening = max(0.4, final_dampening)  # At least 40% impact
        
        print(f"Base dampening: {base_dampening}, Final dampening: {final_dampening}")
        return final_dampening
    
    def _apply_time_decay(self, scores: Dict[str, float], last_update: Optional[str]) -> Dict[str, float]:
        """Apply time-based decay (daily + 7-day retention)."""
        if not last_update:
            return scores
            
        try:
            last_time = datetime.fromisoformat(last_update)
            current_time = datetime.now()
            days_passed = (current_time - last_time).days
            
            if days_passed > 0:
                for label in self.MENTAL_HEALTH_LABELS:
                    # Daily decay
                    daily_decay = scores[label] * self.config["daily_decay_rate"] * days_passed
                    
                    # 7-day retention decay
                    if days_passed >= 7:
                        retention_decay = scores[label] * (1 - self.config["seven_day_retention"])
                        scores[label] = max(0, scores[label] - daily_decay - retention_decay)
                    else:
                        scores[label] = max(0, scores[label] - daily_decay)
        except (ValueError, TypeError):
            # Invalid timestamp, skip time decay
            pass
            
        return scores
    
    def _apply_query_decay(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Apply per-query decay."""
        decay_rate = self.config["query_decay_rate"]
        return {label: score * (1 - decay_rate) for label, score in scores.items()}
    
    def _calculate_evidence_strength(self, result_count: int) -> float:
        """Calculate evidence strength multiplier based on result count."""
        if result_count == 1:
            return self.config["evidence_boost"]["1"]
        elif 2 <= result_count <= 3:
            return self.config["evidence_boost"]["2-3"]
        elif result_count >= 4:
            return self.config["evidence_boost"]["4+"]
        return 1.0
    
    def _process_search_results(
        self, 
        scores: Dict[str, float], 
        results: List[Dict[str, Any]], 
        sentiment: Dict[str, Any],
        evidence_strength: float,
        context_dampening: float
    ) -> Dict[str, float]:
        """FIXED: More aggressive impact calculation for critical cases"""
        label_impacts = {label: 0.0 for label in self.MENTAL_HEALTH_LABELS}
        
        print(f"Processing {len(results)} search results...")
        
        for i, result in enumerate(results):
            similarity = result.get("similarity_score", 0.0)
            label = result.get("label", "")
            
            print(f"Result {i}: {label}, similarity: {similarity:.3f}")
            
            # Skip low similarity results
            if similarity < self.config["similarity_threshold"]:
                print(f"  SKIPPED: Below threshold {self.config['similarity_threshold']}")
                continue
                
            if label in self.MENTAL_HEALTH_LABELS:
                # Calculate base impact
                base_impact = similarity * self.config["similarity_weight"] * evidence_strength
                print(f"  Base impact: {base_impact:.3f}")
                
                # Apply sentiment modifier
                if label == "Normal":
                    sentiment_modifier = (sentiment["pos"] + sentiment["neu"] * 0.5) * self.config["sentiment_weight"]
                else:
                    sentiment_modifier = sentiment["neg"] * self.config["sentiment_weight"]
                
                print(f"  Sentiment modifier: {sentiment_modifier:.3f}")
                
                # FIXED: Special handling for critical cases + less aggressive dampening
                if label == "Suicidal" and sentiment["neg"] > 0.7:  # Critical suicidal content
                    # Bypass most context dampening for critical cases
                    final_impact = base_impact * sentiment_modifier * max(0.8, context_dampening) * 30  # Higher multiplier
                    print(f"  CRITICAL SUICIDAL - Enhanced impact: {final_impact:.3f}")
                elif label in ["Depression", "Anxiety", "Stress"] and sentiment["neg"] > 0.6:
                    # Moderate boost for other negative labels with high negative sentiment
                    final_impact = base_impact * sentiment_modifier * max(0.6, context_dampening) * 20
                    print(f"  HIGH NEGATIVE - Enhanced impact: {final_impact:.3f}")
                else:
                    # Standard calculation with improved baseline
                    final_impact = base_impact * sentiment_modifier * context_dampening * 18  # Increased from 15
                    print(f"  Standard impact: {final_impact:.3f}")
                
                label_impacts[label] += final_impact
                print(f"  Total {label} impact: {label_impacts[label]:.3f}")
        
        # Update scores with calculated impacts
        print(f"Applying impacts: {label_impacts}")
        for label, impact in label_impacts.items():
            old_score = scores[label]
            scores[label] = min(100.0, scores[label] + impact)
            if impact > 0:
                print(f"  {label}: {old_score:.2f} + {impact:.2f} = {scores[label]:.2f}")
            
        return scores
    
    def _apply_sentiment_only_updates(
        self, 
        scores: Dict[str, float], 
        sentiment: Dict[str, Any],
        context_dampening: float
    ) -> Dict[str, float]:
        """FIXED: Apply sentiment-based updates when no search results available."""
        sentiment_impact = self.config["sentiment_impact"] * context_dampening
        threshold = self.config["sentiment_threshold"]
        
        print(f"Applying sentiment-only updates: impact={sentiment_impact:.3f}, threshold={threshold}")
        
        if sentiment["pos"] > threshold:  # Positive sentiment
            # Boost Normal score
            boost = sentiment_impact * sentiment["pos"]
            scores["Normal"] = min(100.0, scores["Normal"] + boost)
            print(f"  Positive boost to Normal: +{boost:.2f}")
            
            # Reduce negative labels slightly
            reduction = sentiment_impact * 0.3 * sentiment["pos"]
            for label in ["Depression", "Anxiety", "Stress", "Suicidal"]:
                scores[label] = max(0.0, scores[label] - reduction)
                print(f"  Positive reduction to {label}: -{reduction:.2f}")
                
        elif sentiment["neg"] > threshold:  # Negative sentiment
            # FIXED: Include Suicidal in negative sentiment updates with special handling
            base_boost = sentiment_impact * 0.6 * sentiment["neg"]
            
            for label in ["Depression", "Anxiety", "Stress"]:
                scores[label] = min(100.0, scores[label] + base_boost)
                print(f"  Negative boost to {label}: +{base_boost:.2f}")
            
            # Special handling for Suicidal - higher impact if very negative
            if sentiment["neg"] > 0.7:
                suicidal_boost = sentiment_impact * 0.8 * sentiment["neg"]  # Higher multiplier
                scores["Suicidal"] = min(100.0, scores["Suicidal"] + suicidal_boost)
                print(f"  HIGH negative boost to Suicidal: +{suicidal_boost:.2f}")
            else:
                scores["Suicidal"] = min(100.0, scores["Suicidal"] + base_boost)
                print(f"  Standard negative boost to Suicidal: +{base_boost:.2f}")
            
            # Reduce Normal score
            normal_reduction = sentiment_impact * 0.2 * sentiment["neg"]
            scores["Normal"] = max(0.0, scores["Normal"] - normal_reduction)
            print(f"  Negative reduction to Normal: -{normal_reduction:.2f}")
        
        return scores
    
    def _balance_normal_score(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Balance Normal score based on negative label totals."""
        negative_labels = [label for label in self.MENTAL_HEALTH_LABELS if label != "Normal"]
        negative_total = sum(scores[label] for label in negative_labels)
        
        # Adjusted thresholds based on 6 negative labels (max 600 total)
        if negative_total < 50:  # REDUCED threshold - Low negative labels -> boost Normal
            normal_boost = (50 - negative_total) * 0.15  # Increased multiplier
            scores["Normal"] = min(100.0, scores["Normal"] + normal_boost)
            print(f"Normal balancing boost: +{normal_boost:.2f}")
        elif negative_total > 200:  # REDUCED threshold - High negative labels -> reduce Normal
            normal_reduction = (negative_total - 200) * 0.08  # Increased multiplier
            scores["Normal"] = max(0.0, scores["Normal"] - normal_reduction)
            print(f"Normal balancing reduction: -{normal_reduction:.2f}")
        
        return scores
    
    def _cap_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Cap all scores between 0 and 100."""
        return {label: max(0.0, min(100.0, score)) for label, score in scores.items()}
    
    def _update_decay_scores(
        self, 
        decay_scores: Dict[str, float], 
        current_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Update decay scores adaptively based on current values."""
        updated_decay = decay_scores.copy()
        
        for label in self.MENTAL_HEALTH_LABELS:
            if current_scores[label] > 80:  # High scores decay slower (persistent conditions)
                updated_decay[label] = decay_scores[label] * 0.8
            elif current_scores[label] < 20:  # Low scores decay faster (quick recovery)
                updated_decay[label] = decay_scores[label] * 1.2
                
        return updated_decay