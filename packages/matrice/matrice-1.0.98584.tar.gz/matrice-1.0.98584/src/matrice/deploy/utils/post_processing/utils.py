"""Utility functions for post-processing."""

def match_results_structure(results):
    """Match the results structure to the expected structure based on actual output formats.
    
    Based on eg_output.json:
    - Classification: {"category": str, "confidence": float}
    - Detection: [{"bounding_box": {...}, "category": str, "confidence": float}, ...]
    - Instance Segmentation: Same as detection but with "masks" field
    - Object Tracking: {"frame_id": [{"track_id": int, "category": str, "confidence": float, "bounding_box": {...}}, ...]}
    - Activity Recognition: {"frame_id": [{"category": str, "confidence": float, "bounding_box": {...}}, ...]} (no track_id)
    """
    if isinstance(results, list):
        # Array format - detection or instance segmentation
        if len(results) > 0 and isinstance(results[0], dict):
            if results[0].get("masks"):
                return "instance_segmentation"
            elif "bounding_box" in results[0] and "category" in results[0] and "confidence" in results[0]:
                return "detection"
        return "detection"  # Default for list format
    
    elif isinstance(results, dict):
        # Check if it's a simple classification result
        if "category" in results and "confidence" in results and len(results) == 2:
            return "classification"
        
        # Check if it's frame-based (tracking or activity recognition)
        # Keys should be frame numbers or frame identifiers
        frame_keys = list(results.keys())
        if frame_keys and all(isinstance(k, (str, int)) for k in frame_keys):
            # Check the first frame's content to determine type
            first_frame_data = list(results.values())[0]
            if isinstance(first_frame_data, list) and len(first_frame_data) > 0:
                first_detection = first_frame_data[0]
                if isinstance(first_detection, dict):
                    # Check if it has track_id (object tracking) or not (activity recognition)
                    if "track_id" in first_detection:
                        return "object_tracking"
                    elif "category" in first_detection and "confidence" in first_detection:
                        return "activity_recognition"
        
        # If we can't determine the type, check for typical classification structure
        if "category" in results and "confidence" in results:
            return "classification"
    
    return "unknown" 