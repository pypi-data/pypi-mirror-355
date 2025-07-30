# TransBrain

TransBrain is an integrated computational framework for bidirectional translation of brain-wide phenotypes between humans and mice. Specifically, TransBrain provides a systematic approach for cross-species quantitative comparison and mechanistic investigation of both normal and pathological brain functions.

![TransBrain_FIG1](./figure/transbrain_fig1.jpg)

What can TransBrain do?

1. Exploring the similarity relationships at the transcriptional level.

2. Inferring the conservation of whole-brain phenotypes.

3. Transforming and annotating whole-brain functional circuits.

4. Linking specific mouse models with human diseases.

## Further Reading

If you wish to learn more about the construction details of this method, please refer to our article: [https://www.biorxiv.org/content/10.1101/2025.01.27.635016v1](https://www.biorxiv.org/content/10.1101/2025.01.27.635016v1) (in preprint).


## Installation
TransBrain is on pypi: https://pypi.org/project/transbrain/

To install TransBrain as a package, run:

```sh
pip install transbrain
```

You can also create a conda environment from the environment.yml file:

* First, clone this repository,
```sh
git clone https://github.com/ibpshangzheng/transbrain.git
```

* Then, create the environment,
```sh
cd transbrain
conda env create -f environment.yml
```

* Activate the environment,
```sh
conda activate transbrain_env
```

## Python Dependencies

The project mainly depends on Python (>= 3.8.5).

```
matplotlib==3.7.5,
matplotlib-inline==0.1.7,
nibabel==5.2.1,
nilearn==0.10.4,
numpy==1.24.4,
openpyxl==3.1.5,
pandas==2.0.3,
scikit-learn==1.3.2,
scipy==1.10.1,
seaborn==0.13.2,
six==1.17.0
```
See full list in environment.yml file. 

## Unit Test

- We provide a [Python Unit Test](https://www.dataquest.io/blog/unit-tests-python/) module to check whether the installation was successful.
- Clone our repository and run this file. Make sure you are in the ​**root directory**​ (where `test_transbrain.py` is located) before running the test.

### File Structure

    transbrain-main/
    ├── transbrain/
    │ └── exampledata/
    ├── test_transbrain.py # Unit Test file
    └── tests/ # Verification files


```bash
python test_transbrain.py
```

- If you see the message ``🎉 TransBrain installed successfully!!!``, it means that TransBrain is ready to use.


## Getting Started
### Usage
- After installation, you can refer to the [**basic usage notebook**](./tests/basic_usage.ipynb) in the root directory of TransBrain to explore usage examples and other functions.
- You can see detailed documentation of TransBrain [here](https://transbrain.readthedocs.io/en/latest/)
- We also provide a [online mapping website](https://transbrain.streamlit.app/), which enables users to directly upload your data for online mapping and visualization.


```python
import pandas as pd
import transbrain as tb

#Initialize TransBrain for specific atlas
Transformer = tb.trans.SpeciesTrans('bn')
```

```python
# Example from mouse to human
mouse_phenotype = pd.read_csv('./transbrain/exampledata/mouse/mouse_all_example_data.csv',index_col=0)
mouse_phenotype_in_human = Transformer.mouse_to_human(mouse_phenotype, region_type='all', normalize=True)
```

```python
# Example from human to mouse
human_phenotype = pd.read_csv('./transbrain/exampledata/human/bn/human_bn_all_example_data.csv',index_col=0)
human_phenotype_in_mouse = Transformer.human_to_mouse(human_phenotype, region_type='all', normalize=True)
```

```python
# Get human phenotypes from nii file
human_atlas = tb.atlas.fetch_human_atlas(atlas_type='bn',region_type='cortex')
phenotype_nii_path = ('./transbrain/exampledata/human/human_example_phenotype_data.nii.gz')
human_phenptype_extracted = tb.base.get_region_phenotypes(phenotype_nii_path, atlas_dict = human_atlas)
```

```python
# Get mouse phenotypes from nii file
mouse_atlas = tb.atlas.fetch_mouse_atlas(region_type='all')
phenotype_nii_path = ('./transbrain/exampledata/mouse/mouse_example_phenotype_data.nii.gz')
mouse_phenptype_extracted = tb.base.get_region_phenotypes(phenotype_nii_path, atlas_dict = mouse_atlas)
```


```python
# Get graph embeddings 
Transformer = tb.trans.SpeciesTrans('bn')
Human_Mouse_embedding_bn = Transformer._load_embeddings()
```

This allows seamless integration into your existing workflows. 🚀


### Toturials
We provided [**Tutorial Cases**](tutorials/README.md) demonstrating how to apply TransBrain for cross-species translation and comparison, which includes:

* Analyzing and visualizing transcriptional similarity between humans and mice.

* Characterizing the evolutionary spectrum of resting-state fMRI network phenotypes.

* Annotating the optogenetic circuits in mice using Neurosynth.

* Linking gene mutations to imaging phenotype deviations in autism.

The analysis process and figures can be viewed in the Jupyter Notebook. The necessary files and datas for completing these analysis are included in the notebook's folder.



## License
This project is covered under the Apache 2.0 License.

## Support
For questions and comments, please file a Github issue and/or email Shangzheng Huang(huangshangzheng@ibp.ac.cn)


