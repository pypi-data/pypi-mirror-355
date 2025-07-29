                   `adder` Parameters                    
                                                         
| Name           | Dimension | Functional Description   |
|----------------|-----------|--------------------------|
| `DATA_WIDTH`   |           | Width of input operands  |
| `OUTPUT_WIDTH` |           | Test configuration value |
                                                         
                               `adder` Interface                                
                                                                                
| Name          | Dimension          | I/O      | Functional Description       |
|---------------|--------------------|----------|------------------------------|
| `A`           | `[DATA_WIDTH-1:0]` | `input`  | Packed input operand A       |
| `B`           | `[DATA_WIDTH-1:0]` | `input`  | Packed input operand B       |
| `X`           | `[DATA_WIDTH:0]`   | `output` | Packed sum output            |
| `byte_p`      | `[7:0]`            | `input`  | Packed byte input            |
| `word_p`      | `[3:0][7:0]`       | `input`  | Packed 32-bit word (4 bytes) |
| `flag_u`      | `1`                | `input`  | Unpacked single bit          |
| `arr_u [0:3]` | `[7:0]`            | `input`  | Unpacked byte array          |
                                                                                
