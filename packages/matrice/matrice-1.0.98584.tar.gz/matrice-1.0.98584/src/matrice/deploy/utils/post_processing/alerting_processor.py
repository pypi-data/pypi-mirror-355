"""Alerting and event triggering functionality for post-processing."""

from typing import List, Dict, Any
import time
from matrice.deploy.utils.post_processing.config import AlertingConfig


class AlertingProcessor:
    """Class for handling alerting and event triggering."""
    
    def __init__(self, config: AlertingConfig):
        """Initialize AlertingProcessor with AlertingConfig.
        
        Args:
            config: AlertingConfig instance with alerting configuration
        """
        if not isinstance(config, AlertingConfig):
            raise TypeError(f"Expected AlertingConfig, got {type(config)}")
        
        self.config = config
        self.alert_history = []
    
    def filter_by_confidence(self, results: Any, threshold: float) -> Any:
        """Filter results by confidence threshold."""
        if isinstance(results, list):
            return [r for r in results if r.get("confidence", 0) >= threshold]
        elif isinstance(results, dict):
            if "confidence" in results:
                return results if results["confidence"] >= threshold else {}
            else:
                # Handle frame-based results
                filtered = {}
                for frame_id, detections in results.items():
                    if isinstance(detections, list):
                        filtered[frame_id] = [d for d in detections if d.get("confidence", 0) >= threshold]
                return filtered
        return results
    
    def trigger_events(self, results: Any, event_config: Dict = None) -> List[Dict]:
        """Trigger events based on detection conditions.
        
        Args:
            results: Processing results to analyze
            event_config: Optional override event configuration (for backward compatibility)
        """
        triggered_events = []
        
        # Use config from AlertingConfig or override
        if event_config:
            # Backward compatibility mode
            count_threshold = event_config.get("count_threshold")
            category_triggers = event_config.get("category_triggers", [])
        else:
            # Use AlertingConfig
            count_threshold = self.config.category_count_threshold.get("all") if self.config.category_count_threshold else None
            category_triggers = self.config.category_triggers
        
        # Count-based triggers
        if count_threshold is not None:
            total_detections = self._count_total_detections(results)
            if total_detections >= count_threshold:
                event = {
                    "event_type": "count_threshold_exceeded",
                    "threshold": count_threshold,
                    "actual_count": total_detections,
                    "timestamp": time.time()
                }
                triggered_events.append(event)
                self.alert_history.append(event)
        
        # Category-based triggers
        if category_triggers:
            detected_categories = self._get_detected_categories(results)
            for trigger_category in category_triggers:
                if trigger_category in detected_categories:
                    event = {
                        "event_type": "category_detected",
                        "category": trigger_category,
                        "timestamp": time.time()
                    }
                    triggered_events.append(event)
                    self.alert_history.append(event)
        
        # Category-specific count thresholds
        if self.config.category_count_threshold:
            category_counts = self._count_by_category(results)
            for category, threshold in self.config.category_count_threshold.items():
                if category != "all" and category_counts.get(category, 0) >= threshold:
                    event = {
                        "event_type": "category_count_threshold_exceeded",
                        "category": category,
                        "threshold": threshold,
                        "actual_count": category_counts[category],
                        "timestamp": time.time()
                    }
                    triggered_events.append(event)
                    self.alert_history.append(event)
        
        return triggered_events
    
    def _count_total_detections(self, results: Any) -> int:
        """Count total detections in results."""
        total_detections = 0
        if isinstance(results, list):
            total_detections = len(results)
        elif isinstance(results, dict):
            for detections in results.values():
                if isinstance(detections, list):
                    total_detections += len(detections)
        return total_detections
    
    def _get_detected_categories(self, results: Any) -> set:
        """Get set of detected categories from results."""
        detected_categories = set()
        if isinstance(results, list):
            detected_categories.update(r.get("category", "") for r in results)
        elif isinstance(results, dict):
            for detections in results.values():
                if isinstance(detections, list):
                    detected_categories.update(d.get("category", "") for d in detections)
        return detected_categories
    
    def _count_by_category(self, results: Any) -> Dict[str, int]:
        """Count detections by category."""
        category_counts = {}
        if isinstance(results, list):
            for result in results:
                category = result.get("category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1
        elif isinstance(results, dict):
            for detections in results.values():
                if isinstance(detections, list):
                    for detection in detections:
                        category = detection.get("category", "unknown")
                        category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts 