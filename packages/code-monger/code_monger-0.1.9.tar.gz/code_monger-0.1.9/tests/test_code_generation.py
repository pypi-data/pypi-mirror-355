
import string , unittest

from unittest import TestCase

from code_monger import CodeGenerator , generate_code

default_code_length = generate_code.__defaults__[0]

class TestCodeGeneration(TestCase):
	def test_SimpleCodeGeneration(self):
		'''
		check if a code is generated or not 
		'''
		code = generate_code(  )
		self.assertTrue(type(code) == str and len(code) > 0 )



	def test_CustomCodeGeneration(self):
		'''
		Checking if different parameters during custom code generation are considered 
		'''
		# code length
		none_special_chartachters = string.ascii_uppercase + string.ascii_lowercase + string.digits
		code = generate_code(length = 20  )
		self.assertTrue(len(code) == 20 )
		# check letter casing
		code  = generate_code(casing = "upper" , numbers = False , letters = True )
		self.assertTrue(code.isupper())
		code  = generate_code(casing = "lower" ,letters = True , numbers = False)
		self.assertTrue(code.islower())
		# check numbers only
		code = generate_code(numbers = True , letters = False)
		self.assertTrue(code.isnumeric())
		# check code generation with  special charachters 
		code = generate_code(punctuation_chars = True  , letters = False , numbers = False)
		self.assertTrue(all(  [  (char not in none_special_chartachters) for char in code   ] ))
		# check if code generation happens when no parameters are specified
		code = generate_code()
		self.assertTrue(len(code) == default_code_length)
	def test_CodeClearance(self):
		test_file = "codes_test_file.txt"
		cg = CodeGenerator(test_file)

 

	def test_NewCode(self):
		'''
		Testing the generation of a new code

		'''
		test_file = "./test_data/codes.txt"
		test_key_string = "myemail@gmail.com"
		cg = CodeGenerator(test_file)
		code = cg.NewCode(test_key_string   )
		self.assertTrue(len(code) == default_code_length)
		file_data = ''
		with open (test_file , "r") as f:
			file_data = f.read()
		self.assertTrue(code in file_data)
		validation_result = cg.ValidateCode(code , test_key_string)
		self.assertTrue(validation_result == True)
		with open (test_file , "r") as f:
			file_data = f.read()
		# chec if the code was deleted after validation
		self.assertTrue(code not in file_data)

		# test when delete_if_valid is set to False
		code = cg.NewCode(test_key_string  )
		validation_result = cg.ValidateCode(code , test_key_string , delete_if_valid = False)
		self.assertTrue(validation_result == True)
		with open (test_file , "r") as f:
			file_data = f.read()
		self.assertTrue(code in file_data)

if __name__ == '__main__':
	unittest.main()