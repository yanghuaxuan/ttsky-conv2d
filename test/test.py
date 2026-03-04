# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import numpy as np


class Conv2dModel:
    """Simple 3x3, stride-1, no-padding conv2d model on a 3xW image.

    Kernel is all ones, so the output at each valid horizontal position is
    just the sum of the 3x3 window.
    """

    def __init__(self, linewidth_px_p: int):
        self._linewidth_px_p = int(linewidth_px_p)

    def conv_image(self, inps: np.ndarray) -> list[int]:
        """Compute reference outputs for a flattened 3xW image.

        inps is a 1D array of length 3 * linewidth_px_p, row-major.
        Returns a list of (linewidth_px_p - 2) convolution outputs.
        """

        width = self._linewidth_px_p
        img = np.reshape(inps, (3, width))

        outputs: list[int] = []
        for col in range(width - 2):
            window = img[:, col : col + 3]
            outputs.append(int(window.sum()))
        return outputs


@cocotb.test()
async def test_line_buffer_conv3x16(dut):
    dut._log.info("Start 3x3 conv2d line-buffer test on 3x16 image")

    # Clock: 10 us period (100 kHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Fixed image width used in RTL parameters
    linewidth_px_p = 16
    model = Conv2dModel(linewidth_px_p)

    # Create 3x16 "image" as 0..47
    inps = np.arange(linewidth_px_p * 3, dtype=int)
    expected = model.conv_image(inps)

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Streaming 3x16 image into conv2d")

    hw_outputs: list[int] = []

    # Helper to drive valid_i on uio_in[6]
    def set_valid(val: int) -> None:
        cur = int(dut.uio_in.value)
        if val:
            cur |= (1 << 6)
        else:
            cur &= ~(1 << 6)
        dut.uio_in.value = cur

    # Stream the 3x16 pixels, one per cycle, with valid_i asserted
    for pix in inps:
        dut.ui_in.value = pix & 0xFF
        set_valid(1)
        await ClockCycles(dut.clk, 1)

        # Capture output when valid_o (uio_out[7]) is high
        uio_out_val = int(dut.uio_out.value)
        if (uio_out_val >> 7) & 0x1:
            low = int(dut.uo_out.value) & 0xFF
            high6 = uio_out_val & 0x3F  # bits 5:0 hold data_o[13:8]
            hw_outputs.append((high6 << 8) | low)

    # De-assert valid and flush the pipeline for a bit
    set_valid(0)
    for _ in range(2 * linewidth_px_p):
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 1)

        uio_out_val = int(dut.uio_out.value)
        if (uio_out_val >> 7) & 0x1:
            low = int(dut.uo_out.value) & 0xFF
            high6 = uio_out_val & 0x3F
            hw_outputs.append((high6 << 8) | low)

    dut._log.info(f"Collected {len(hw_outputs)} hardware outputs")
    dut._log.info(f"Expected outputs ({len(expected)}): {expected}")

    # Compare the tail of the hardware stream to the expected conv outputs
    assert len(hw_outputs) >= len(expected), "Not enough valid outputs from DUT"
    tail = hw_outputs[-len(expected) :]
    assert tail == expected, f"Mismatch between DUT outputs and conv2d model. DUT tail={tail}, expected={expected}"
