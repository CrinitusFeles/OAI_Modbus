# Poetry guide

1) Install poetry to your python environment.
> pip install poetry

2) For creating packet configuration you can use these methods:

    1) In the folder of your project do:
    > poetry init

    It will start the process of initialization of your project. In command-line poetry propose your define such project parameters like:
    >Package name,
    Version,
    Description,
    Author,
    License,
    Compatible Python versions

    and also offer to add dependencies interactively. You can write "no" and add dependencies later.
    After this poetry will create .toml file with packet configuration information. 

    Also, you can open this file in any redactor and change any configuration.

    2) If you still dont have your project you can do:

    >poetry new ***your-package-name***

    It will create folder _'your-package-name'_ which will consist: 
    - _'your-package-name'_ folder with init file
    - _'tests'_ folder 
    - _.tomle_ file where you can define your package configuration
    - _Readme.md_

3) If your code does not have errors you can build your package

>poetry build

It will create folder _'dist'_ wich has two files _'your_packege_name-version'.tar.gz_ and _'your_packege_name-version'.whl_ 
It is the package of your python module. After this, your can publish your package on your github repository.

For this go to your github repository and create a new release, where you should specify _"tag version"_, _"release title"_ and attach your _.tar.gz_ and _.whl_ files.