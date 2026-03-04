# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
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

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())
    linewidth_px_p = dut.linewidth_px_p.value
    model = Conv2dModel(dut)

    # create 3x16 "image"
    inps = np.arange(linewidth_px_p.to_unsigned() * 3)

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    # Set the input values you want to test
    dut.ui_in.value = 20
    dut.uio_in.value = 30

    # Wait for one clock cycle to see the output values
    await ClockCycles(dut.clk, 1)

    # The following assertion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    assert dut.uo_out.value == 50

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
