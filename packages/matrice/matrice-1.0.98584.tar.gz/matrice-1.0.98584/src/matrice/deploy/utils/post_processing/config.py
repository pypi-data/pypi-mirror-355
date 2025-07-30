"""Configuration examples and templates for post-processing."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class AlertingConfig:
    """Configuration for alerting functionality."""
    enable_alerting: bool = False
    category_threshold: Dict[str, float] = field(default_factory=dict)
    category_count_threshold: Dict[str, int] = field(default_factory=dict)
    category_triggers: List[str] = field(default_factory=list)


@dataclass
class TrackingConfig:
    """Configuration for tracking functionality."""
    enable_tracking: bool = False
    tracking_zones: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    crossing_lines: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)


@dataclass
class CountingConfig:
    """Configuration for counting functionality."""
    enable_counting: bool = False
    identification_keys: List[str] = field(default_factory=list)
    count_rules: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_time_based_config(
        cls,
        enable_counting: bool = True,
        identification_keys: List[str] = None,
        time_window_seconds: int = 3600,
        track_expiry_seconds: int = 300,
        enable_time_based_counting: bool = True,
        report_time_window_only: bool = False,
        unique_by_track: bool = True,
        enable_bbox_deduplication: bool = True,
        bbox_similarity_threshold: float = 0.8,
        **additional_rules
    ):
        """Create a CountingConfig with time-based counting settings and bbox deduplication."""
        if identification_keys is None:
            identification_keys = ["track_id"]
        
        count_rules = {
            "time_window_seconds": time_window_seconds,
            "track_expiry_seconds": track_expiry_seconds,
            "enable_time_based_counting": enable_time_based_counting,
            "report_time_window_only": report_time_window_only,
            "unique_by_track": unique_by_track,
            "enable_bbox_deduplication": enable_bbox_deduplication,
            "bbox_similarity_threshold": bbox_similarity_threshold,
            **additional_rules
        }
        
        return cls(
            enable_counting=enable_counting,
            identification_keys=identification_keys,
            count_rules=count_rules
        )


@dataclass
class PostProcessingConfig:
    """Main post-processing configuration class with pythonic accessible data structure."""
    
    # Category mapping
    map_index_to_category: bool = False
    index_to_category: Dict[int, str] = field(default_factory=dict)
    
    # Sub-configurations
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    counting: CountingConfig = field(default_factory=CountingConfig)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PostProcessingConfig':
        """Create PostProcessingConfig from dictionary."""
        # Extract main level configs
        map_index_to_category = config_dict.get('map_index_to_category', False)
        index_to_category = config_dict.get('index_to_category', {})
        
        # Create alerting config
        alerting_dict = config_dict.get('alerting', {})
        alerting_config = AlertingConfig(
            enable_alerting=alerting_dict.get('enable_alerting', False),
            category_threshold=alerting_dict.get('category_threshold', {}),
            category_count_threshold=alerting_dict.get('category_count_threshold', {}),
            category_triggers=alerting_dict.get('category_triggers', [])
        )
        
        # Create tracking config
        tracking_dict = config_dict.get('tracking', {})
        tracking_config = TrackingConfig(
            enable_tracking=tracking_dict.get('enable_tracking', False),
            tracking_zones=tracking_dict.get('tracking_zones', {}),
            crossing_lines=tracking_dict.get('crossing_lines', {})
        )
        
        # Create counting config
        counting_dict = config_dict.get('counting', {})
        counting_config = CountingConfig(
            enable_counting=counting_dict.get('enable_counting', False),
            identification_keys=counting_dict.get('identification_keys', []),
            count_rules=counting_dict.get('count_rules', {})
        )
        
        return cls(
            map_index_to_category=map_index_to_category,
            index_to_category=index_to_category,
            alerting=alerting_config,
            tracking=tracking_config,
            counting=counting_config
        )
    
    @classmethod
    def from_params(
        cls,
        # Category mapping params
        map_index_to_category: bool = True,
        index_to_category: Optional[Dict[int, str]] = None,
        
        # Alerting params
        enable_alerting: bool = False,
        confidence_threshold: Optional[float] = None,
        category_thresholds: Optional[Dict[str, float]] = None,
        count_threshold: Optional[int] = None,
        category_count_thresholds: Optional[Dict[str, int]] = None,
        category_triggers: Optional[List[str]] = None,
        
        # Tracking params
        enable_tracking: bool = False,
        tracking_zones: Optional[Dict[str, List[Tuple[int, int]]]] = None,
        crossing_lines: Optional[Dict[str, List[Tuple[int, int]]]] = None,
        
        # Counting params
        enable_counting: bool = False,
        identification_keys: Optional[List[str]] = None,
        count_rules: Optional[Dict[str, Any]] = None,
    ) -> 'PostProcessingConfig':
        """Create PostProcessingConfig from individual parameters."""
        
        # Build category thresholds
        final_category_threshold = {}
        if category_thresholds:
            final_category_threshold.update(category_thresholds)
        elif confidence_threshold is not None:
            final_category_threshold["all"] = confidence_threshold
        
        # Build category count thresholds
        final_category_count_threshold = {}
        if category_count_thresholds:
            final_category_count_threshold.update(category_count_thresholds)
        elif count_threshold is not None:
            final_category_count_threshold["all"] = count_threshold
        
        # Create alerting config
        alerting_config = AlertingConfig(
            enable_alerting=enable_alerting,
            category_threshold=final_category_threshold,
            category_count_threshold=final_category_count_threshold,
            category_triggers=category_triggers or []
        )
        
        # Create tracking config
        tracking_config = TrackingConfig(
            enable_tracking=enable_tracking,
            tracking_zones=tracking_zones or {},
            crossing_lines=crossing_lines or {}
        )
        
        # Create counting config
        counting_config = CountingConfig(
            enable_counting=enable_counting,
            identification_keys=identification_keys or [],
            count_rules=count_rules or {}
        )
        
        return cls(
            map_index_to_category=map_index_to_category,
            index_to_category=index_to_category or {},
            alerting=alerting_config,
            tracking=tracking_config,
            counting=counting_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PostProcessingConfig to dictionary format."""
        config = {}
        
        # Category mapping
        if self.map_index_to_category or self.index_to_category:
            config["map_index_to_category"] = self.map_index_to_category
            if self.index_to_category:
                config["index_to_category"] = self.index_to_category
        
        # Alerting configuration
        if (self.alerting.enable_alerting or self.alerting.category_threshold or 
            self.alerting.category_count_threshold or self.alerting.category_triggers):
            config["alerting"] = {
                "enable_alerting": self.alerting.enable_alerting
            }
            if self.alerting.category_threshold:
                config["alerting"]["category_threshold"] = self.alerting.category_threshold
            if self.alerting.category_count_threshold:
                config["alerting"]["category_count_threshold"] = self.alerting.category_count_threshold
            if self.alerting.category_triggers:
                config["alerting"]["category_triggers"] = self.alerting.category_triggers
        
        # Tracking configuration
        if (self.tracking.enable_tracking or self.tracking.tracking_zones or 
            self.tracking.crossing_lines):
            config["tracking"] = {
                "enable_tracking": self.tracking.enable_tracking
            }
            if self.tracking.tracking_zones:
                config["tracking"]["tracking_zones"] = self.tracking.tracking_zones
            if self.tracking.crossing_lines:
                config["tracking"]["crossing_lines"] = self.tracking.crossing_lines
        
        # Counting configuration
        if (self.counting.enable_counting or self.counting.identification_keys or 
            self.counting.count_rules):
            config["counting"] = {
                "enable_counting": self.counting.enable_counting
            }
            if self.counting.identification_keys:
                config["counting"]["identification_keys"] = self.counting.identification_keys
            if self.counting.count_rules:
                config["counting"]["count_rules"] = self.counting.count_rules
        
        return config


# Example usage and configuration templates
EXAMPLE_CONFIGS = {
    "map_index_to_category": True,
    "index_to_category": {0: "car", 1: "truck", 2: "bus"},
    "alerting": {
        "enable_alerting": True,
        "category_threshold": {
            "all": 0.5,  # all categories
            "car": 0.5,
            "truck": 0.5,
            "bus": 0.5,
        },
        "category_count_threshold": {
            "all": 100,  # all categories
            "car": 100,
            "truck": 100,
            "bus": 100,
        },
    },
    "tracking": {
        "enable_tracking": True,
        "tracking_zones": {
            "parking_zone": [(100, 100), (200, 100), (200, 200), (100, 200)]
        },
        "crossing_lines": {"entrance_line": [(150, 50), (150, 250)]},
    },
    "counting": {"enable_counting": True, "identification_keys": ["track_id"]},
}

# For detection models - output: [{"bounding_box": {...}, "category": str, "confidence": float}, ...]
# For classification models - output: {"category": str, "confidence": float}
# For object tracking models - output: {"frame_id": [{"track_id": int, "category": str, ...}, ...]}
# For activity recognition models - output: {"frame_id": [{"category": str, "confidence": float, ...}, ...]}
# For instance segmentation models - same as detection but with masks


def create_post_processing_config(
    custom_config: Dict[str, Any] = None,
    enable_alerting: bool = False,
    confidence_threshold: Optional[float] = None,
    category_thresholds: Dict[str, float] = None,
    count_threshold: int = None,
    category_count_thresholds: Dict[str, int] = None,
    enable_tracking: bool = False,
    tracking_zones: Dict[str, List[Tuple[int, int]]] = None,
    crossing_lines: Dict[str, List[Tuple[int, int]]] = None,
    enable_counting: bool = False,
    identification_keys: List[str] = None,
    category_triggers: List[str] = None,
    count_rules: Dict[str, Any] = None,
    map_index_to_category: bool = True,
    index_to_category: Dict[int, str] = None
) -> PostProcessingConfig:
    """Create a post-processing configuration.
    
    This function creates a PostProcessingConfig that can be used directly with PostProcessor
    or InferenceInterface for post-processing model results.
    
    Args:
        custom_config: Custom post-processing configuration dictionary. If provided,
                      will be used to create PostProcessingConfig via from_dict().
        enable_alerting: Enable alerting/filtering features
        confidence_threshold: Global confidence threshold for filtering
        category_thresholds: Per-category confidence thresholds
        count_threshold: Threshold for triggering count-based alerts
        category_count_thresholds: Per-category count thresholds
        enable_tracking: Enable tracking features
        tracking_zones: Dictionary of zone_name -> polygon coordinates
        crossing_lines: Dictionary of line_name -> line coordinates
        enable_counting: Enable counting features
        identification_keys: Keys to use for object identification (e.g., ["track_id"])
        category_triggers: List of categories that should trigger alerts
        count_rules: Rules for counting behavior
        map_index_to_category: Whether to map category indices to strings
        index_to_category: Mapping from indices to category strings
        
    Returns:
        PostProcessingConfig instance that can be used with PostProcessor
        
    Examples:
        # Create custom configuration with specific parameters
        >>> config = create_post_processing_config(
        ...     enable_alerting=True,
        ...     confidence_threshold=0.7,
        ...     enable_counting=True,
        ...     identification_keys=["category"]
        ... )
        >>> processor = PostProcessor(config=config)
        
        # For InferenceInterface
        >>> interface = InferenceInterface(
        ...     model_manager=manager,
        ...     post_processing_config=create_post_processing_config()
        ... )   
    """
    # If custom_config is provided, use it to create PostProcessingConfig
    if custom_config:
        return PostProcessingConfig.from_dict(custom_config)
    
    # Build configuration from individual parameters using from_params
    return PostProcessingConfig.from_params(
        map_index_to_category=map_index_to_category,
        index_to_category=index_to_category,
        enable_alerting=enable_alerting,
        confidence_threshold=confidence_threshold,
        category_thresholds=category_thresholds,
        count_threshold=count_threshold,
        category_count_thresholds=category_count_thresholds,
        category_triggers=category_triggers,
        enable_tracking=enable_tracking,
        tracking_zones=tracking_zones,
        crossing_lines=crossing_lines,
        enable_counting=enable_counting,
        identification_keys=identification_keys,
        count_rules=count_rules
    )
