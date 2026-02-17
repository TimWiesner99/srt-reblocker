from src.srt_block import SrtBlock
from src.timecode import DecimalTimecode

# Default alias for this SRT-focused project
Timecode = DecimalTimecode


def main():
    try:
        print("Hello World!")
        # add main program here



    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        input("Press Enter to exit...")    



if __name__ == "__main__":
    main()