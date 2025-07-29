  <figure>
    <img src="https://github.com/kwyip/txt_to_pickle/blob/main/logo.png?raw=True" alt="logo" height="143" />
  </figure>

[![](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/kwyip/txt_to_pickle/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/txt_to_pickle)](https://pypi.org/project/txt_to_pickle/)
[![Static Badge](https://img.shields.io/badge/CalVer-2025.0416-ff5733)](https://pypi.org/project/txt_to_pickle)
[![Static Badge](https://img.shields.io/badge/PyPI-wheels-d8d805)](https://pypi.org/project/txt_to_pickle/#files)
[![](https://pepy.tech/badge/txt_to_pickle/month)](https://pepy.tech/project/txt_to_pickle)

[txt_to_pickle](https://txt_to_pickle.github.io/)
===============================================

txt_to_pickle is a method turning a txt file to a pickle file. 

In layman&#39;s terms, it automates conversion by:

1.  turning a txt file to a list,
2.  saving a list to a pickle file.

#### Input:

*   `input.txt` – A [txt](https://en.wikipedia.org/wiki/Text_file)
        file containing data.</li>
*   `data_length` – Length of the txt file containing data for each segnment.

#### Output:

*   `output.pkl` – A pickle file of a list.

* * *

Installation
------------

It can be installed with `pip`, ideally by using a [virtual environment](https://realpython.com/what-is-pip/#using-pip-in-a-python-virtual-environment). Open up a terminal and install the package and the dependencies with:  
  

    `pip install txt_to_pickle`

_or_

    `python -m pip install txt_to_pickle`

  
_🐍 This requires Python 3.8 or newer versions_

* * *

### Steps to convert txt file to pickle file

1.  **Prepare the input file (i.e., a txt file containing data)**.
2.  **Know how long the data is for each segment (`data_length`)**:  
      
    
           `txt_to_pickle input.txt data_length output.pkl`


* * *

### Test

You may test the installation using the sample input file (`input_string_list.pkl`) located in the test folder.

---

♥ Lastly executed on Python `3.10` on 2025-06-12.