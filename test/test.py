# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge
import numpy as np
import queue


# 3x3 convolution with kernel of ones model
class Conv2dModel():
    def __init__(self, dut):
        self._q = queue.SimpleQueue()
        self._linewidth_px_p = dut.linewidth_px_p.value

        # Initialize _buf with NaN so that we can
        # detect when the output should be not an X in simulation
        self._buf = np.zeros((3,self._linewidth_px_p))/0

    def _update_window(self, inp):
        tmp = self._buf.flatten()

        tmp = np.roll(tmp, -1, axis=0)
        tmp[-1] = inp
        tmp = np.reshape(tmp, self._buf.shape)
        self._buf = tmp

    def _apply_kernel(self, buf):
        window = buf[:,-3:]
        # The kernel is all ones, so we can just sum the window to get the result
        result = window.sum()
        return result

    def enqueue_inp(self, data_i):
        self._q.put(data_i)

    def line_convolve(self):
        self._update_window(self._q.get())
        expected = self._apply_kernel(self._buf)
        return expected

# Helper to drive valid_i on uio_in[6]
def set_valid(dut, val: int) -> None:
    cur = int(dut.uio_in.value)
    if val:
        cur |= (1 << 6)
    else:
        cur &= ~(1 << 6)
    dut.uio_in.value = cur

@cocotb.test()
async def test_line_buffer_conv3x16(dut):
    dut._log.info("Start 3x3 conv2d line-buffer test on 3x16 image")

    # Clock: 10 us period (100 kHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    linewidth_px_p = dut.linewidth_px_p.value.to_unsigned()
    model = Conv2dModel(dut)

    # Create 3x16 "image" as 0..47
    inps = np.arange(linewidth_px_p * 3, dtype=int)

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Streaming 3x16 image into conv2d")


    # Stream the 3x16 pixels, one per cycle, with valid_i asserted
    set_valid(dut, 1)

    for i in inps:
        model.enqueue_inp(i)
        await FallingEdge(dut.clk)

    for _ in range(linewidth_px_p):
      await RisingEdge(dut.clk)
      expected = model.line_convolve()
      print(f"Expected: {expected}, Got: {dut.data_o.value}")
