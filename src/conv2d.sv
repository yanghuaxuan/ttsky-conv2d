module conv2d
  #(
     parameter  linewidth_px_p = 16
    ,parameter width_p = 8)
   (input [0:0] clk_i
    ,input [0:0] reset_i
    ,input [0:0] valid_i
    ,output [0:0] ready_o
    ,input [width_p - 1 : 0] data_i
    ,output [0:0] valid_o
    ,input [0:0] ready_i
    ,output [(2 * width_p) - 1 : 0] data_o
    );

   // Elastic State Machine Logic
   logic                        valid_r;
   wire                         enable_w;

   // logic [width_p - 1:0] window_head_l[2:0];
   logic [2 * width_p - 1:0] window_head_l[2:0];
   logic [2 * width_p - 1:0] window_mid_l[2:0];
   logic [2 * width_p - 1:0] window_tail_l[2:0];
   wire [2 * width_p - 1:0]  delaybuf0_out_w, delaybuf1_out_w;

   assign enable_w = valid_i & ready_o;

   assign ready_o = ~valid_o | ready_i;

   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         valid_r <= 1'b0;
      end else if (ready_o) begin
         valid_r <= enable_w;
      end
   end
   assign valid_o = valid_r;

   // shift register logic for head shift register
   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         window_head_l[0] <= '0;
         window_head_l[1] <= '0;
         window_head_l[2] <= '0;
      end else begin
         if(enable_w) begin
            // buffer_r[0] <= data_i;
            window_head_l[0] <= { {width_p{'0}},  data_i };
            window_head_l[1] <= window_head_l[0];
            window_head_l[2] <= window_head_l[1];
         end
      end
   end

   delaybuffer #(.width_p(2 * width_p), .delay_p(linewidth_px_p - 3 - 1))
     delay_buf_inst0
       (
        // Outputs
        .ready_o                        (),
        .valid_o                        (),
        .data_o                         (delaybuf0_out_w),
        // Inputs
        .clk_i                          (clk_i),
        .reset_i                        (reset_i),
        .data_i                         (window_head_l[2]),
        .valid_i                        (enable_w),
        .ready_i                        (1'b1));

   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         window_mid_l[0] <= '0;
         window_mid_l[1] <= '0;
         window_mid_l[2] <= '0;
      end else begin
         if(enable_w) begin
            window_mid_l[0] <= delaybuf0_out_w;
            window_mid_l[1] <= window_mid_l[0];
            window_mid_l[2] <= window_mid_l[1];
         end
      end
   end

   // delay buffer delay delays by delay_p, but we want it one cycle earlier
   delaybuffer #(.width_p(2 * width_p), .delay_p(linewidth_px_p - 3 - 1))
     delay_buf_inst1
       (
        // Outputs
        .ready_o                        (),
        .valid_o                        (),
        .data_o                         (delaybuf1_out_w),
        // Inputs
        .clk_i                          (clk_i),
        .reset_i                        (reset_i),
        .data_i                         (window_mid_l[2]),
        .valid_i                        (enable_w),
        .ready_i                        (1'b1));

   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         window_tail_l[0] <= '0;
         window_tail_l[1] <= '0;
         window_tail_l[2] <= '0;
      end else begin
         if (enable_w) begin
            window_tail_l[0] <= delaybuf1_out_w;
            window_tail_l[1] <= window_tail_l[0];
            window_tail_l[2] <= window_tail_l[1];
         end
      end
   end

   assign data_o = '0 + (window_tail_l[2] + window_tail_l[1] + window_tail_l[0]) +
                   (window_mid_l[2] + window_mid_l[1] + window_mid_l[0]) +
                   (window_head_l[2] + window_head_l[1] + window_head_l[0]);
endmodule
