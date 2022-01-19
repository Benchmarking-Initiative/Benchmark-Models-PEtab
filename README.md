# Benchmark-Models-PEtab
A collection of mathematical models with experimental data in the [PEtab](https://github.com/PEtab-dev) format as benchmark problems in order to evaluate new and existing methodologies for data-based modelling. The publication for the introduction and analysis of the benchmark problem collection is available at https://academic.oup.com/bioinformatics/article/35/17/3073/5280731.

Contributions to the collection are very welcome. For this, please create a new branch, add your model and test your files with the provided functions, and start a pull request. We will then check your model and merge it into the collection. We are continuously working on the extension of the collection.
a
# Optimizer efficiency for benchmark models
|Model name|Optimizer|Overall efficiency|Number of starts|
|:---| :---:| ---:|---:|
|Alkan_SciSignal2018|L-BFGS-B|0.5873002343726723|250
|Bachmann_MSB2011|cg|0.8535095423511391|250
|Beer_MolBioSystems2014|nlopt_11|0.3021393820412641|250
|Bertozzi_PNAS2020|nlopt_42|0.0625368965225103|250
|Blasi_CellSystems2016|nlopt_42|0.062619053603697|250
|Boehm_JProteomeRes2014|nlopt_42|0.0625503158813442|250
|Borghans_BiophysChem1997|nlopt_42|0.0625090423025281|250
|Brannmark_JBC2010|Nelder-Mead|0.0300288309625841|250
|Bruno_JExpBot2016|nlopt_42|0.0624973327924617|250
|Crauste_CellSystems2017|nlopt_42|0.0625128653808899|250
|Elowitz_Nature2000|nlopt_42|0.06251683093855|250
|Fiedler_BMC2016|nlopt_42|0.0625210244076697|250
|Fujita_SciSignal2010|newton-cg|0.2861550080202327|250
|Giordano_Nature2020|Nelder-Mead|0.0782034592682471|250
|Isensee_JCB2018|COBYLA|0.648030745923714|250
|Lucarelli_CellSystems2018|tnc|0.2908116422868182|250
|Okuonghae_ChaosSolitonsFractals2020|nlopt_42|0.0624754021054171|250
|Oliveira_NatCommun2021|L-BFGS-B|0.0125610504744164|250
|Perelson_Science1996|nlopt_42|0.062476295984509|250
|Rahman_MBS2016|SLSQP|0.0361244345719155|250
|Raimundez_PCB2020|fides|0.3226217261103182|250
|SalazarCavazos_MBoC2020|SLSQP|0.3506103769454492|250
|Schwen_PONE2014|newton-cg|0.1201887849471576|250
|Sneyd_PNAS2002|SLSQP|0.1393394787410767|250
|Weber_BMC2015|Nelder-Mead|0.0771565221791643|250
|Zhao_QuantBiol2020|Nelder-Mead|0.0357648294805615|250
|Zheng_PNAS2012|Nelder-Mead|0.0757800686116193|250

## License

Any original content in this repository may be used under the terms of the [BSD-3-Clause license](LICENSE).
Different terms may apply to models and datasets, for which we refer the user to the original publications
that are referenced in the respective SBML files.
