# RSML.Python
Adds [RedSeaMarkupLanguage]("https://github.com/OceanApocalypseStudios/RedSeaMarkupLanguage) support for Python.

## Get Started
```py
# RSML.Python is not a port of RSML, as the original executable is required
executable = RedSeaCLIExecutable(...)

document = RedSeaDocument()
document.load_from_string(...)

executable.load_document(document)

output = executable.evaluate_document() # non-prettified output
print(output)
```

> **Made with :heart: by OceanApocalypseStudios.**
> 
> *Copyright (c) 2025 OceanApocalypseStudios*
