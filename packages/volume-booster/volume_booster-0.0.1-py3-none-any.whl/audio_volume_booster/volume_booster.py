from audio_segment import AudioSegment
import math

def volume_multiplier_to_db(multiplier):
    """Convert a volume multiplier to decibels."""
    return 20 * math.log10(multiplier)

def increase_volume(input_file, output_file, multiplier):
    """
    Increase the volume of an audio file and save it to output_file.
    
    Args:
        input_file (str): Path to the input audio file.
        output_file (str): Path to save the output audio file.
        multiplier (float): Volume multiplier (e.g., 2.0 for double volume).
    
    Returns:
        str: Path to the output audio file.
    """
    sound = AudioSegment.from_file(input_file)
    db_increase = volume_multiplier_to_db(multiplier)
    louder = sound + db_increase
    louder.export(output_file, format="mp3")
    return output_file
