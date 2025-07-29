# Install from PyPi
`pip install zikomo`
`pip install -U zikomo`
`pip install --no-cache-dir -U package_name`

# Install CLI from source
`pip install .`

# Uninstall
`pip uninstall zikomo`
-------------------------------------------------------
# COMMANDS
`zikomo deploy --staging --project=backoffice`
`zikomo deploy --staging --project=websites`
`mini update log database on staging`
`zikomo --help`
`pip show zikomo`
------------------------------------------------------
# DevOps Workflow
1. `zikomo deploy backoffice to staging`
2. `zikomo deploy websites to staging`
3. `zikomo update master database on staging`
4. `zikomo update client database on staging`
------------------------------------------------------
# Distribute package
#### Run the commands from the directory where `setup.py` is available
1. `pip install twine build`
2. `python -m build`
3. `twine upload dist/*`

### PyPi URL
`https://pypi.org/project/zikomo/1.0.0/`
-------------------------------------------------------
## STORE PYPI CREDENTIALS
1. %USERPROFILE%\.pypirc
Add the following content:
```[distutils]
index-servers =
    pypi

[pypi]
username = imran.shah
password = pypi-<token>
```


# Test directly
python __main__.py deploy backoffice to staging
python __main__.py deploy websites to staging
python __main__.py reboot uat server
python __main__.py update log database on staging
python __main__.py migrate log database on staging
