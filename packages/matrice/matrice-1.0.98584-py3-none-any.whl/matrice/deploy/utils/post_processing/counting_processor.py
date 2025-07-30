"""Counting functionality for post-processing."""

import time
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict
from matrice.deploy.utils.post_processing.utils import match_results_structure
from matrice.deploy.utils.post_processing.config import CountingConfig


class CountingProcessor:
    """Class for handling object counting operations with time-based tracking."""
    
    def __init__(self, config: CountingConfig):
        """Initialize CountingProcessor with CountingConfig.
        
        Args:
            config: CountingConfig instance with counting configuration
        """
        if not isinstance(config, CountingConfig):
            raise TypeError(f"Expected CountingConfig, got {type(config)}")
        
        self.config = config
        self.zone_counters = defaultdict(int)
        self.dwell_times = defaultdict(dict)
        
        # Time-based tracking for incremental counting
        self.unique_tracks_seen = set()  # All unique track IDs ever seen
        self.track_timestamps = {}  # track_id -> first_seen_timestamp
        self.track_last_seen = {}  # track_id -> last_seen_timestamp
        self.zone_unique_tracks = defaultdict(set)  # zone_name -> set of unique track IDs
        self.zone_track_timestamps = defaultdict(dict)  # zone_name -> {track_id: first_seen}
        
        # Bounding box-based deduplication
        self.bbox_fingerprints = {}  # track_id -> bbox_fingerprint for deduplication
        self.seen_bbox_fingerprints = set()  # Set of all bbox fingerprints seen
        self.category_bbox_fingerprints = defaultdict(set)  # category -> set of bbox fingerprints
        
        # Time window configuration
        self.time_window = self.config.count_rules.get('time_window_seconds', 3600)  # Default 1 hour
        self.track_expiry_time = self.config.count_rules.get('track_expiry_seconds', 300)  # Default 5 minutes
        self.enable_time_based_counting = self.config.count_rules.get('enable_time_based_counting', True)
        
        # Bounding box similarity threshold for deduplication
        self.bbox_similarity_threshold = self.config.count_rules.get('bbox_similarity_threshold', 0.8)
        self.enable_bbox_deduplication = self.config.count_rules.get('enable_bbox_deduplication', True)
    
    def count_objects(self, results: Any, identification_keys: List[str] = None, 
                     current_timestamp: Optional[float] = None) -> Tuple[Any, Dict]:
        """Count objects with metadata, supporting incremental time-based counting."""
        # Use config identification keys if not provided
        if identification_keys is None:
            identification_keys = self.config.identification_keys or ["track_id"]
        
        if current_timestamp is None:
            current_timestamp = time.time()
        
        # Clean expired tracks if time-based counting is enabled
        if self.enable_time_based_counting:
            self._clean_expired_tracks(current_timestamp)
        
        metadata = {"total": 0, "by_category": defaultdict(int)}
        results_type = match_results_structure(results)
        
        if results_type == "detection":
            metadata["total"] = len(results)
            for result in results:
                category = result.get("category", "unknown")
                metadata["by_category"][category] += 1
        
        elif results_type == "classification":
            metadata["total"] = len(results)
        
        elif results_type == "object_tracking":
            current_unique_tracks = set()
            new_tracks_this_frame = set()
            unique_detections_per_category = defaultdict(set)  # For proper category counting
            
            # Keep track of processed detections to avoid duplicates
            processed_detections = []
            
            for frame_id, detections in results.items():
                if isinstance(detections, list):
                    for detection in detections:
                        # Skip if this detection is a duplicate of an already processed detection
                        if self.enable_bbox_deduplication and self._is_duplicate_detection(detection, processed_detections):
                            continue
                        
                        # Add to processed detections to check future duplicates
                        processed_detections.append(detection)
                            
                        for key in identification_keys:
                            if key in detection:
                                track_id = detection[key]
                                current_unique_tracks.add(track_id)
                                
                                # Track time-based information
                                if self.enable_time_based_counting:
                                    if track_id not in self.unique_tracks_seen:
                                        self.unique_tracks_seen.add(track_id)
                                        self.track_timestamps[track_id] = current_timestamp
                                        new_tracks_this_frame.add(track_id)
                                    
                                    # Update last seen time
                                    self.track_last_seen[track_id] = current_timestamp
                                
                                category = detection.get("category", "unknown")
                                
                                # Use bounding box fingerprint for unique category counting
                                if "bounding_box" in detection and self.enable_bbox_deduplication:
                                    bbox_fingerprint = self._calculate_bbox_fingerprint(detection["bounding_box"], category)
                                    unique_detections_per_category[category].add(bbox_fingerprint)
                                else:
                                    # Fallback to track_id based counting
                                    unique_detections_per_category[category].add(track_id)
                                
                                break  # Only use first matching identification key
            
            # Update category counts based on unique detections
            for category, unique_fingerprints in unique_detections_per_category.items():
                metadata["by_category"][category] = len(unique_fingerprints)
            
            # Set counts based on counting mode
            if self.enable_time_based_counting:
                metadata["total"] = len(self.unique_tracks_seen)
                metadata["current_frame_unique"] = len(current_unique_tracks)
                metadata["new_tracks_this_frame"] = len(new_tracks_this_frame)
                metadata["total_tracks_in_time_window"] = len(self._get_tracks_in_time_window(current_timestamp))
            else:
                metadata["total"] = len(current_unique_tracks)
        
        # Apply count rules from config
        if self.config.count_rules:
            metadata = self._apply_count_rules(metadata, self.config.count_rules, current_timestamp)
        
        # Convert defaultdict to regular dict for JSON serialization
        metadata["by_category"] = dict(metadata["by_category"])
        
        # Add time-based metadata
        if self.enable_time_based_counting:
            metadata["time_based_counting"] = {
                "enabled": True,
                "time_window_seconds": self.time_window,
                "track_expiry_seconds": self.track_expiry_time,
                "current_timestamp": current_timestamp,
                "active_tracks": len([t for t in self.track_last_seen.values() 
                                    if current_timestamp - t <= self.track_expiry_time])
            }
        
        return results, metadata
    
    def count_in_zones(self, results: Dict, zones: Dict[str, List[Tuple[int, int]]] = None, 
                      count_rules: Optional[Dict] = None, current_timestamp: Optional[float] = None) -> Dict:
        """Count objects in defined zones with configurable rules and time-based tracking."""
        # Use zones from config if not provided
        if zones is None:
            zones = {}
        
        # Use count rules from config if not provided
        if count_rules is None:
            count_rules = self.config.count_rules or {"reset_on_threshold": False, "threshold": 100}
        
        if current_timestamp is None:
            current_timestamp = time.time()
        
        # Clean expired tracks for each zone
        if self.enable_time_based_counting:
            for zone_name in zones.keys():
                self._clean_expired_zone_tracks(zone_name, current_timestamp)
        
        zone_counts = {}
        
        for zone_name, zone_polygon in zones.items():
            if zone_name not in self.zone_counters:
                self.zone_counters[zone_name] = 0
            
            current_count = 0
            current_frame_tracks = set()
            new_zone_tracks = set()
            
            if isinstance(results, dict):
                for frame_id, detections in results.items():
                    if isinstance(detections, list):
                        for detection in detections:
                            if "bounding_box" in detection:
                                bbox = detection["bounding_box"]
                                center = (
                                    (bbox["xmin"] + bbox["xmax"]) // 2,
                                    (bbox["ymin"] + bbox["ymax"]) // 2
                                )
                                
                                if self._point_in_polygon(center, zone_polygon):
                                    # Get track ID for uniqueness
                                    track_id = None
                                    for key in self.config.identification_keys or ["track_id"]:
                                        if key in detection:
                                            track_id = detection[key]
                                            break
                                    
                                    if track_id is not None:
                                        current_frame_tracks.add(track_id)
                                        
                                        # Time-based zone tracking
                                        if self.enable_time_based_counting:
                                            if track_id not in self.zone_unique_tracks[zone_name]:
                                                self.zone_unique_tracks[zone_name].add(track_id)
                                                self.zone_track_timestamps[zone_name][track_id] = current_timestamp
                                                new_zone_tracks.add(track_id)
                                        else:
                                            current_count += 1
            
            # Update zone counters based on counting mode
            if self.enable_time_based_counting:
                # Count unique tracks in zone within time window
                tracks_in_window = self._get_zone_tracks_in_time_window(zone_name, current_timestamp)
                self.zone_counters[zone_name] = len(self.zone_unique_tracks[zone_name])
                current_count = len(tracks_in_window)
            else:
                self.zone_counters[zone_name] += current_count
            
            # Apply reset rules
            if (count_rules.get("reset_on_threshold", False) and 
                self.zone_counters[zone_name] >= count_rules.get("threshold", 100)):
                self.zone_counters[zone_name] = 0
                if self.enable_time_based_counting:
                    self.zone_unique_tracks[zone_name].clear()
                    self.zone_track_timestamps[zone_name].clear()
            
            zone_counts[zone_name] = {
                "current_frame_count": len(current_frame_tracks),
                "total_unique_count": self.zone_counters[zone_name],
                "new_tracks_this_frame": len(new_zone_tracks) if self.enable_time_based_counting else 0,
                "tracks_in_time_window": current_count if self.enable_time_based_counting else current_count
            }
        
        return zone_counts
    
    def get_unique_count_by_keys(self, results: Any, keys: List[str] = None) -> Dict[str, int]:
        """Get unique count using specified identification keys."""
        if keys is None:
            keys = self.config.identification_keys or ["track_id"]
        
        unique_values = {key: set() for key in keys}
        
        if isinstance(results, list):
            for result in results:
                for key in keys:
                    if key in result:
                        unique_values[key].add(result[key])
        elif isinstance(results, dict):
            for detections in results.values():
                if isinstance(detections, list):
                    for detection in detections:
                        for key in keys:
                            if key in detection:
                                unique_values[key].add(detection[key])
        
        return {key: len(values) for key, values in unique_values.items()}
    
    def get_counting_statistics(self, current_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """Get comprehensive counting statistics."""
        if current_timestamp is None:
            current_timestamp = time.time()
        
        if not self.enable_time_based_counting:
            return {
                "time_based_counting": False,
                "total_unique_tracks": len(self.unique_tracks_seen)
            }
        
        # Clean expired tracks
        self._clean_expired_tracks(current_timestamp)
        
        active_tracks = [
            track_id for track_id, last_seen in self.track_last_seen.items()
            if current_timestamp - last_seen <= self.track_expiry_time
        ]
        
        tracks_in_window = self._get_tracks_in_time_window(current_timestamp)
        
        return {
            "time_based_counting": True,
            "total_unique_tracks_ever": len(self.unique_tracks_seen),
            "active_tracks": len(active_tracks),
            "tracks_in_time_window": len(tracks_in_window),
            "time_window_seconds": self.time_window,
            "track_expiry_seconds": self.track_expiry_time,
            "current_timestamp": current_timestamp,
            "oldest_active_track": min(self.track_timestamps.values()) if self.track_timestamps else None,
            "zone_statistics": {
                zone_name: {
                    "total_unique_tracks": len(tracks),
                    "tracks_in_window": len(self._get_zone_tracks_in_time_window(zone_name, current_timestamp))
                }
                for zone_name, tracks in self.zone_unique_tracks.items()
            }
        }
    
    def reset_counters(self, reset_zones: bool = True, reset_time_tracking: bool = True):
        """Reset all counters and tracking data."""
        self.zone_counters.clear()
        self.dwell_times.clear()
        
        if reset_time_tracking:
            self.unique_tracks_seen.clear()
            self.track_timestamps.clear()
            self.track_last_seen.clear()
            # Clear bbox deduplication data
            self.bbox_fingerprints.clear()
            self.seen_bbox_fingerprints.clear()
            self.category_bbox_fingerprints.clear()
        
        if reset_zones:
            self.zone_unique_tracks.clear()
            self.zone_track_timestamps.clear()
    
    def _get_tracks_in_time_window(self, current_timestamp: float) -> Set[str]:
        """Get track IDs that were first seen within the time window."""
        cutoff_time = current_timestamp - self.time_window
        return {
            track_id for track_id, first_seen in self.track_timestamps.items()
            if first_seen >= cutoff_time
        }
    
    def _get_zone_tracks_in_time_window(self, zone_name: str, current_timestamp: float) -> Set[str]:
        """Get track IDs for a zone that were first seen within the time window."""
        cutoff_time = current_timestamp - self.time_window
        zone_timestamps = self.zone_track_timestamps.get(zone_name, {})
        return {
            track_id for track_id, first_seen in zone_timestamps.items()
            if first_seen >= cutoff_time
        }
    
    def _clean_expired_tracks(self, current_timestamp: float):
        """Remove expired tracks from tracking."""
        cutoff_time = current_timestamp - self.track_expiry_time
        expired_tracks = [
            track_id for track_id, last_seen in self.track_last_seen.items()
            if last_seen < cutoff_time
        ]
        
        for track_id in expired_tracks:
            # Remove from global tracking (but keep in unique_tracks_seen for historical count)
            if track_id in self.track_last_seen:
                del self.track_last_seen[track_id]
    
    def _clean_expired_zone_tracks(self, zone_name: str, current_timestamp: float):
        """Remove expired tracks from zone tracking."""
        if zone_name not in self.zone_track_timestamps:
            return
        
        cutoff_time = current_timestamp - self.track_expiry_time
        zone_timestamps = self.zone_track_timestamps[zone_name]
        expired_tracks = [
            track_id for track_id, first_seen in zone_timestamps.items()
            if current_timestamp - first_seen > self.track_expiry_time
        ]
        
        # Note: We don't remove from zone_unique_tracks to maintain historical count
        # Only remove from active tracking timestamps
        for track_id in expired_tracks:
            if track_id in zone_timestamps:
                del zone_timestamps[track_id]
    
    def _apply_count_rules(self, metadata: Dict, count_rules: Dict, current_timestamp: float) -> Dict:
        """Apply counting rules to metadata."""
        if count_rules.get("unique_by_track", False):
            # Add track-based uniqueness indicator
            metadata["unique_by_track"] = True
        
        if count_rules.get("count_per_category", False):
            # Ensure per-category counting is enabled
            metadata["count_per_category"] = True
        
        if "min_count_threshold" in count_rules:
            # Filter out categories below threshold
            min_threshold = count_rules["min_count_threshold"]
            filtered_categories = {
                cat: count for cat, count in metadata["by_category"].items() 
                if count >= min_threshold
            }
            metadata["by_category"] = filtered_categories
            metadata["total"] = sum(filtered_categories.values())
        
        # Add time-based rules
        if self.enable_time_based_counting:
            if count_rules.get("report_time_window_only", False):
                # Only report counts within the time window
                tracks_in_window = self._get_tracks_in_time_window(current_timestamp)
                metadata["total"] = len(tracks_in_window)
                metadata["count_mode"] = "time_window_only"
            else:
                metadata["count_mode"] = "cumulative_unique"
        
        return metadata

    def _point_in_polygon(self, point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
        """Check if point is inside polygon using ray casting algorithm."""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    def _calculate_bbox_fingerprint(self, bbox: Dict[str, int], category: str = "unknown") -> str:
        """Calculate a fingerprint for a bounding box to detect similar objects."""
        try:
            # Normalize bbox coordinates to reduce minor variations
            width = bbox["xmax"] - bbox["xmin"]
            height = bbox["ymax"] - bbox["ymin"]
            center_x = (bbox["xmin"] + bbox["xmax"]) // 2
            center_y = (bbox["ymin"] + bbox["ymax"]) // 2
            
            # Create a fingerprint that's tolerant to small movements
            # Round to nearest 10 pixels to group nearby objects
            grid_size = 20
            grid_x = center_x // grid_size
            grid_y = center_y // grid_size
            size_bucket = (width // 10, height // 10)  # Group similar sizes
            
            return f"{category}_{grid_x}_{grid_y}_{size_bucket[0]}_{size_bucket[1]}"
        except (KeyError, TypeError):
            return f"{category}_unknown_bbox"
    
    def _calculate_bbox_overlap(self, bbox1: Dict[str, int], bbox2: Dict[str, int]) -> float:
        """Calculate IoU (Intersection over Union) between two bounding boxes."""
        try:
            # Calculate intersection coordinates
            x1 = max(bbox1["xmin"], bbox2["xmin"])
            y1 = max(bbox1["ymin"], bbox2["ymin"])
            x2 = min(bbox1["xmax"], bbox2["xmax"])
            y2 = min(bbox1["ymax"], bbox2["ymax"])
            
            # Calculate intersection area
            if x2 <= x1 or y2 <= y1:
                return 0.0
            
            intersection = (x2 - x1) * (y2 - y1)
            
            # Calculate union area
            area1 = (bbox1["xmax"] - bbox1["xmin"]) * (bbox1["ymax"] - bbox1["ymin"])
            area2 = (bbox2["xmax"] - bbox2["xmin"]) * (bbox2["ymax"] - bbox2["ymin"])
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0.0
        except (KeyError, TypeError, ZeroDivisionError):
            return 0.0
    
    def _is_duplicate_detection(self, detection: Dict[str, Any], current_detections: List[Dict[str, Any]]) -> bool:
        """Check if a detection is a duplicate based on bounding box similarity."""
        if not self.enable_bbox_deduplication or "bounding_box" not in detection:
            return False
        
        current_bbox = detection["bounding_box"]
        current_category = detection.get("category", "unknown")
        
        # Check against current detections in this batch
        for other_detection in current_detections:
            if "bounding_box" not in other_detection:
                continue
                
            other_category = other_detection.get("category", "unknown")
            if current_category != other_category:
                continue
                
            overlap = self._calculate_bbox_overlap(current_bbox, other_detection["bounding_box"])
            if overlap >= self.bbox_similarity_threshold:
                return True
        
        return False 