/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_yanghuaxuan_conv2d #(
  parameter linewidth_px_p = 16
)(
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    /* verilator lint_off UNUSEDSIGNAL */
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    /* verilator lint_on UNUSEDSIGNAL */
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire rst = ~rst_n;
  // only valid_i and valid_o are used in this design indicate valid input and data
  wire valid_i;
  wire valid_o;
  wire [15:0] conv2d_data_o;

  assign valid_i = uio_in[6];
  assign uio_out[7] = valid_o;
  assign uio_oe = 8'b10111111; // Enable output for valid_o and ready_o

  // to output, most significant 2 bits of uio_out is reserved for valid_o and valid_i signal
  // bit 9:2 -> uo_out[9:2]
  // bit 15:10 -> uio_out[15:10]

  // GPIO[5:0] <- conv2d_data_o[15:10]
  // GPIO[6]   <- valid_i
  // GPIO[7]   <- valid_o

  assign uo_out = conv2d_data_o[9:2];
  assign uio_out[6] = 1'b0; // unused
  assign uio_out[5:0] = conv2d_data_o[15:10];

  // 3x3 convolution with kernel of all ones, stride 1, and no padding
  conv2d #(
    .linewidth_px_p(linewidth_px_p),
    .width_p(8)
  ) conv2d_inst
  (
    .clk_i(clk),
    .reset_i(rst),
    .data_i(ui_in),
    .data_o(conv2d_data_o),
    .valid_i(valid_i),
    .valid_o(valid_o),
    .ready_i(1'b1),
    /* verilator lint_off PINCONNECTEMPTY */
    .ready_o()
    /* verilator lint_on PINCONNECTEMPTY */
  );

  wire _unused_ok = 1'b0 && &{1'b0,
                    uio_in[7],
                    uio_in[5:0],
                    conv2d_data_o[2:0],
                    1'b0};

endmodule
