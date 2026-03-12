# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge
import numpy as np
import queue

# Helper to drive valid_i on uio_in[6]
def set_valid(dut, val: int) -> None:
    cur = int(dut.uio_in.value)
    if val:
        cur |= (1 << 6)
    else:
        cur &= ~(1 << 6)
    dut.uio_in.value = cur

def is_valid_o(dut, val) -> bool:
    return (val) & 0x1 == 1

# 3x3 convolution with kernel of ones model
class Conv2dModel():
    def __init__(self, dut, buf):
        self._q = queue.SimpleQueue()
        self._linewidth_px_p = dut.linewidth_px_p.value
        self._buf = buf

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
        # print(f"Current buffer state before convolution:\n{self._buf}")
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

   # Create 3x16 "image" as 0..47
    inps = np.arange(linewidth_px_p * 3, dtype=int)

    model = Conv2dModel(dut, inps.reshape(3, linewidth_px_p))

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Streaming 3x16 image into conv2d")

    await RisingEdge(dut.rst_n)

    # Stream the 3x16 pixels, one per cycle, with valid_i asserted
    set_valid(dut, 1)

    for i in inps:
        # enqueue dummy input as well
        model.enqueue_inp(0)
        dut.ui_in.value = int(i)
        await FallingEdge(dut.clk)

    # set inputs to zero, but keep window buffer running to drain output
    dut.ui_in.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    print(f"Expected Buffer is {inps.reshape((3, linewidth_px_p))}")

    for _ in range(linewidth_px_p):
      # Concatenate 8-bit dedicated output and 6-bit GPIO output into 14-bit value
      expected = model.line_convolve()
      model.enqueue_inp(0)  # Enqueue dummy input for next cycle
      dedicated_out = int(dut.uo_out.value) & 0xFF  # 8-bit from uo_out
      gpio_out = int(dut.uio_out.value) & 0x3F     # 6-bit from uio_out[5:0]
      full_output = (gpio_out << 8) | (dedicated_out << 2)  # GPIO in upper 6 bits, dedicated in lower 8 bits
      await RisingEdge(dut.clk)
      
      print(f"Expected: {expected}, Full Output: {full_output:014b} (int(full_output)={full_output}), error: {abs((expected - full_output) / expected)}")
      assert abs((expected - full_output) / expected) < 0.1
