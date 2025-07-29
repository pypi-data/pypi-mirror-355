"""
RSML.Python
=============
Matthew (MF366) from OceanApocalypseStudios
MIT License
"""

import subprocess


class RedSeaDocument:
    """
    RedSeaDocument
    ==============
    Represents a RedSeaMarkupLanguage document.
    """
    
    def __init__(self):
        """
        __init__
        ================
        Creates a new empty document.
        """
        
        self._rsml: str = ""
        
    def load_from_file(self, filepath: str, encoding: str = 'utf-8'):
        """
        load_from_file
        ================
        Loads a document from a file at a given filepath.

        :param str filepath: file to load RSML from
        :param str encoding: encoding to open the file with, defaults to 'utf-8'
        """
        
        with open(filepath, "r", encoding=encoding) as f:
            self._rsml = f.read()
            
    def load_from_string(self, data: str):
        """
        load_from_string
        ==================
        Loads a document from a string.

        :param str data: the string containing RSML data
        """
        
        self._rsml = data
        
    def get_document_data(self) -> str:
        """
        get_document_data
        ================
        Returns the loaded data.

        :return str: laoded data
        """
        
        return self._rsml

    def write_document_to_file(self, filepath: str, encoding: str = 'utf-8'):
        """
        write_document_to_file
        ======================
        Writes the loaded data to a file

        :param str filepath: path to the file to write to
        :param str encoding: the encoding to write with, defaults to 'utf-8'
        """
        
        with open(filepath, "w", encoding=encoding) as f:
            f.write(self._rsml)


class RedSeaCLIExecutable:
    """
    RedSeaCLIExecutable
    ===================
    Represents a RSML.CLI executable.
    """
    
    def __init__(self, path_to_executable: str | None = None):
        """
        __init__
        ==================
        Creates a new executable given a path.
        
        If a path isn't given at this stage, it may be given later.

        :param str | None path_to_executable: the path to the executable, defaults to None
        """
        
        self._path_to_executable: str | None = path_to_executable
        self._doc: RedSeaDocument | None = None

    def load_document(self, document: RedSeaDocument):
        """
        load_document
        ===============
        Loads a document in.

        :param RedSeaDocument document: the document to load
        """
        
        self._doc = document
    
    def evaluate_document_as_mfroad(self) -> str:
        """
        evaluate_document_as_mfroad
        =======================
        Evaluates the document as if it was MFRoad.

        :raises ValueError: no executable loaded
        :return str: output
        """
        
        if self._path_to_executable is None:
            raise ValueError("Executable is null.")
        
        process = subprocess.run(
            [self._path_to_executable, "roadlike", "--no-pretty"],
            input='\n'.join(self._doc.write_document_to_new_list()),
            text=True,
            capture_output=True
        )
        
        if process.returncode not in (0, 3):
            process.check_returncode()
        
        return process.stdout
    
    def evaluate_document(self,
                          custom_rid: str | None = None,
                          primary_only: bool = False,
                          fallbacks: tuple[str | None, str] = (None, "[WARNING] No match was found.")) -> str:
        """
        evaluate_document
        ===================
        Evaluates a document.

        :param str | None custom_rid: custom RID to check against, defaults to system RID
        :param bool primary_only: whether to only output primary operator results and errors (true) or to output everything (false), defaults to False
        :param tuple[str | None, str] fallbacks: the error/null message fallbacks, defaults to RSML.CLI's messages
        :raises ValueError: executable not loaded
        :return str: output
        """
        
        if self._path_to_executable is None:
            raise ValueError("Executable is null.")
        
        argument_list: list[str] = [self._path_to_executable, "evaluate", "--no-pretty"]
        
        if fallbacks[0]:
            argument_list.append("--antierror-fallback")
            argument_list.append(fallbacks[0])
            
        argument_list.append("--antinull-fallback")
        argument_list.append(fallbacks[1])
        
        if primary_only:
            argument_list.append("--primary-only")
            
        if custom_rid:
            argument_list.append("--custom-rid")
            argument_list.append(custom_rid)
        
        process = subprocess.run(
            argument_list,
            input='\n'.join(self._doc.write_document_to_new_list()),
            text=True,
            capture_output=True
        )
        
        if process.returncode not in (0, 3):
            process.check_returncode()
        
        return process.stdout
    
    def get_runtime_id(self) -> str:
        """
        get_runtime_id
        ================
        Return the executable's RID.

        :raises ValueError: executable not loaded
        :return str: just the RID
        """
        
        if self._path_to_executable is None:
            raise ValueError("Executable is null.")
        
        argument_list: list[str] = [self._path_to_executable, "get-rid", "--no-pretty"]
        
        process = subprocess.run(
            argument_list,
            text=True,
            capture_output=True
        )
        
        process.check_returncode()
        return process.stdout.split('\n')[0][36:-1] # yes magic number here cry about it
    
    @property
    def version(self) -> str:
        """
        version
        ================
        Returns RSML's version - not the CLI's version and not this module's version.

        :raises ValueError: executable not loaded
        :return str: version, as vX.X.X
        """
        
        if self._path_to_executable is None:
            raise ValueError("Executable is null.")
        
        argument_list: list[str] = [self._path_to_executable, "-V", "--no-pretty"]
        
        process = subprocess.run(
            argument_list,
            text=True,
            capture_output=True
        )
        
        process.check_returncode()
        return process.stdout.split('\n')[0][30:-1] # yes magic number here cry about it
    
    @property
    def repository_python(self) -> str:
        """
        repository_python
        =================
        Returns the link to this module's repository.

        :return str: https://github.com/OceanApocalypseStudios/RSML.Python
        """
        
        return "https://github.com/OceanApocalypseStudios/RSML.Python"

    @property
    def repository(self) -> str:
        """
        repository
        ==================
        Returns the link to RSML's repository.
        
        :return str: https://github.com/OceanApocalypseStudios/RedSeaMarkupLanguage
        """
        
        return "https://github.com/OceanApocalypseStudios/RedSeaMarkupLanguage"


if __name__ == '__main__':
    ### TEST CASES DOWN HERE ###
    ### ALL TESTS PASSING ###    
    EXE_PATH = r"YOUR PATH GOES HERE"
    executable = RedSeaCLIExecutable(EXE_PATH)
    document = RedSeaDocument()
    document.load_from_string('win.+ || "good stuff"\nlinux.+ -> "Hey, Tux"\nwin.+ -> "Hey, corporate greed"\nosx.+ ^! "Error"\n')
    executable.load_document(document)

    out1 = executable.evaluate_document() # good stuff .. Hey, corporate greed
    out2 = executable.evaluate_document("linux-x64") # Hey, Tux
    out3 = executable.evaluate_document(None, True) # Hey, corporate greed
    out4 = executable.evaluate_document("osx-x64", False, ("Error happened", "[WARNING] Yup")) # Error happened
    out5 = executable.evaluate_document("stuff", False, (None, "No match damn")) # No match damn
    out6 = executable.evaluate_document("stuff", True) # default warning message
    out7 = executable.evaluate_document("linux-x86", True) # Hey, Tux
    out8 = executable.get_runtime_id() # win-x64
    out9 = executable.version # v1.0.2
    
    while True:
        a = input("Test case: ")
        
        match int(a):
            case 1:
                print(out1, end='\n\n')
                
            case 2:
                print(out2, end='\n\n')
                
            case 3:
                print(out3, end='\n\n')
                
            case 4:
                print(out4, end='\n\n')
                
            case 5:
                print(out5, end='\n\n')
                
            case 6:
                print(out6, end='\n\n')

            case 7:
                print(out7, end='\n\n')
                
            case 8:
                print(out8, end='\n\n')

            case 9:
                print(out9, end='\n\n')

            case _:
                print("Error.", end='\n\n')
