from PIL import Image
import numpy as np
from scipy import ndimage
import os

def hex_to_rgba(hex_color):
    """
    Convert hex color code to RGBA tuple.
    
    Args:
        hex_color (str): Hex color code (e.g., '#FF0000' or 'FF0000')
    
    Returns:
        tuple: RGBA color values (R, G, B, A)
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB and add alpha channel (255 for fully opaque)
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return rgb + (255,)

def find_color_zones(img_array, target_color, min_size=100):
    """
    Find connected zones of target color in the image.
    
    Args:
        img_array: Image array
        target_color: Target color in RGBA format
        min_size: Minimum size of zone to consider
    
    Returns:
        List of (zone_mask, zone_size) tuples
    """
    # Create mask for target color pixels
    target_mask = np.all(img_array[:, :, :3] == target_color[:3], axis=2)
    
    # Label connected components
    labeled_array, num_features = ndimage.label(target_mask)
    
    # Find zones and their sizes
    zones = []
    for i in range(1, num_features + 1):
        zone_mask = (labeled_array == i)
        zone_size = np.sum(zone_mask)
        if zone_size >= min_size:
            zones.append((zone_mask, zone_size))
    
    # Sort zones by size (largest first)
    zones.sort(key=lambda x: x[1], reverse=True)
    return zones

def get_ordered_pixels(zone_mask):
    """
    Get pixel coordinates in the zone ordered from top-left to bottom-right.
    
    Args:
        zone_mask: Boolean mask of the zone
    
    Returns:
        List of (y, x) coordinates
    """
    y_coords, x_coords = np.where(zone_mask)
    # Sort by y first, then x to get top-to-bottom, left-to-right order
    sorted_indices = np.lexsort((x_coords, y_coords))
    return list(zip(y_coords[sorted_indices], x_coords[sorted_indices]))

def process_image(image_path, target_color_hex, first_color_hex, second_color_hex, first_percentage, total_percentage, min_zone_size=100):
    """
    Process an image by counting pixels of target color and replacing them with two different colors
    based on specified percentages, filling pixels sequentially in each zone with second color
    following immediately after first color.
    
    Args:
        image_path (str): Path to the input image
        target_color_hex (str): Hex color code to count and replace (e.g., '#FF0000')
        first_color_hex (str): First hex color code to replace with (e.g., '#00FF00')
        second_color_hex (str): Second hex color code to replace with (e.g., '#0000FF')
        first_percentage (float): Percentage of target color pixels to replace with first color (0-100)
        total_percentage (float): Total percentage of target color pixels to replace (0-100)
        min_zone_size (int): Minimum size of color zone to consider
    
    Returns:
        str: Path to the processed image
    """
    try:
        # Convert hex colors to RGBA
        target_color = hex_to_rgba(target_color_hex)
        first_color = hex_to_rgba(first_color_hex)
        second_color = hex_to_rgba(second_color_hex)
        
        # Open the image
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Find color zones
        zones = find_color_zones(img_array, target_color, min_zone_size)
        
        if not zones:
            print(f"No zones of color {target_color_hex} found in the image.")
            return None
        
        # Calculate total pixels in all zones
        total_target_pixels = sum(zone_size for _, zone_size in zones)
        total_pixels_to_replace = int(total_target_pixels * (total_percentage / 100))
        first_color_pixels = int(total_target_pixels * (first_percentage / 100))
        second_color_pixels = total_pixels_to_replace - first_color_pixels
        
        # Process zones
        remaining_first_pixels = first_color_pixels
        remaining_second_pixels = second_color_pixels
        
        for zone_mask, zone_size in zones:
            # Get ordered pixel coordinates for this zone
            ordered_pixels = get_ordered_pixels(zone_mask)
            
            # Calculate how many pixels to replace in this zone
            zone_first_pixels = min(remaining_first_pixels, zone_size)
            zone_second_pixels = min(remaining_second_pixels, zone_size - zone_first_pixels)
            
            if zone_first_pixels > 0:
                # Replace pixels with first color
                for y, x in ordered_pixels[:zone_first_pixels]:
                    img_array[y, x] = first_color
                remaining_first_pixels -= zone_first_pixels
                
                # Replace pixels with second color immediately after
                if zone_second_pixels > 0:
                    for y, x in ordered_pixels[zone_first_pixels:zone_first_pixels + zone_second_pixels]:
                        img_array[y, x] = second_color
                    remaining_second_pixels -= zone_second_pixels
            
            if remaining_first_pixels <= 0 and remaining_second_pixels <= 0:
                break
        
        # Create output filename
        base_name = os.path.splitext(image_path)[0]
        output_path = f"{base_name}_processed.png"
        
        # Save the processed image
        processed_img = Image.fromarray(img_array)
        processed_img.save(output_path)
        
        print(f"Processed image saved as: {output_path}")
        print(f"Total pixels of color {target_color_hex}: {total_target_pixels}")
        print(f"Pixels replaced with {first_color_hex}: {first_color_pixels} ({first_percentage}%)")
        print(f"Pixels replaced with {second_color_hex}: {second_color_pixels} ({total_percentage - first_percentage}%)")
        print(f"Number of zones processed: {len(zones)}")
        
        return output_path
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None 