"""Main post-processor class that coordinates all processing components."""

from typing import Dict, Any, Optional, Union
import logging
import time
from matrice.deploy.utils.post_processing.category_mapper import CategoryMapper
from matrice.deploy.utils.post_processing.alerting_processor import AlertingProcessor
from matrice.deploy.utils.post_processing.tracking_processor import TrackingProcessor
from matrice.deploy.utils.post_processing.counting_processor import CountingProcessor
from matrice.deploy.utils.post_processing.utils import match_results_structure
from matrice.deploy.utils.post_processing.config import (
    PostProcessingConfig,
    TrackingConfig,
    CountingConfig,
    AlertingConfig,
)


class PostProcessor:
    """Main post-processing class that coordinates all processing components."""

    def __init__(
        self,
        config: Union[PostProcessingConfig, Dict[str, Any]],
        index_to_category: Dict[int, str] = None,
        map_index_to_category: bool = True,
    ):
        """Initialize PostProcessor with PostProcessingConfig.

        Args:
            config: PostProcessingConfig instance with all configuration settings
        """
        if isinstance(config, dict):
            self.config = PostProcessingConfig.from_dict(config)
        else:
            self.config = config

        # Initialize component processors with their respective configs
        self.category_mapper = None
        if map_index_to_category:
            if index_to_category:
                self.category_mapper = CategoryMapper(index_to_category)
            else:
                logging.warning(
                    "map_index_to_category is True but index_to_category is empty, category mapping will not work"
                )
        else:
            logging.warning(
                "map_index_to_category is True but index_to_category is empty, category mapping will not work"
            )

        self.alerting_processor = AlertingProcessor(self.config.alerting)
        self.tracking_processor = TrackingProcessor(self.config.tracking)
        self.counting_processor = CountingProcessor(self.config.counting)

    def process(
        self, results: Any, config: Optional[PostProcessingConfig] = None
    ) -> Dict[str, Any]:
        """Main processing function that applies configured post-processing steps."""
        # Use passed config or fall back to instance config
        active_config = config if config is not None else self.config

        if not isinstance(active_config, PostProcessingConfig):
            raise TypeError(f"Expected PostProcessingConfig, got {type(active_config)}")

        # Update category mapper if needed
        if self.config.map_index_to_category and self.config.index_to_category:
            self.category_mapper = CategoryMapper(self.config.index_to_category)
        elif self.config.map_index_to_category and not self.config.index_to_category:
            logging.warning(
                "map_index_to_category is True but index_to_category is empty, category mapping will not work"
            )

        # Determine result structure type
        result_type = match_results_structure(results)

        # Initialize processed results
        processed_results = {
            "original_results": results,
            "result_type": result_type,
            "processed_data": results,
            "metadata": {},
        }

        # Apply confidence filtering from alerting config
        if (
            active_config.alerting.enable_alerting
            and active_config.alerting.category_threshold
        ):
            confidence_threshold = self._get_confidence_threshold(
                active_config.alerting.category_threshold
            )
            if confidence_threshold > 0:
                processed_results["processed_data"] = (
                    self.alerting_processor.filter_by_confidence(
                        processed_results["processed_data"], confidence_threshold
                    )
                )
                processed_results["metadata"]["confidence_filtered"] = True

        # Apply category mapping
        if self.category_mapper:
            processed_results["processed_data"] = self.category_mapper.map_results(
                processed_results["processed_data"]
            )
            processed_results["metadata"]["category_mapping_applied"] = True

        # Apply tracking features
        if active_config.tracking.enable_tracking:
            processed_results = self._apply_tracking_features(
                processed_results, active_config.tracking
            )

        # Apply counting features
        if active_config.counting.enable_counting:
            processed_results = self._apply_counting_features(
                processed_results, active_config.counting
            )

        # Apply alerting features
        if active_config.alerting.enable_alerting:
            processed_results = self._apply_alerting_features(
                processed_results, active_config.alerting
            )

        # Ensure consistent return format with processed_data key
        if (
            isinstance(processed_results, dict)
            and "processed_data" in processed_results
        ):
            return processed_results
        else:
            return {
                "processed_data": (
                    processed_results.get("results", results)
                    if isinstance(processed_results, dict)
                    else results
                ),
                "metadata": (
                    processed_results if isinstance(processed_results, dict) else {}
                ),
                "status": "success",
            }

    def _get_confidence_threshold(self, category_threshold: Dict[str, float]) -> float:
        """Extract confidence threshold from category threshold configuration."""
        if "all" in category_threshold:
            return category_threshold["all"]
        elif category_threshold:
            return min(category_threshold.values())
        return 0.0

    def _apply_tracking_features(
        self, processed_results: Dict, tracking_config: TrackingConfig = None
    ) -> Dict:
        """Apply tracking-related post-processing features."""
        results = processed_results["processed_data"]

        # Zone tracking
        if tracking_config and tracking_config.tracking_zones:
            zone_tracking = {}
            for zone_name, zone_polygon in tracking_config.tracking_zones.items():
                if isinstance(results, list):
                    zone_tracking[zone_name] = self.tracking_processor.track_in_zone(
                        results, zone_polygon
                    )
            processed_results["zone_tracking"] = zone_tracking

        # Line crossing detection
        if tracking_config and tracking_config.crossing_lines:
            line_crossings = {}
            for line_name, line_points in tracking_config.crossing_lines.items():
                line_crossings[line_name] = (
                    self.tracking_processor.detect_line_crossing(results, line_points)
                )
            processed_results["line_crossings"] = line_crossings

        return processed_results

    def _apply_counting_features(
        self, processed_results: Dict, counting_config: CountingConfig = None
    ) -> Dict:
        """Apply counting-related post-processing features."""
        results = processed_results["processed_data"]
        identification_keys = counting_config.identification_keys or ["track_id"]

        # Basic object counting with timestamp support
        current_timestamp = time.time()
        results, count_metadata = self.counting_processor.count_objects(
            results, identification_keys, current_timestamp
        )
        processed_results["count_metadata"] = count_metadata

        # Zone-based counting
        if counting_config and counting_config.count_rules:
            processed_results["count_rules_applied"] = counting_config.count_rules
        
        # Add counting statistics if time-based counting is enabled
        if (counting_config and 
            counting_config.count_rules and 
            counting_config.count_rules.get("enable_time_based_counting", False)):
            processed_results["counting_statistics"] = self.counting_processor.get_counting_statistics(current_timestamp)

        return processed_results

    def _apply_alerting_features(
        self, processed_results: Dict, alerting_config: AlertingConfig = None
    ) -> Dict:
        """Apply alerting-related post-processing features."""
        results = processed_results["processed_data"]

        # Prepare event configuration
        event_config = {}

        # Add count thresholds
        if alerting_config and alerting_config.category_count_threshold:
            if "all" in alerting_config.category_count_threshold:
                event_config["count_threshold"] = (
                    alerting_config.category_count_threshold["all"]
                )

            # Category-specific triggers
            category_triggers = [
                cat
                for cat in alerting_config.category_count_threshold.keys()
                if cat != "all"
            ]
            if category_triggers:
                event_config["category_triggers"] = category_triggers

        # Add specific category triggers
        if alerting_config and alerting_config.category_triggers:
            event_config.setdefault("category_triggers", []).extend(
                alerting_config.category_triggers
            )

        # Trigger events based on configuration
        if event_config:
            triggered_events = self.alerting_processor.trigger_events(
                results, event_config
            )
            processed_results["triggered_events"] = triggered_events

        return processed_results
