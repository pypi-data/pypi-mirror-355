                `param_module` Parameters                 
                                                          
| Name             | Dimension | Functional Description  |
|------------------|-----------|-------------------------|
| `WIDTH`          |           | Width of the input data |
| `DEPTH`          |           |                         |
| `INIT_VAL`       | `[7:0]`   |                         |
| `ENABLE_FEATURE` |           |                         |
                                                          
                     `param_module` Interface                      
                                                                   
| Name        | Dimension     | I/O      | Functional Description |
|-------------|---------------|----------|------------------------|
| `clk`       | `1`           | `input`  |                        |
| `rst_n`     | `1`           | `input`  | active-low reset       |
| `data_in`   | `[WIDTH-1:0]` | `input`  | Input data             |
| `data_out`  | `[WIDTH-1:0]` | `output` |                        |
| `bidir_bus` | `[DEPTH-1:0]` | `inout`  |                        |
                                                                   
               `sub_module` Parameters               
                                                     
| Name         | Dimension | Functional Description |
|--------------|-----------|------------------------|
| `DATA_WIDTH` |           |                        |
| `INIT_VALUE` | `[7:0]`   |                        |
                                                     
                           `sub_module` Interface                           
                                                                            
| Name          | Dimension            | I/O      | Functional Description |
|---------------|----------------------|----------|------------------------|
| `clk`         | `1`                  | `input`  |                        |
| `reset`       | `1`                  | `input`  |                        |
| `input_data`  | `[DATA_WIDTH-1:0]`   | `input`  |                        |
| `output_data` | `[DATA_WIDTH-1:0]`   | `output` |                        |
| `config_bus`  | `[DATA_WIDTH/2-1:0]` | `inout`  |                        |
                                                                            
