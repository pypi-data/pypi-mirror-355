# Genius Project File Format

- Status: proposed
- Deciders: [Jeff Pike](mailto:jeff.pike@verses.ai), [Quinn Madson](mailto:quinn.madson@verses.ai)
- Date: 2025-05-16

Technical Story: [GPIL-632](https://verses.atlassian.net/browse/GPIL-632)

## Context and Problem Statement

Currently, our VFG file is a single json file containing graph structure, numeric tensors, graph metadata, and graph
display information. It threatens to contain even more data, unrelated to inference. As well, JSON is uniquely unsuited
to storing large quantities of numeric data, which tensors inherently are. Our RAM usage is currently limited by
parsing this JSON file, which takes exponential space to parse. We cannot perform any validation until the file loads,
which usually takes more time to parse than the inference takes to run!

In addition, large JSON files are difficult to work with for both the client and the server. All of the above problems
are also problems in the model editor.

## Decision Drivers

- Efficient, in-place computation
- At least as much representational power as VFG 0.5.0.
- Ability to partially load tensors
- Binary tensor representation
- Ability to load tensors in web-browser javascript
- Ability to load tensors in server-side python
  - Support for other languages is a plus but not a requirement
- Low overhead for saving and loading
- Ability to recover partially-transmitted or corrupted files
- Ability to inspect graph structure independent of tensor loading
- Storage of metadata, especially display-only metadata, separate from the tensors

## Considered Options

- json vfg (no change)
- json vfg + parquet
- json vfg + hdf5
- json vfg + np (single vector)
- json vfg + npz (multi vector)

## Decision Matrix

To systematically evaluate the considered options, we have created a decision matrix. This matrix lists each option in a row and each decision driver in a column. Each cell in the matrix contains a rating that reflects how well the option meets the corresponding decision driver. The rating scale is as follows:

- -5: Extremely Poor
- -3: Poor
- -1: Slightly Negative
- 0: Neutral
- 1: Slightly Positive
- 3: Good
- 5: Excellent

### Example Decision Matrix

| Option \ Driver      | In-place computation | Partial loading | Binary representation | Language Support | Durability | Introspection | Metadata Separation | Total |
|----------------------|----------------------|-----------------|-----------------------|------------------|------------|---------------|---------------------|-------|
| json vfg (no change) | -5                   | -5              | -5                    | 5                | 5          | 5             | -5                  | -5    |
| vfg + parquet        | -3                   | 1               | 5                     | 3                | -1         | -1            | 3                   | 7     | 
| vfg + hdf5           | 5                    | 5               | 5                     | -1               | -5         | -3            | 5                   | 11    |
| vfg + np             | 5                    | 5               | 5                     | 3                | 1          | -5            | 5                   | 19    |
| vfg + npz            | 5                    | 5               | 5                     | 1                | 5          | -5            | 5                   | 21    |

### Example Analysis

No change fails on key metrics. Its complete lack of computational efficiency and binary representation are already
leading to problems, which led to this ADR.

vfg+parquet is a good option, but due to its lack of in-place computation, it will need engineering effort to reach
the same efficiencies of the other libraries.

vfg+hdf5 is a better option, but it falls short due to its lackluster javascript support (it requires a native library,
which is available as a wasm file but is quite large). It also suffers from catastrophic failures under single-byte
corruption, where the entire file cannot be recovered due to a small error in the index. In a distributed system,
such a corruption is easy to trigger and impossible to avoid.

vfg+np and npz score highly on all metrics. npz has slightly higher recoverability, and np has slightly better language
support. If we needed to, we can write a parser for either in-house; but we don't need to, as well-supported third party
libraries for both languages exist.

## Decision Outcome

Option `vfg+npz` has the highest score, tied with `vfg+np`. Thus, under technical merits, either would be a suitable
choice. `vfg+npz` is slightly favoured here as it is easier to work with a variety of tensors rather than a single
tensor, and if a single tensor is later desired, it's trivial to have an array with one element.

Since npz allows for string key to tensor identification, the vfg structure will link to its tensors by certain attributes,
which link to matching keys in the npz file.

## Benchmarks
### NPZ
| Name                                                                                        | Min (ms)            | Max (ms)            | Mean (ms)           | StdDev (ms)        | Median (ms)         | IQR (ms)           | Outliers | OPS            | Rounds | Iterations |
|---------------------------------------------------------------------------------------------|---------------------|---------------------|---------------------|--------------------|---------------------|--------------------|----------|----------------|--------|------------|
| test_load_project_vfg[taxi/taxi_vfg.gpf]                                                    | 7.9559 (1.0)        | 8.8275 (1.0)        | 8.4264 (1.0)        | 0.1531 (1.0)       | 8.4456 (1.0)        | 0.1205 (1.0)       | 20;10    | 118.6749 (1.0) | 87     | 1          |
| test_load_standalone_vfg[taxi/taxi_vfg.json]                                                | 63.8372 (8.02)      | 89.7093 (10.16)     | 73.6617 (8.74)      | 10.8076 (70.58)    | 70.4329 (8.34)      | 17.6017 (146.05)   | 1;0      | 13.5756 (0.11) | 6      | 1          |
| test_load_project_vfg[taxi_vfg_0_3_0.gpf]                                                   | 93.2933 (11.73)     | 98.3392 (11.14)     | 95.4663 (11.33)     | 1.7446 (11.39)     | 94.9592 (11.24)     | 2.4710 (20.50)     | 2;0      | 10.4749 (0.09) | 7      | 1          |
| test_load_standalone_vfg[7500_lines_over_833_areas_transmission_network_23335_factors.json] | 518.4428 (65.16)    | 589.7543 (66.81)    | 553.3912 (65.67)    | 31.2346 (203.99)   | 567.0299 (67.14)    | 52.3509 (434.37)   | 2;0      | 1.8070 (0.02)  | 5      | 1          |
| test_load_standalone_vfg[taxi_vfg_0_3_0.json]                                               | 919.7552 (115.61)   | 1,024.5637 (116.06) | 979.3480 (116.22)   | 39.9670 (261.02)   | 992.2107 (117.48)   | 52.7628 (437.79)   | 2;0      | 1.0211 (0.01)  | 5      | 1          |
| test_load_project_vfg[7500_lines_over_833_areas_transmission_network_23335_factors.gpf]     | 7,749.7313 (974.09) | 8,386.8038 (950.08) | 8,055.4520 (955.98) | 264.3051 (>1000.0) | 8,084.3069 (957.22) | 447.5112 (>1000.0) | 2;0      | 0.1241 (0.00)  | 5      | 1          |
## NP
| Name                                                                                        | Min (ms)          | Max (ms)            | Mean (ms)         | StdDev (ms)     | Median (ms)       | IQR (ms)        | Outliers | OPS            | Rounds | Iterations |
|---------------------------------------------------------------------------------------------|-------------------|---------------------|-------------------|-----------------|-------------------|-----------------|----------|----------------|--------|------------|
| test_load_project_vfg[taxi/taxi_vfg.gpf]                                                    | 1.4460 (1.0)      | 7.6209 (1.0)        | 2.5121 (1.0)      | 1.1998 (1.0)    | 2.1483 (1.0)      | 0.5033 (1.0)    | 21;23    | 398.0658 (1.0) | 148    | 1          |
| test_load_project_vfg[taxi_vfg_0_3_0.gpf]                                                   | 40.7675 (28.19)   | 59.6857 (7.83)      | 49.1265 (19.56)   | 5.2049 (4.34)   | 48.2735 (22.47)   | 3.8586 (7.67)   | 2;2      | 20.3556 (0.05) | 9      | 1          |
| test_load_standalone_vfg[taxi/taxi_vfg.json]                                                | 52.3858 (36.23)   | 57.0627 (7.49)      | 54.1450 (21.55)   | 1.4869 (1.24)   | 53.5980 (24.95)   | 2.2327 (4.44)   | 3;0      | 18.4689 (0.05) | 13     | 1          |
| test_load_standalone_vfg[7500_lines_over_833_areas_transmission_network_23335_factors.json] | 480.3620 (332.20) | 496.7831 (65.19)    | 487.5370 (194.07) | 6.1943 (5.16)   | 486.6516 (226.53) | 8.2160 (16.32)  | 2;0      | 2.0511 (0.01)  | 5      | 1          |
| test_load_standalone_vfg[taxi_vfg_0_3_0.json]                                               | 875.3593 (605.37) | 1,010.3135 (132.57) | 963.0774 (383.37) | 51.5429 (42.96) | 974.3891 (453.57) | 46.6238 (92.63) | 1;1      | 1.0383 (0.00)  | 5      | 1          |
| test_load_project_vfg[7500_lines_over_833_areas_transmission_network_23335_factors.gpf]     | 945.4630 (653.85) | 1,002.4085 (131.53) | 975.6963 (388.39) | 23.0249 (19.19) | 972.6650 (452.77) | 37.0424 (73.60) | 2;0      | 1.0249 (0.00)  | 5      | 1          |


## Links
- Specifications
  - [JSON](https://datatracker.ietf.org/doc/html/rfc7159.html)
  - [Parquet](https://parquet.apache.org/docs/file-format/)
  - [HDF5](https://www.hdfgroup.org/)
  - [NP/NPZ](https://numpy.org/doc/2.2/reference/generated/numpy.lib.format.html)