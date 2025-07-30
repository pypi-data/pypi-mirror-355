def sample_function():
    """
    A sample function for the test package.
    
    This function is a placeholder to demonstrate the structure of a function
    within the test package. It currently does not perform any operations.
    
    Returns:
        str: A sample return message.
    """
    return "This is a sample function in the test package."

class SampleClass:
    """
    A sample class for the test package.
    
    This class serves as a placeholder to demonstrate the structure of a class
    within the test package. It includes a simple method that returns a message.
    """
    
    def __init__(self, name):
        """
        Initializes the SampleClass with a name.
        
        Args:
            name (str): The name to be associated with the instance.
        """
        self.name = name
    
    def greet(self):
        """
        A method to return a greeting message.
        
        Returns:
            str: A greeting message including the name.
        """
        return f"Hello, {self.name}! Welcome to the test package."
