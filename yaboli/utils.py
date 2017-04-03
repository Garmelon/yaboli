def mention(name):
	"""
	mention(name) -> name
	
	Removes all whitespace and some special characters from the name,
	such that the resulting name, if prepended with a "@", will mention the user.
	"""
	
	return "".join(c for c in name if not c in ".!?;&<'\"" and not c.isspace())

def reduce_name(name):
	"""
	reduce_name(name) -> name
	
	Reduces a name to a form which can be compared with other such forms.
	If two such forms are equal, they are both mentioned by the same @mentions,
	and should be considered identical when used to identify users.
	"""
	
	#TODO: implement
	pass
