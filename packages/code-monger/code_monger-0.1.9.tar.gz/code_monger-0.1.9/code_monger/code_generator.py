# product id manage here 




import uuid,os
from string import ascii_uppercase, digits , printable , punctuation , whitespace ,ascii_lowercase
from random import choice 
from io import StringIO
import datetime as dt


valid_casing_values = ['all' , "upper" ,'lower']
UNWANTED_CHARACHTERS = '''"','''
def generate_code( length = 10 ,  numbers = False , letters = False , punctuation_chars = False , casing = "all"):
    '''Makes a code following the parameters provided

    Parameters
    ----------
    length:int
        length of the code to be generated
    numbers:bool
        set to [True] to Include integers during code generation
    letters:bool
        set to [True] to Include english alphabet letters
    punctuation_chars:bool
        set to [True] to include punctuation characters  
    casing:str
        Choice of casing for the code generated , it can only be one of these :
            > 'lower' - Lowercase only
            > 'upper' - Uppercase only
            > 'all'   - Mix uppercase and lowercase
        If an invalid value is provided, the value is reset to 'all'

    Returns
    -------
    str
        the generated code is returned as a string object

    '''

    contents = ""
    casing = casing.strip().lower()
    if not casing in valid_casing_values:
        casing = "all"
    if numbers:
        contents += digits
    if letters:
        if casing == "all":
            contents += ascii_uppercase + ascii_lowercase
        elif casing == "upper":
            contents += ascii_uppercase
        elif casing == "lower":
            contents += ascii_lowercase
    if punctuation_chars:
        contents += punctuation  
    cache = ""
    if contents == "":
        contents = ascii_uppercase + digits  
    contents = "".join([ char for char in contents if not char in UNWANTED_CHARACHTERS])
    while True:
        for i in range(0, length):
            cache += choice(contents)
        return cache



class CodeGenerator:
    def __init__(self , storage_file):
        self.storage_file = storage_file
        self.CheckStorage()

    def  NewCode(self,
            key_string ,
            length = 10 ,
            numbers = True ,
            letters = False ,
            punctuation_chars = False ,
            casing = "all"
             ) -> str:
        '''
        Generate a new code , store it in a file and return the code

         Parameters
        ----------
        key_string:str
            A string that will act as an identifier of the code ownership during validation
            An example is an email_address, or a username 
        length:int
            length of the code to be generated
        numbers:bool
            set to [True] to Include integers during code generation
        letters:bool
            set to [True] to Include english alphabet letters
        punctuation_chars:bool
            set to [True] to include punctuation characters  
        casing:str
            Choice of casing for the code generated , it can only be one of these :
                > 'lower' - Lowercase only
                > 'upper' - Uppercase only
                > 'all'   - Mix uppercase and lowercase
            If an invalid value is provided, the value is reset to 'all'

        Returns
        -------
        str
            the generated code is returned as a string object

        '''
        self.CheckStorage()
        data_file = self.storage_file
        with open(data_file, "r") as f :
            lines = f.readlines()
        lines = [s.strip() for s in lines]
        contents = digits + ascii_uppercase
        while True:
            cache = generate_code( 
                length = length ,
                numbers = numbers ,
                letters = letters ,
                punctuation_chars =punctuation_chars ,
                casing = casing)
            if not cache  in lines:
                lines.append(key_string +","+ cache)
                with open(data_file, 'w') as f:
                    for char in lines:
                        f.write(char + "\n")
                return cache

     
     
    def ValidateCode(self, code , key_string , delete_if_valid =  True  )-> None:
        """
        Check if a code exists in the storage file . 
        if delete_if_valid is True , the code is deleted from the file .

        Parameters
        ----------
        code:str
            The code that is to be vlaidated
        key_string:str
            A string that will act as an identifier of the code ownership during validation
            An example is an email_address, or a username 
        delete_if_valid:bool
            set to [True] to delete the code after positive validation , 
            setting to [False] will leave the code in the file .   
        """

        self.CheckStorage()
        file = self.storage_file
        if not os.path.isfile(file):
            with open(file, "w") as f:
                f.write("")
        with open(file, "r") as f:
            data = f.readlines()
        info = []
        lines = [s.strip() for s in data]
        for l in lines:
            vals = l.split(',')
            ks = vals[0]
            cd = vals[1]
            if key_string == ks and code == cd :
                if delete_if_valid:
                    lines.pop(lines.index(l))
                with open(file, "w") as f:
                    for l in lines:
                        f.write(l+"\n")
                return True
        return False

    def ClearCodes(self ,delete_file = False ):
        ''' 
        This methods removes all the codes from the storage file . 
        set delete to True to delete the file 

        Parameters
        ----------
        delete_file:bool
            Set to [True] to delete the storage file , [False] will just clear the file contents

        Returns
        -------
        None
        '''

        if delete_file:
            # delete the storage file
            try:
                os.remove(self.storage_file)
            except Exception as e:
                print("Could not delete {} because of {}".format(self.storage_file ,e))
                raise
            return
        # overwrite the data in the storagefile
        with open(self.storage_file , "w") as f:
            f.write("")

    def CheckStorage(self):
        '''
        Ensure that the storage file is present , if not, attempt to create it

        Returns
        -------
        None

        '''
        storage_file = self.storage_file
        if not os.path.isfile(storage_file):
            print("Storage file {} is non-existent , attempting to create ".format(storage_file), end = "")
            try:
                missing_folder , missing_file  = os.path.split(storage_file)
                if missing_folder:
                    if not os.path.isdir(missing_folder):
                        os.makedirs(missing_folder)
                with open( storage_file , "w") as f:
                    f.write("")
                print("DONE")
            except Exception as e:
                print("ERROR")
                print("Error creating the storage file because of {}  Error".format(e))
                raise


if __name__ == '__main__':
    print(NewSerialNo(10))