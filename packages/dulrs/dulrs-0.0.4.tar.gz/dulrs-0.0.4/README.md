# API

## Download 

Please download 'Template.zip'.

### Description of Folders

- **datasets**: This folder holds the raw datasets used for the project. 
- **export**: This folder is for files that include models.
- **result**: This folder is for pretrained model parameters
- **mats**: This directory stores MATLAB-related files, such as `.mat` files or other results generated during computation.
- **your script**: Your script should be placed at the same level as 'export'

## Usage Guide for `dulrs` Package

The `dulrs` package provides tools to calculate and visualize some evaluation matrix (heatmap, low-rankness, sparsity)of our models on various scenarios from different datasets.

### Installation

First, install the package using `pip`:

```bash
pip install dulrs
```

### Importing the Package

Import the package in your Python script:

```python
from dulrs import dulrs_class
```

### Available Functions

The package includes the following functions:

0. `dulrs_class(model_name, model_path, use_cuda=True)`
1. `dulrs_class.heatmap(img_path, data_name,output_mat,output_png)`
2. `dulrs_class.lowrank_cal(img_path, model_name, data_name, save_dir)`
3. `dulrs_class.lowrank_draw(model_name, data_name, mat_dir, save_dir)`
4. `dulrs_class.sparsity_cal(img_path, model_name, data_name, save_dir)`

### Function Descriptions and Examples

#### 0. `dulrs_class(model_name, model_path, use_cuda=True)`
The `dulrs_class` in the `dulrs` package is used to initialize the models with pretrained parameters and including following fucntions.

#### 1. `dulrs_class.heatmap(img_path, data_name, output_mat, output_png)`

The `dulrs_class.heatmap` function in the `dulrs` package allows users to draw and save the heatmaps obtained from different stages.

#### 2. `dulrs_class.lowrank_cal(img_path, model_name, data_name, save_dir)`

The `dulrs_class.lowrank_cal` function in the `dulrs` package allows users to calculate and save the low-rankness data with mat format.

#### 3. `dulrs_class.lowrank_draw(model_name, data_name, mat_dir, save_dir)`

The `dulrs_class.lowrank_draw` function in the `dulrs` package allows users to draw the low-rankness figure based on the calculated low-rankess data and save with png format.

#### 4. `dulrs_class.sparsity_cal(img_path, model_name, data_name, save_dir)`

The `dulrs_class.sparsity_cal` function in the `dulrs` package allows users to calculate and save the sparsity data with mat format.


#### Function Parameters

The `dulrs_class` accepts the following parameters:
- `model_name`: refer to the model which is underestimated.
- `model_path`: the pretrained parameters pkl path.
- `use_cuda`: Determined whether use GPU for acceleration.

The `dulrs_class.heatmap` function accepts the following parameters:
- `img_path`: refer to the testing image.
- `data_name`: refer to the name of testing image.
- `output_mat`: save path for result with mat format.
- `output_png`: save path for result with png format.

The `dulrs_class.lowrank_cal` function accepts the following parameters:
- `img_path`: refer to the testing image set.
- `model_name`: refer to the model which is underestimated.
- `data_name`: refer to the name of testing image.
- `save_dir`: save path for low-rankness result with mat format.

The `dulrs_class.lowrank_draw` function accepts the following parameters:
- `model_name`: refer to the model which is underestimated.
- `data_name`: refer to the name of testing image.
- `mat_dir`: refer to the path for low-rankess result.
- `save_dir`: save path for low rankness result with png format.

The `dulrs_class.sparsity_cal` function accepts the following parameters:
- `img_path`: refer to the testing image set.
- `model_name`: refer to the model which is underestimated.
- `data_name`: refer to the name of testing image.
- `save_dir`: save path for sparsity result with mat format.

#### Examples

1. **For given model RPCANet9**

    Place the following script at the same level as file 'export' 

   ```python
    from dulrs import dulrs_class
    # Initial model
    dulrs = dulrs_class(
        model_name="rpcanet9", 
        model_path="./result/best.pkl",     # Path for pretrained parameters
        use_cuda=True)

    # For heatmap generation
    heatmap = dulrs.heatmap(
        img_path="./datasets/NUDT-SIRST/test/images/000001.png",
        data_name="NUDT-SIRST_test_images_000001",
        output_mat="./heatmap/mat",  # If users want to save the data as mat format. Default=None
        output_png="./heatmap/png"   # If users want to save the figure as png format. Default=None
    )

    # For lowrank calculation
    lowrank_matrix = dulrs.lowrank_cal(
        img_path="./datasets/NUDT-SIRST/test/images",
        model_name="rpcanet9",
        data_name="NUDT-SIRST",
        save_dir= './mats/lowrank' # Save path for result with mat format
    )

    # For lowrank paint based on calculation
    lowrank_matrix_draw = dulrs.lowrank_draw(
        model_name="rpcanet9",
        data_name="NUDT-SIRST",
        mat_dir= './mats/lowrank',         
        save_dir = './mats/lowrank/figure' # Save path for result with png format
    )

    # For sparsity calculation
    sparsity_matrix = dulrs.sparsity_cal(
        img_path="./datasets/NUDT-SIRST/test/images",
        model_name="rpcanet9",
        data_name="NUDT-SIRST",
        save_dir = './mats/sparsity'        # Save path for result with mat format
    )
   ```

