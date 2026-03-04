module ram_1r1w_sync
  #(parameter WIDTH_P=8,
    parameter DEPTH_P=256,
    parameter ZERO_INIT=0)
   (input clk_i
    ,input reset_i
    ,input [0:0] wr_valid_i
    ,input [WIDTH_P - 1:0] wr_data_i
    ,input [$clog2(DEPTH_P) - 1 : 0] wr_addr_i

    ,input [0:0] rd_valid_i
    ,input [$clog2(DEPTH_P) - 1 : 0] rd_addr_i
    ,output [WIDTH_P-1:0] rd_data_o);

   logic [WIDTH_P - 1 : 0] mem[DEPTH_P - 1 : 0];
   logic [$clog2(DEPTH_P) - 1 : 0] rd_addr_r;

   // this is only because UART module refuses to process X inputs
`ifndef SYNTHESIS
   initial begin
      if (ZERO_INIT) begin
         for (int i = 0; i < DEPTH_P; i++) begin
            mem[i] = '0;
         end
      end
   end
`endif

   // assign rd_data_o = rd_data_r;
   assign rd_data_o = mem[rd_addr_r];

   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         rd_addr_r <= '0;
      end else begin
         if (rd_valid_i) begin
            rd_addr_r <= rd_addr_i;
         end
      end
   end

   always_ff @(posedge clk_i) begin
      if (!reset_i) begin
         if (wr_valid_i) begin
            mem[wr_addr_i] <= wr_data_i;
         end
      end
   end
endmodule
