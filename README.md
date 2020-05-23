# your
`your` stands for Your Unified Reader. This library reads sigproc filterbanks, psrfits, and psrdada formats and can go from one format to another.

| Format        | Read                     | Write               |
| ------------- |:-------------:           | -----:              |
| filterbank    | :white_check_mark:       | :white_check_mark:  |
| psrfits       | :white_check_mark:       | :x:                 |
| psrdada       | :x:                      | :white_check_mark:  |

The inspiration for the name comes from the Daily Dose of Internet [videos](https://www.youtube.com/channel/UCdC0An4ZPNr_YiFiYoVbwaw).

# Installation
First you need to install [psrdada-python](https://github.com/AA-ALERT/psrdada-python).
Once psrdada is installed, git clone the repo and use `setup.py` to install `your`.

    git clone https://github.com/devanshkv/your.git
    cd your
    python setup.py install

Have a look at our [docs](https://devanshkv.github.io/your/) for the basic documentation. We will add detail shortly. 