/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_yanghuaxuan_conv2d (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
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
  // bit 7:0 -> uo_out[7:0]
  // bit 13:8 -> uio_out[5:0]
  assign uo_out = conv2d_data_o[7:0];
  assign uio_out[5:0] = conv2d_data_o[13:8];

  // 3x3 convolution with kernel of all ones, stride 1, and no padding
  conv2d #(
    .linewidth_px_p(16),
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
    .ready_o()
  );

endmodule
