import argparse
import os
import re

from src.srt_block import SrtBlock
from src.timecode import DecimalTimecode

Timecode = DecimalTimecode

TIMECODE_LINE_PATTERN = re.compile(
    r'^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})$'
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine SRT subtitle blocks into larger blocks.")
    parser.add_argument("srt_file", help="Path to the SRT file")
    parser.add_argument("block_length", type=int, help="Desired block length in seconds")
    parser.add_argument("output_path", nargs="?", default=None, help="Output directory (default: same directory as input file)")
    return parser.parse_args()


def read_srt(filepath: str) -> list[SrtBlock]:
    """Read an SRT file and return an ordered list of SrtBlocks."""
    with open(filepath, encoding="utf-8-sig") as f:
        content = f.read()

    blocks: list[SrtBlock] = []
    # Split on blank lines to get raw block chunks
    raw_blocks = re.split(r'\n\s*\n', content.strip())

    for raw in raw_blocks:
        lines = raw.strip().splitlines()
        if len(lines) < 3:
            continue

        index = int(lines[0].strip())

        tc_match = TIMECODE_LINE_PATTERN.match(lines[1].strip())
        if not tc_match:
            raise ValueError(f"Invalid timecode line in block {index}: '{lines[1].strip()}'")

        begin = Timecode.from_string(tc_match.group(1))
        end = Timecode.from_string(tc_match.group(2))
        
        # text = "\n".join(lines[2:])
        text = remove_dots(" ".join(lines[2:]))

        blocks.append(SrtBlock(index=index, begin=begin, end=end, text=text))

    return blocks

def remove_linebreaks(text: str) -> str:
    """Removes linebreaks from strings."""
    return text.replace("\n", " ")

def remove_dots(text: str) -> str:
    """Removes '...' from strings."""
    return text.replace("...", "")

def write_srt(blocks: list[SrtBlock], filepath: str) -> None:
    """Write a list of SrtBlocks to an SRT file."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(f"{block.index}\n")
            f.write(f"{block.begin.to_string()} --> {block.end.to_string()}\n")
            f.write(f"{block.text}\n")
            f.write("\n")


def rebuild_blocks(blocks: list[SrtBlock], block_length: Timecode) -> list[SrtBlock]:
    new_blocks: list[SrtBlock] = []

    while len(blocks) > 0:
        this_block = blocks.pop(0)
        current_length = this_block.end - this_block.begin

        # go through following blocks
        while current_length < block_length:
            # check if there are any blocks left to pop, otherwise break out of loop
            if len(blocks) == 0:
                break

            # get next block in list
            next_block = blocks.pop(0)

            # append information to this block
            this_block.text += " " + next_block.text  
            this_block.end = next_block.end

            # update length of block
            current_length = this_block.end - this_block.begin

        new_blocks.append(this_block)

    return new_blocks

def main():
    args = parse_args()

    block_length = Timecode(minutes = args.block_length)

    try:
        blocks = read_srt(args.srt_file)
        print(f"Loaded {len(blocks)} subtitle blocks from '{args.srt_file}'")

        number_original = len(blocks) 
        new_blocks = rebuild_blocks(blocks, block_length)
        print(f"Reorganized {number_original} blocks into {len(new_blocks)} blocks of around {args.block_length} minutes.")

        # for testing only: print output to console
        # for block in new_blocks:
        #     print(f'from:{block.begin} to:{block.end} \n{block.text}')

        # "recount" blocks, i.e. make indices consecutive again
        for i, block in enumerate(new_blocks):
            block.index = i

        # output new_blocks to new srt file
        output_dir = args.output_path or os.path.dirname(os.path.abspath(args.srt_file))
        source_name = os.path.splitext(os.path.basename(args.srt_file))[0]
        output_file = os.path.join(output_dir, f"{source_name}_reblocked_{args.block_length}min.srt")
        write_srt(new_blocks, output_file)
        print(f"Written output to '{output_file}'")


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        input("Press Enter to exit...")    

if __name__ == "__main__":
    main()