##  PU-CGCNN-based Models for CR and NCR Classifier of MOFs (MOFClassifier).
                                                                                                                                          
[![Static Badge](https://img.shields.io/badge/chemrxiv-2025.nvmnr.v1-brightgreen?style=flat)](https://doi.org/10.26434/x)
![GitHub repo size](https://img.shields.io/github/repo-size/sxm13/NCRChecker?logo=github&logoColor=white&label=Repo%20Size)
[![PyPI](https://img.shields.io/pypi/v/NCRChecker?logo=pypi&logoColor=white)](https://pypi.org/project/NCRChecker?logo=pypi&logoColor=white)
[![Requires Python 3.9](https://img.shields.io/badge/Python-3.9-blue.svg?logo=python&logoColor=white)](https://python.org/downloads)
[![GitHub license](https://img.shields.io/github/license/sxm13/NCRChecker)](https://github.com/sxm13/NCRChecker/blob/main/LICENSE)
[![Downloads](https://pepy.tech/badge/NCRChecker)](https://pepy.tech/project/NCRChecker)
[![GitHub issues](https://img.shields.io/github/issues/sxm13/NCRChecker.svg)](https://GitHub.com/sxm13/NCRChecker/issues/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.x.svg)](https://doi.org/10.5281/zenodo.x)
                         
### Installation 
                                     
```sh
pip install MOFClassifier
```

### Examples                                                                                                     
```python
from MOFClassifier import predict
cifid, CLscores, CLscore = predict(root_cif="./example.cif")
```
-  **root_cif**: the path of your structure
-  **cifid**: the name of structure
-  **CLscores**: the CLscore predicted by 100 models (bags)
-  **CLscore**: the mean CLscore of **CLscores**
                                                                                
### Citation                                          
**Guobin Zhao**, **Pengyu Zhao** and **Yongchul G. Chung**. 2025. **ChemRxiv**.
