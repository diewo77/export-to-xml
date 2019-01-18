from cx_Freeze import setup, Executable

base = None

executables = [Executable("main.py", base=base)]

packages = ["idna", "pyodbc", "xml.etree.cElementTree", "datetime"]
options = {
    'build_exe': {
        'packages': packages,
    },
}

setup(
    name="dbToXML",
    options=options,
    version="0.1",
    description='let\'s try',
    executables=executables
)
