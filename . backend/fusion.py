# fusion.py

def fuse_features(cam_feat=None, wear_feat=None):
    """
    Combines features from camera PPG and wearable PPG.

    Priority:
    - Wearable data is more reliable → higher weight
    - Camera data is secondary

    Returns:
    - fused feature dictionary
    """

    # If both available → weighted fusion
    if cam_feat and wear_feat:
        fused = {}

        for key in cam_feat:
            cam_value = cam_feat.get(key, 0)
            wear_value = wear_feat.get(key, 0)

            # Weighted combination
            fused[key] = 0.4 * cam_value + 0.6 * wear_value

        return fused

    # If only wearable available
    if wear_feat:
        return wear_feat

    # If only camera available
    if cam_feat:
        return cam_feat

    # If nothing available
    return {}
