import argparse
from volume_booster import increase_volume

def main():
    parser = argparse.ArgumentParser(description="Increase the volume of an audio file.")
    parser.add_argument("input_file", help="Path to the input audio file")
    parser.add_argument("output_file", help="Path to save the output audio file")
    parser.add_argument("multiplier", type=float, help="Volume multiplier (e.g., 2.0 for double volume)")
    
    args = parser.parse_args()
    
    try:
        output_path = increase_volume(args.input_file, args.output_file, args.multiplier)
        print(f"✅ Volume increased by {args.multiplier}x and saved as {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
