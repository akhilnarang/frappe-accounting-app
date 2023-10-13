import random
import string


def generate_random_string(k: int = 10) -> str:
	"""
	Function to generate a random string of length k

	:param k: Length of the random string, default 10
	:return: Random string of length k
	"""
	return "".join(random.choices(string.ascii_letters + string.digits, k=k))


def get_random_integer(minimum: int = 1, maximum: int = 100) -> int:
	"""
	Function to return a random integer between a given range

	:param minimum: Minimum value of the random integer, default 1
	:param maximum: Maximum value of the random integer, default 100
	:return: Random integer between minimum and maximum
	"""
	return random.randint(minimum, maximum)
