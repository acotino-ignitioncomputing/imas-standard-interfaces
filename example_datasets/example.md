# Examples of (in)valid netCDF datasets

This folder contains three minimal CDL descriptions of netCDF-datasets
containting dummy data. One CDL-description (`valid_efit++_input.cdl`) is valid
 with respect to the interface definition `efit++_input_1.yaml` in folder
 `example_definitions/Data_Dictionary_v_3.42.0/efit++/input_interfaces/`, while
 the remaining two CDL-descriptions are invalid.

The Linux tool `ncgen` can be used to generate netCDF datasets from these
CDL-files:

```bash
ncgen -k 3 -o output_file.nc valid_efit++_input.cdl
```

where the flag `-k 3` indicates the usage of the netCDF classic format.
