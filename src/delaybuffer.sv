module delaybuffer
  #(parameter [31:0] width_p = 8
   ,parameter [31:0] delay_p = 8
    ,parameter [$clog2(delay_p):0] delay_p_l = delay_p[$clog2(delay_p):0]
   )
  (input [0:0] clk_i
  ,input [0:0] reset_i

  ,input [width_p - 1:0] data_i
  ,input [0:0] valid_i
  ,output [0:0] ready_o 

  ,output [0:0] valid_o 
  ,output [width_p - 1:0] data_o 
  ,input [0:0] ready_i
  );

   // enum logic [0:0] { IDLE='0, IHVD=1'b1 } state_d_n, state_q_r;
   // logic [width_p - 1: 0] shifts_w [delay_p:0];
   wire                          hs_w;
   logic [$clog2(delay_p):0] rd_ptr_r, rd_ptr_n, wr_ptr_r, wr_ptr_n;
   logic valid_l;


   assign valid_o = valid_l;
   assign ready_o = ~valid_o | ready_i;
   assign hs_w = ready_o && valid_i;

   // ready valid state machine
   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         valid_l <= '0;
      end else begin
         if (ready_o) begin
            valid_l <= valid_i;
         end
      end
   end

   // Roll counter for rd and wr pointers.  wr_ptr is initialized to be at the tail end of the RAM to implement delay
   always_comb begin
      rd_ptr_n = rd_ptr_r;
      wr_ptr_n = wr_ptr_r;
      if (hs_w) begin
         if (rd_ptr_r == (delay_p_l)) begin
            rd_ptr_n = '0;
         end else begin
            rd_ptr_n = rd_ptr_r + 1;
         end

         if (wr_ptr_r == (delay_p_l)) begin
            wr_ptr_n = '0;
         end else begin
            wr_ptr_n = wr_ptr_r + 1;
         end
      end
   end
   // implement the delay by creating constant distance between rd and wr ptr
   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         rd_ptr_r <= '0;
         wr_ptr_r <= (delay_p_l);
      end else begin
         rd_ptr_r <= rd_ptr_n;
         wr_ptr_r <= wr_ptr_n;
      end
   end

   // we overallocate one log_2 level more RAM to prevent possible width truncation issues with RAM address
   // also zero init because simulating uart disallows special values (i.e. 'X')
   ram_1r1w_sync #(.WIDTH_P(width_p), .DEPTH_P(1 << ($clog2(delay_p)+1)), .ZERO_INIT(1))
       ram
       (.clk_i(clk_i),
        .reset_i(reset_i),
        .rd_addr_i(rd_ptr_r),
        .wr_addr_i(wr_ptr_r),
        .wr_data_i(data_i),
        .wr_valid_i(hs_w),
        .rd_valid_i(hs_w),
        .rd_data_o(data_o));

endmodule
