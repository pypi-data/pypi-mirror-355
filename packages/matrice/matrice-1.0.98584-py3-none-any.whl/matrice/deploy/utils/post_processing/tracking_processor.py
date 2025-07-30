"""Tracking functionality for post-processing."""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
from matrice.deploy.utils.post_processing.config import TrackingConfig


class TrackingProcessor:
    """Class for handling tracking-related operations."""
    
    def __init__(self, config: TrackingConfig):
        """Initialize TrackingProcessor with TrackingConfig.
        
        Args:
            config: TrackingConfig instance with tracking configuration
        """
        if not isinstance(config, TrackingConfig):
            raise TypeError(f"Expected TrackingConfig, got {type(config)}")
        
        self.config = config
        self.trackers = {}
        self.line_crossings = defaultdict(list)
    
    def track_in_zone(self, results: List[Dict], zone_polygon: List[Tuple[int, int]]) -> Dict:
        """Track objects within a defined zone."""
        zone_tracks = []
        
        for result in results:
            if "bounding_box" in result:
                bbox = result["bounding_box"]
                center = (
                    (bbox["xmin"] + bbox["xmax"]) // 2,
                    (bbox["ymin"] + bbox["ymax"]) // 2
                )
                
                if self._point_in_polygon(center, zone_polygon):
                    zone_tracks.append({
                        **result,
                        "in_zone": True,
                        "zone_center": center
                    })
        
        return {
            "zone_tracks": zone_tracks,
            "count_in_zone": len(zone_tracks)
        }
    
    def detect_line_crossing(self, results: Dict, line_points: List[Tuple[int, int]], 
                           track_id_key: str = "track_id") -> Dict:
        """Detect when tracked objects cross a virtual line."""
        crossings = []
        
        if len(line_points) != 2:
            return {"crossings": crossings, "total_crossings": 0}
        
        line_start, line_end = line_points
        
        for frame_id, detections in results.items():
            if isinstance(detections, list):
                for detection in detections:
                    if track_id_key in detection and "bounding_box" in detection:
                        track_id = detection[track_id_key]
                        bbox = detection["bounding_box"]
                        center = (
                            (bbox["xmin"] + bbox["xmax"]) // 2,
                            (bbox["ymin"] + bbox["ymax"]) // 2
                        )
                        
                        if self._check_line_crossing(track_id, center, line_start, line_end, frame_id):
                            crossings.append({
                                "track_id": track_id,
                                "frame_id": frame_id,
                                "position": center,
                                "category": detection.get("category", "unknown")
                            })
        
        return {
            "crossings": crossings,
            "total_crossings": len(crossings)
        }
    
    def process_all_zones(self, results: List[Dict]) -> Dict[str, Dict]:
        """Process all tracking zones from config."""
        zone_results = {}
        
        if not self.config.tracking_zones:
            return zone_results
        
        for zone_name, zone_polygon in self.config.tracking_zones.items():
            zone_results[zone_name] = self.track_in_zone(results, zone_polygon)
        
        return zone_results
    
    def process_all_line_crossings(self, results: Dict) -> Dict[str, Dict]:
        """Process all crossing lines from config."""
        crossing_results = {}
        
        if not self.config.crossing_lines:
            return crossing_results
        
        for line_name, line_points in self.config.crossing_lines.items():
            crossing_results[line_name] = self.detect_line_crossing(results, line_points)
        
        return crossing_results
    
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
    
    def _check_line_crossing(self, track_id: int, current_pos: Tuple[int, int], 
                           line_start: Tuple[int, int], line_end: Tuple[int, int], 
                           frame_id: str) -> bool:
        """Check if a track crossed a line between current and previous position."""
        if track_id not in self.line_crossings:
            self.line_crossings[track_id] = []
        
        prev_positions = self.line_crossings[track_id]
        
        if prev_positions:
            prev_pos = prev_positions[-1]["position"]
            if self._line_segments_intersect(prev_pos, current_pos, line_start, line_end):
                return True
        
        # Store current position
        self.line_crossings[track_id].append({
            "position": current_pos,
            "frame_id": frame_id
        })
        
        # Keep only recent positions (last 10)
        if len(self.line_crossings[track_id]) > 10:
            self.line_crossings[track_id] = self.line_crossings[track_id][-10:]
        
        return False
    
    def _line_segments_intersect(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                               p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
        """Check if two line segments intersect."""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4) 