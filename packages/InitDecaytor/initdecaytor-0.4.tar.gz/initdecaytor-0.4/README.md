# InitDecaytor
##### _Thermal decomposition of free-radical initiators_

The purpose of this program is to simulate the thermal decomposition of 
free radical initiators based on literature kinetic data and a set of (virtual)
experimental parameters, such as the concentration and temperature.  

Currently, multiple charges of a variety of radical initiators are supported 
at a constant temperature. The end-time of the experiment can be visually represented
based on a desired threshold of initiator relative to its maximum concentration.

Developed on a fresh python install (v3.13) with the most recent package versions in June 2025. 
In case of issues, please consider updating your packages. 

##### How to get started?
Install InitDecaytor:

```bash
pip install InitDecaytor
```

or upgrade if you've installed a previous version before:

```bash
pip install --upgrade InitDecaytor
```

Create a python script, for example `GUI.py`, containing the following code: 

```python
import InitDecaytor

if __name__ == '__main__':
    app = InitDecaytor.GUI()
    app.run(debug=True)
```

Finally, run the script: 
```bash
python GUI.py
```

This  will generate a link to open the user interface in your browser. (Ctrl+)Click the link or copy-paste it manually. Tested with Microsoft Edge.

##### License

InitDecaytor is available free of charge under an MIT License. 
See the LICENCE file for more details.


##### Changelog

###### 0.4
* All important basic functions are now included in the GUI 
  * Some invalid combinations of input elements are now captured
  * Everything seems to work fine, but no thorough checks for bugs performed yet

###### 0.3
* Initial GUI

###### 0.2
* Temperature profiles supported
  * CSV file from the Huber SpyControl software be imported
  * Should be readily expandable to other CSV formats/layouts

###### 0.1
* Initial release



