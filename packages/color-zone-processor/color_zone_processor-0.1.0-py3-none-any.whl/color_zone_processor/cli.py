import argparse
from .processor import process_image

def main():
    parser = argparse.ArgumentParser(description='Process image by replacing pixels of specific color with two other colors.')
    parser.add_argument('--first-percentage', type=float, required=True,
                      help='Percentage of target color pixels to replace with first color (0-100)')
    parser.add_argument('--total-percentage', type=float, required=True,
                      help='Total percentage of target color pixels to replace (0-100)')
    parser.add_argument('--min-zone-size', type=int, default=100,
                      help='Minimum size of color zone to consider (default: 100)')
    parser.add_argument('--input', type=str, default='input.png',
                      help='Input image path (default: input.png)')
    parser.add_argument('--target-color', type=str, default='#5B6075',
                      help='Target color in hex (default: #5B6075)')
    parser.add_argument('--first-color', type=str, default='#1C505D',
                      help='First replacement color in hex (default: #1C505D)')
    parser.add_argument('--second-color', type=str, default='#329D9C',
                      help='Second replacement color in hex (default: #329D9C)')
    
    args = parser.parse_args()
    
    # Validate percentages
    if not (0 <= args.first_percentage <= 100):
        parser.error("First percentage must be between 0 and 100")
    if not (0 <= args.total_percentage <= 100):
        parser.error("Total percentage must be between 0 and 100")
    if args.first_percentage > args.total_percentage:
        parser.error("First percentage cannot be greater than total percentage")
    
    process_image(
        args.input,
        args.target_color,
        args.first_color,
        args.second_color,
        args.first_percentage,
        args.total_percentage,
        args.min_zone_size
    )

if __name__ == "__main__":
    main() 