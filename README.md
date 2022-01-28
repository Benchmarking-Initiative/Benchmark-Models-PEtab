# Benchmark-Models-PEtab
A collection of mathematical models with experimental data in the [PEtab](https://github.com/PEtab-dev) format as benchmark problems in order to evaluate new and existing methodologies for data-based modelling. The publication for the introduction and analysis of the benchmark problem collection is available at https://academic.oup.com/bioinformatics/article/35/17/3073/5280731.

Contributions to the collection are very welcome. For this, please create a new branch, add your model and test your files with the provided functions, and start a pull request. We will then check your model and merge it into the collection. We are continuously working on the extension of the collection.

## Overview
| Model ID                            |   Conditions |   Estimated Parameters |   Events | Preequilibration   | Postequilibration   |   Measurements |   Observables |   Species |
|:------------------------------------|-------------:|-----------------------:|---------:|:-------------------|:--------------------|---------------:|--------------:|----------:|
| Alkan_SciSignal2018                 |           73 |                     56 |        0 | No                 | No                  |           1733 |            12 |        36 |
| Bachmann_MSB2011                    |           36 |                    113 |        0 | No                 | No                  |            541 |            20 |        25 |
| Beer_MolBioSystems2014              |           19 |                     72 |        1 | No                 | No                  |          27132 |             2 |         4 |
| Bertozzi_PNAS2020                   |            2 |                      3 |        1 | No                 | No                  |            138 |             1 |         3 |
| Blasi_CellSystems2016               |            1 |                      9 |        0 | No                 | Yes                 |            252 |            15 |        16 |
| Boehm_JProteomeRes2014              |            1 |                      9 |        0 | No                 | No                  |             48 |             3 |         8 |
| Borghans_BiophysChem1997            |            1 |                     23 |        0 | No                 | No                  |            111 |             1 |         3 |
| Brannmark_JBC2010                   |            8 |                     22 |        1 | Yes                | No                  |             43 |             3 |         9 |
| Bruno_JExpBot2016                   |            6 |                     13 |        0 | No                 | No                  |             77 |             5 |         7 |
| Chen_MSB2009                        |            4 |                    155 |        6 | No                 | No                  |            120 |             3 |       500 |
| Crauste_CellSystems2017             |            1 |                     12 |        0 | No                 | No                  |             21 |             4 |         5 |
| Elowitz_Nature2000                  |            1 |                     21 |        0 | No                 | No                  |             58 |             1 |         8 |
| Fiedler_BMC2016                     |            3 |                     22 |        0 | No                 | No                  |             72 |             2 |         6 |
| Fujita_SciSignal2010                |            6 |                     19 |        1 | No                 | No                  |            144 |             3 |         9 |
| Giordano_Nature2020                 |            1 |                     50 |       14 | No                 | No                  |            313 |             7 |        13 |
| Isensee_JCB2018                     |          123 |                     46 |        8 | Yes                | No                  |            687 |             3 |        25 |
| Laske_PLOSComputBiol2019            |            3 |                     13 |        0 | No                 | No                  |             42 |            13 |        41 |
| Lucarelli_CellSystems2018           |           16 |                     84 |        0 | No                 | No                  |           1755 |            65 |        33 |
| Okuonghae_ChaosSolitonsFractals2020 |            1 |                     16 |        0 | No                 | No                  |             92 |             2 |         9 |
| Oliveira_NatCommun2021              |            1 |                     12 |        1 | No                 | No                  |            120 |             2 |         9 |
| Perelson_Science1996                |            1 |                      3 |        0 | No                 | No                  |             16 |             1 |         4 |
| Rahman_MBS2016                      |            1 |                      9 |        0 | No                 | No                  |             23 |             1 |         7 |
| Raimundez_PCB2020                   |          170 |                    136 |        3 | Yes                | No                  |            627 |            79 |        22 |
| SalazarCavazos_MBoC2020             |            4 |                      6 |        0 | No                 | No                  |             18 |             3 |        75 |
| Schwen_PONE2014                     |           19 |                     30 |        0 | No                 | No                  |            286 |             4 |        11 |
| Sneyd_PNAS2002                      |            9 |                     15 |        0 | No                 | No                  |            135 |             1 |         6 |
| Weber_BMC2015                       |            2 |                     36 |        4 | Yes                | No                  |            135 |             8 |         7 |
| Zhao_QuantBiol2020                  |            7 |                     28 |        0 | No                 | No                  |             82 |             1 |         5 |
| Zheng_PNAS2012                      |            1 |                     46 |        0 | Yes                | No                  |             60 |            15 |        15 |

## License

Any original content in this repository may be used under the terms of the [BSD-3-Clause license](LICENSE).
Different terms may apply to models and datasets, for which we refer the user to the original publications
that are referenced in the respective SBML files.
