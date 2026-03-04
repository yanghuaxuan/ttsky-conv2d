## How it works

This project implements a streaming 2D convolution engine for a fixed 3x3 kernel of all ones.

- Input pixel width: 8 bits (`ui_in[7:0]`)
- Image line width parameter: 16 pixels (`linewidth_px_p = 16`)
- Kernel: all ones
- Stride: 1
- Padding: none

The core (`conv2d`) uses two line delay buffers plus three 3-tap shift registers to build a sliding 3x3 window from a 1-pixel-per-cycle input stream. For each valid window position, it sums all 9 pixels and produces the convolution result.

Interface mapping in the Tiny Tapeout wrapper (`tt_um_yanghuaxuan_conv2d`):

- `ui_in[7:0]`: pixel input (`data_i`)
- `uio_in[6]`: input valid (`valid_i`)
- `uio_out[7]`: output valid (`valid_o`)
- `uo_out[7:0]`: output bits `[7:0]`
- `uio_out[5:0]`: output bits `[13:8]`

So the full convolution output is 14 bits:

- `conv_out[13:0] = {uio_out[5:0], uo_out[7:0]}`

`ready_i` is tied high inside the wrapper, so the core is always ready to send data downstream.

## How to test

The included cocotb test streams a 3x16 image (`0..47`) into the design and compares the DUT output against a Python model of the same 3x3 all-ones convolution.

From the `test` directory, run:

```sh
make -B
```

What the test does:

1. Resets the DUT.
2. Drives one 8-bit pixel per clock on `ui_in`.
3. Asserts `valid_i` through `uio_in[6]` while streaming.
4. Reads output as `full_output = (uio_out[5:0] << 8) | uo_out[7:0]`.
5. Checks/prints expected vs DUT convolution values.


## External hardware

No external hardware is required.

## Usage of LLMs
An LLM was used to assist with creating the testbench, as well as docoumentation
