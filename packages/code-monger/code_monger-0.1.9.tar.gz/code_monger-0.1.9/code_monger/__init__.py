

"""



This package handles creation of strings that are unique in the files they are stored in . 
Used in applications that reqiure generation and verification of codes


"""



from .code_generator import CodeGenerator , generate_code

__all__ = [
	"CodeGenerator" , 
	"generation",

	]