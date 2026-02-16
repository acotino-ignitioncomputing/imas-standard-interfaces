# Examples of (in)valid netCDF datasets

This folder contains three minimal CDL descriptions of netCDF-datasets. One CDL-
description (`valid_pf_passive.cdl`) is valid with respect to the interface
 definition of `pf_passive`, while the remaining two are invalid.

The Linux tool `ncgen` can be used to generate netCDF datasets from these
CDL-files:

```bash
ncgen -k 4 -o output_file.nc valid_pf_passive.cdl
```

where the flag  `-k 4` indicates the usage of the netCDF-4 format.
