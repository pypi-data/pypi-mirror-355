def read_from_file(file:str) -> list:
    """
        Function to read the file contents from the given file. 

        Args:
            file    (str): File name to read the content.  
            
        Returns:
            list    :   Returns content in a list (splited by lines).
                
    """
    try:
        with open (file,"r") as opened_file:
            contents = opened_file.readlines()
            return contents
        
    except FileNotFoundError as Fe:
        print(f"[ ! ] The file '{file}' doesn't exist")
        exit(1)

    except PermissionError as Pe:
        print(f"[ ! ] Permission denied for '{file}' ")
        exit(1)