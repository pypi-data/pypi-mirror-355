# si4pipeline-gui

[![PyPI - Version](https://img.shields.io/pypi/v/si4pipeline-gui)](https://pypi.org/project/si4pipeline-gui/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/si4pipeline-gui)](https://pypi.org/project/si4pipeline-gui/)
[![PyPI - License](https://img.shields.io/pypi/l/si4pipeline-gui)](https://pypi.org/project/si4pipeline-gui/)

This package provides the user-friendly graphical user interface (GUI) for the [`si4pipeline`](https://github.com/Takeuchi-Lab-SI-Group/si4pipeline) package, which allows users to perform a statistical test for any feature selection pipeline by selective inference.
The technical details of the statistical test methods are described in the paper "[Statistical Test for Feature Selection Pipelines by Selective Inference](https://arxiv.org/abs/2406.18902)".


## Requirements
This package has the following dependencies:
- Python (version 3.10 or higher, we use 3.12.10)
- si4pipeline (version 1.0.1 or higher)
- streamlit (version 1.45.0 or higher)
- barfi (version 1.1.0)


## Installation and Usage

You can install this package from the PyPI using pip.
```
pip install si4pipeline-gui
```

Run the application:
```
si4pipeline-gui
```

Then, you can access the GUI by opening the browser and go to the following URL:
```http://localhost:8501```

> **Note**
> When the application is launched for the first time, the application creates a directory in your home folder to store pipeline definitions:
> ```~/.si4pipeline_gui/```



## Installation from code repository
If you want to install the latest version of this package from the [code repository](https://github.com/ni-shu/si4pipeline-gui), please clone the repository and install it as follows:
1. Clone the repository:
2. Change the directory to the cloned repository:
   ```
   cd si4pipeline-gui
   ```
3. Install the required dependencies:
    ```
    pip install si4pipeline==1.0.1
    pip install streamlit==1.45.0
    pip install barfi==1.1.0
    ```
4. Run the application:
    ```
    cd si4pipeline_gui
    streamlit run app.py
    ```
    Then, you can access the demo by opening the browser and go to the following URL:
    ```http://localhost:8501```
