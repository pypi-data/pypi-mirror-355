"""
**AveyTense Exceptions**

@lifetime >= 0.3.27a1 \\
© 2024-Present Aveyzan // License: MIT

Exception classes for AveyTense. Used in any scope modules scattered around the project. \\
Globally accessible since 0.3.44.
"""
class MissingValueError(Exception):
    """
    @lifetime >= 0.3.19
    ```
    # 0.3.26b3 - 0.3.26c3 in module tense.tcs
    # to 0.3.26b3 in module tense.primary
    ```
    Missing value (empty parameter)
    """
    ...
class IncorrectValueError(Exception):
    """
    @lifetime >= 0.3.19
    ```
    # 0.3.26b3 - 0.3.26c3 in module tense.tcs
    # to 0.3.26b3 in module tense.primary
    ```
    Incorrect value of a parameter, having correct type
    """
    ...
class NotInitializedError(Exception):
    """
    @lifetime >= 0.3.25
    ```
    # 0.3.26b3 - 0.3.26c3 in module tense.tcs
    # to 0.3.26b3 in module tense.primary
    ```
    Class was not instantiated
    """
    ...
class InitializedError(Exception):
    """
    @lifetime >= 0.3.26b3
    
    Class was instantiated
    """
    ...
class NotReassignableError(Exception):
    """
    @lifetime >= 0.3.26b3
    
    Attempt to re-assign a value
    """
    ...
class NotComparableError(Exception):
    """
    @lifetime >= 0.3.26rc1
    
    Attempt to compare a value with another one
    """
    ...
class NotIterableError(Exception):
    """
    @lifetime >= 0.3.26rc1
    
    Attempt to iterate
    """
    ...
class NotCallableError(Exception):
    """
    @lifetime >= 0.3.45
    
    Attempt to call an object
    """
    ...
    
NotInvocableError = NotCallableError # >= 0.3.26rc1
    
class SubclassedError(Exception):
    """
    @lifetime >= 0.3.27rc1
    
    Class has been inherited by the other class
    """
    ...

if __name__ == "__main__":
    error = RuntimeError("Import-only module")
    raise error