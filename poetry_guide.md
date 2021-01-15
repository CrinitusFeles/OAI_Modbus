# Poetry guide

1) Install poetry to your python environment.
> pip install poetry

2) Create your packet configuration:
>poetry new ***your-package-name***

It will create folder _'your-package-name'_ which will consist: 
- _'your-package-name'_ folder with init file
- _'tests'_ folder 
- _.tomle_ file where you can define your package configuration
- _Readme.md_

3) Move your .py files into _'your-package-name'_ folder.

4) After that you have to open __init__.py file and add all dependencies. Example of __init__.py:
```\__version__ = '0.1.1'

from .OAI_Modbus import OAI_Modbus
```

5) If your code does not have errors you can build your package

>poetry build

It will create folder _'dist'_ wich has two files _'your_packege_name-version'.tar.gz_ and _'your_packege_name-version'.whl_ 
It is the package of your python module. After this, your can publish your package on your github repository.

For this go to your github repository and create a new release, where you should specify _"tag version"_ and attach your _.tar.gz_ and _.whl_ files.
