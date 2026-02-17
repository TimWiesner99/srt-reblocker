# srt-reblocker

Combines small subtitle blocks from an SRT file into larger blocks of a given duration. Useful for generating transcripts and spotting lists where you need fewer, longer text segments instead of the short fragments typical of subtitles.

Line breaks within blocks are merged into single lines and trailing ellipses (`...`) are removed automatically.

## Usage

```
python main.py <srt_file> <block_length> [output_path]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `srt_file` | Yes | Path to the input SRT file |
| `block_length` | Yes | Desired block length in minutes |
| `output_path` | No | Output directory (default: same as input file) |

The output file is written to `<output_path>/<original_filename>_reblocker.srt`.

### Examples

Combine blocks into roughly 5-minute segments, output next to the input file:

```
python main.py subtitles.srt 5
```

Same, but write to a custom directory:

```
python main.py subtitles.srt 10 ./my_output/
```
