# Solidipy

Solidipy is a python package that provides a variety of utilities for common tasks. It is 100% unit tested and verified.  [PyPi repo](https://pypi.org/project/solidipy/).

---

# Installation

```pip install solidipy```

---------------------------

---

# Logging Utility

## BaseLogger

BaseLogger is a wrapper around the standard python logging mod that provides a
simple interface for different levels of logging synchronously or asynchronously.
The BaseLogger object is intended to be instantiated as a singleton. Its default 
behavior is to log to the console synchronously. You can pass your own logger
to the BaseLogger on init or use the one provided as the default value. You
can also optionally pass an absolute filepath to a dir as a second arg at init
to log to a file. If you do not pass a filepath, it will not log to a file. The
supplied filepath must end in a directory. Log files will be saved as
"{name_of_logger}__{year}-{month}-{day}.log". This means that it will
automatically move over to a new logging file every day. If you want to change
to the path of a logger after init, supply a path to the "set_log_file" method.
To disable logging to a file, supply None to the "set_log_file" method.

### ex using default value:

```python
from solidipy.logging_utility import BaseLogger


# Import the `singleton_logger` to other modules to use it across the project.
singleton_logger: BaseLogger = BaseLogger()

singleton_logger.log_info('This is an info message')
singleton_logger.log_json(json_dict={"JSON": "PAYLOAD"}, tag='JSON payload ==>', indent=0)
singleton_logger.log_debug('This is a debug message')
singleton_logger.log_warning('This is a warning message')
singleton_logger.log_error('This is an error message')
singleton_logger.log_exception('This is a critical message')

# The asychronous versions of the logging methods take the same
# arguments as their synchronous counterparts.
await singleton_logger.log_aysnc_info('This is an info message')
await singleton_logger.log_json(json_dict={"JSON": "PAYLOAD"}, tag='JSON payload ==>')
await singleton_logger.log_aysnc_debug('This is a debug message')
await singleton_logger.log_aysnc_warning('This is a warning message')
await singleton_logger.log_aysnc_error('This is an error message')
await singleton_logger.log_aysnc_exception('This is a critical message')
```

### ex using custom logger value:

```python
from solidipy.logging_utility import BaseLogger


standard_python_logger: Logger = logging.getLogger("super_sick_nasty_logger_name")
custom_singelton_logger: BaseLogger = BaseLogger(standard_python_logger)

custom_singelton_logger.log_info('This is an info message')
custom_singelton_logger.log_debug('This is a debug message')
custom_singelton_logger.log_warning('This is a warning message')
custom_singelton_logger.log_error('This is an error message')
custom_singelton_logger.log_exception('This is a critical message')

# The asychronous versions of the logging methods take the same
# arguments as their synchronous counterparts.
await custom_singelton_logger.log_aysnc_info('This is an info message')
await custom_singelton_logger.log_aysnc_debug('This is a debug message')
await custom_singelton_logger.log_aysnc_warning('This is a warning message')
await custom_singelton_logger.log_aysnc_error('This is an error message')
await custom_singelton_logger.log_aysnc_exception('This is a critical message')
```

### ex that logs to a file:

```python
from solidipy.logging_and_exceptions.logger import BaseLogger

custom_singelton_logger: BaseLogger = BaseLogger(
    logging.getLogger("super_sick_nasty_logger_name"),
    "user/some_user/some_project/logger_dir/"
)

custom_singelton_logger.log_info('This is an info message') # Will print to console & log to a file in the specified dir.

custom_singelton_logger.set_log_file(None) # Removes the file path and stops logging_utility to a file, but keeps logging_utility to the console.
custom_singelton_logger.log_info('This is an info message') # Will only print to console.

custom_singleton_logger.set_log_file("user/some_user/some_other_project/logging_utility/") # Resetting the log file path will start logging_utility to a file again.
custom_singelton_logger.log_info('This is an info message')# Will log to a file again.
```

---------------------------

---

# Exceptions

## ExceptionHandler

ExceptionHandler is an object that logs and maps exceptions their corresponding error message. If no logger is
supplied at init, it will only map the exception to a dictionary and return it. If a logger is supplied, it will
log the exception AND return the dictionary. The exception handler is designed to only be used synchronously and
to use the logging methods that exist within the BaseLogger class.

### Basic example:

```python
from solidipy.exceptions import ExceptionHandler, MASTER_EXCEPTION_TUPLE


def some_function() -> bool:
	"""
	A Function that probably does something.
	:return: True if something was done, False if an exception was raised.
	"""

	try:
		# SOMETHING RISKY
		return True
	except MASTER_EXCEPTION_TUPLE as exception:
		exc_handler: ExceptionHandler = ExceptionHandler()
		exception_log: dict = exc_handler.get_exception_log(exception)
		return False
```

### Example with logger

```python
from solidipy.exceptions import ExceptionHandler, MASTER_EXCEPTION_TUPLE

from my_cool_project.logger import singleton_logger


def some_function() -> bool:
	"""
	A Function that probably does something.
	:return: True if something was done, False if an exception was raised.
	"""
   
	try:
		# SOMETHING RISKY
		return True
	except (CustomValidationError, MASTER_EXCEPTION_TUPLE) as exception:
		exc_handler: ExceptionHandler = ExceptionHandler(singleton_logger)
		exception_log: dict = exc_handler.get_exception_log(exception)
		return False
```

### ex with singletons used (how it is intended to be used):

Setup singletons in their own module to be imported around the project:
```python
# /utils/logging_and_exceptions.py
import logging

from solidipy.exceptions import ExceptionHandler
from solidipy.logging_utility import BaseLogger


custom_singelton_logger: BaseLogger = BaseLogger(
    logging.getLogger("logger_name")
)
"""
Singleton logger that is intended to be used across the project.
"""

exception_handler: ExceptionHandler = ExceptionHandler(custom_singelton_logger)
"""
Singleton exception handler that is intended to be used across the project.
"""

```
Use the singletons in your modules:
```python
# /my_cool_project/module.py

from utils.logging_and_exceptions import (
    custom_singelton_logger, exception_handler
)
from solidipy.exceptions import MASTER_EXCEPTION_TUPLE


def some_function() -> bool:
	"""
	A Function that probably does something.
	:return: True if something was done, False if an exception was raised.
	"""
   
	try:
		# SOMETHING RISKY
		return True
	except MASTER_EXCEPTION_TUPLE as exception:
        # It logs it automatically because it was handed a logger at init.
        # It will also return the dictionary so you can use it in your code,
        # but capturing the dict in a variable isn't required.
		exception_log: dict = exception_handler.get_exception_log(exception)
		return False
```
---------------------------

---------------------------

---------------------------

---

# Utilities

'solidipy' provides a variety of utilities for common tasks.

---


## Dict Utilities

### normalize_keys

Utility function to normalize all string keys in a dictionary to lowercase.

Example code:

```python
from typing import List
from solidipy.utilities.dict_utilities import normalize_keys

# Scenario 1 - All keys are strings.
test_dict: dict = { 'A': 1, 'B': 2, 'C': 3 }
normalize_keys(test_dict_1) # {'a': 1, 'b': 2, 'c': 3}

# Scenario 2 - Some keys are strings, some are not.
test_dict_2: dict = { 'A': 1, 'B': 2, 3: 'C' }
normalize_keys(test_dict_1) # {'a': 1, 'b': 2, 3: 'C'}

# Scenario 3 - All keys are not strings.
test_dict_3: dict = { 1: 'A', 2: 'B', 3: 'C' }
normalize_keys(test_dict_1) # {1: 'A', 2: 'B', 3: 'C'}
```

---

## list Utilities

### is_every_list_item_unique

Utility function to determine if a list contains only unique items.

Example code:

```python
from typing import List
from solidipy.utilities.list_utilities import is_every_list_item_unique


unique_list: List[str] = ['a', 'b', 'c']
is_unique: bool = is_every_list_item_unique(unique_list) # True

dupe_list: List[str] = ['a', 'b', 'c', 'a']
is_unique: bool = is_every_list_item_unique(dupe_list) # False
```

### list_contents_are_identical_without_order

Utility function for determining if two lists contain the same items, regardless of order.

Example code:

```python
from solidipy.utilities.list_utilities import list_contents_are_identical_without_order


list_a: List[str] = ['a', 'b', 'c']
list_b: List[str] = ['c', 'b', 'a']
list_c: List[str] = ['a', 'f', 'c']

are_identical: bool = list_contents_are_identical_without_order(list_a, list_b) # True
are_identical: bool = list_contents_are_identical_without_order(list_a, list_c) # False
```

### serialize_list

Utility function that serializes a list of strings into a single string.

Example code:

```python
from solidipy.utilities.list_utilities import serialize_list


list_a: List[str] = ['a', 'b', 'c']
serialized_list: str = serialize_list(list_a) # `a,b,c`
```

---------------------------

### deserialize_list

Utility function that deserializes a list of strings from a single string.

Example code:

```python
from solidipy.utilities.list_utilities import deserialize_list


serialized_str: str = 'a,b,c'
deserialized_list: List[str] = deserialize_list(serialized_list)# [`a`, `b`, `c`]
```

---------------------------

---

## Number Utilities

### get_rounded_quotient

Utility function for getting a quotient that is rounded up or down. It will round up by default.

Example code:

```python
from solidipy.utilities.number_utilities import get_rounded_quotient

quotient: int = get_rounded_quotient(5, 2) # 3
quotient: int = get_rounded_quotient(5, 2, False) # 2
```

---------------------------

---------------------------

---

## String Utilities

### get_os_variable

Utility function for returning an existing OS environment variable by key.

Example code:

```python
from solidipy.utilities.string_utilities import get_os_variable


os_var: str = get_os_variable('MY_OS_VAR') # "my_os_var_value"

non_existant_os_var: str = get_os_variable('MY_OS_VAR') # ""
```

### is_regex_pattern_match

Utility function for conducting a regex match against a string value.

Example code:

```python
from solidipy.utilities.string_utilities import is_regex_pattern_match


regex_pattern: str = '^[a-z]+$'

is_match: bool = is_regex_pattern_match(regex_pattern, 'my_string') # True
is_match: bool = is_regex_pattern_match(regex_pattern, 'my_string123') # False
```

### reformat_string

Utility function for reformatting a string.

Example code:

```python
from solidipy.utilities.string_utilities import reformat_string

ex_str: str = "This_is_a_string"
reformatted_str: str = reformat_string(ex_str, '_', ' ') # "This is a string"
```

### get_random_uuid

Utility function for returning a UUID of a specified length.

Example code:

```python
from solidipy.utilities.string_utilities import get_random_uuid


uuid: str = get_random_uuid(10) # "a1b2c3d4e5"
uuid_2: str = get_random_uuid(10) # "f6g7h8i9j0"
uuid_3 str = get_random_uuid(14) # "k1l2m3n4o55F89"
```

### generate_hex_bytes_as_string

Utility function for generating bytes in hexadecimal format and returning them as a string that is the specified length.

Example code:

```python
from solidipy.utilities.string_utilities import generate_hex_bytes_as_string


str_bytes: str = generate_hex_bytes_as_string(10) # "a1b2c3d4e5"
str_bytes_2: str = generate_hex_bytes_as_string(10) # "f6g7h8i9j0"
str_bytes_3 str = generate_hex_bytes_as_string(14) # "k1l2m3n4o55F89"
```

### base64_decode_string

Utility function for decoding a base64 encoded string.

Example code:

```python
from solidipy.utilities.string_utilities import base64_decode_string

b_64_encoded_str: str = "cmF2aW9saSByYXZpb2xpIGdpdmUgbWUgdGhlIGZvcm11b2xpCg=="
decoded_str: str = base64_decode_string(b_64_encoded_str) # "ravioli ravioli give me the formuoli"
```

### get_base64_string_from_dict

Utility function for returning a dictionary as a base64 encoded string.

Example code:

```python
from solidipy.utilities.string_utilities import get_base64_string_from_dict

important_information: dict = {
	'name': 'John Doe',
	'age': 42,
	'favorite_food': 'ravioli'
}

b_64_encoded_str: str = get_base64_string_from_dict(important_information) # "ewogICAgJ25hbWUnOiAnSm9obiBEb2UnLAogICAgJ2FnZSc6IDQyLAogICAgJ2Zhdm9yaXRlX2Zvb2QnOiAncmF2aW9saScKfQo="
```

### get_hex_encoded_str

Utility function for hexadecimal encoding a string.

Example code:

```python
from solidipy.utilities.string_utilities import get_hex_encoded_str

str_to_encode: str = "ravioli ravioli give me the formuoli"
hex_encoded_str: str = get_hex_encoded_str(str_to_encode) # "726176696f6c6920726176696f6c692067697665206d652074686520666f726d756f6c69"
```

### generate_alphanumeric_str

Utility function for generating a random alphanumeric string of a specified size.

Example code:

```python
from solidipy.utilities.string_utilities import generate_alphanumeric_str


alphanumeric_str: str = generate_alphanumeric_str(10) # "a1b2c3d4e5"
alphanumeric_str_2: str = generate_alphanumeric_str(10) # "f6g7h8i9j0"
alphanumeric_str_3 str = generate_alphanumeric_str(14) # "k1l2m3n4o55F89"
```

---------------------------

---------------------------

---

## Time Utilities

### get_time_in_future

Utility function for returning a date in the future down to the matching second.

Example code:

```python
from solidipy.utilities.time_utilities import get_time_in_future


seconds_in_future: datetime = get_time_in_future(seconds=10) # Datetime object 10 seconds in the future.
weeks_in_future: datetime = get_time_in_future(seconds=10, minutes=10, hours=10, days=10, weeks=10) # Datetime object 80.42 days in the future.
```

### is_after_today

Utility function for telling if a given date and time is later than today.

Example code:

```python
from solidipy.utilities.time_utilities import is_after_today


tomorrow: datetime = datetime.now() + timedelta(days=1)
is_after: bool = is_after_today(tomorrow) # True

yesterday: datetime = datetime.now() - timedelta(days=1)
is_after: bool = is_after_today(yesterday) # False
```

### get_datetime_in_epoch

Utility function for converting a datetime object into epoch seconds.

Example code:

```python
from solidipy.utilities.time_utilities import get_datetime_in_epoch


current_date_and_time: datetime = datetime.now()
time_in_epoch: int = get_datetime_in_epoch(current_date_and_time) # 1616425200
```

### get_iso_datestr

Utility function for converting a datetime object into a standardized ISO formatted string. If a timezone unaware
datetime is passed, as the parameter or a non-UTC datetime is passed, it will be converted to UTC before output.

Example Code:

```python
from solidipy.utilities.time_utilities import get_iso_datestr


some_date: datetime = datetime('2022-01-25 22:56:00.911847', tzinfo=timezone.utc)
iso_date_string: str = get_iso_datestr(some_date) # "2022-01-25T22:56:00.911847+00:00"
```

### get_seconds_remaining_until_expiration

Utility function for determining how many seconds are left until an expiration date and time.
If no second argument is supplied, it is assumed that the current time is the comparison time.

Example figuring out how many seconds are left until the year 2040:

```python
from solidipy.utilities.time_utilities import get_seconds_remaining_until_expiration


expiration_date: datetime = datetime('2040-01-01 00:00:00.00000', tzinfo=timezone.utc)
get_seconds_remaining_until_expiration(expiration_time) # 507704330
```

Example using expiration date in the past:

```python
from solidipy.utilities.time_utilities import get_seconds_remaining_until_expiration

expiration_date: datetime = datetime('1997-01-01 00:00:00.00000')
get_seconds_remaining_until_expiration(expiration_time) # 0
```

Example comparing two dates:

```python
from solidipy.utilities.time_utilities import get_seconds_remaining_until_expiration

expiration_date: datetime = datetime('2040-01-01 00:00:00.00000', tzinfo=timezone.utc)
some_date: datetime = datetime('2022-01-25 22:56:00.911847', tzinfo=timezone.utc)
get_seconds_remaining_until_expiration(expiration_time, some_date) # 507704330
```

---------------------------

---------------------------

---

# Validation
If the Pydantic validation library is installed, 'solidipy' provides
a few ways to make the library more flexible and convenient.

## CustomValidationError
Custom error class used to handle Pydantic validation errors that are
outside the scope of the library's functionality.  This class can override
a normal error that Pydantic will throw to mold the information included to
be that your choosing.  There are certain scenarios where Pydantic's normal
error handling is not sufficient.  This class is designed to be raised and
caught as an exception.

Example code:

```python
from pydantic import (
    BaseModel, Field, field_validator,
)

from solidipy.utilities.validation import CustomValidationError


class Person(BaseModel):

    age: int = Field()

    address: Dict[str, Any] = Field(max_length=3)

    @classmethod
    def __validate_address_field(
        cls, field: str, value: Union[str, int], field_type: Type
    ):
        """
         Helper method that validates values within the 'address' field.
         Validates a given value's existence and type.

        :param field: The field name to validate.
        :param value: The value to validate.  Either a string or integer.
        :param field_type: The type to validate against.
        """

        if value is None:
            raise CustomValidationError(
                error_type="missing",
                msg="field is required",
                loc=("address", field),
                user_input=value
                error_code=400
            )

        if not isinstance(value, field_type):
            raise CustomValidationError(
                error_type="type mismatch",
                msg=f"Input should be a valid {field_type.__name__}",
                loc=("address", field),
                user_input=value
                error_code=400
            )

        return value

    @field_validator("address")
    def validate_address(cls, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Custom validation interface method for the address dictionary field.

        :param address: The address dictionary to validate.
        :return: The validated address dictionary.
        """

        if address is None:
            raise CustomValidationError(
                error_type="missing",
                msg=f"adress is required",
                error_code=400
            )

        address["street"] = cls.__validate_address_field(
            "street", address.get("street"), str
        )
        address["city"] = cls.__validate_address_field(
            "city", address.get("city"), str
        )
        address["zip_code"] = cls.__validate_address_field(
            "zip_code", address.get("zip_code"), int
        )
        return address
```

## ValidationErrorHandler
Class designed to make parsing and returning Pydantic
validation errors in an efficient and consistent manner.
Requires Pydantic & Flask

Example code:

```python
from pydantic import ValidationError, PydanticCustomError

from CustomValidationError.example import Person
from solidipy.validation import ValidationErrorHandler, CustomValidationError

person_data: dict = {
    "age": "Bad value",
    "address": {
        "street": "1234 Main St.",
        "city": "New York",
        "zip_code": 12345
    }
}

    def validate_person_data(person_data: dict) -> Union[Person, dict]:
        try:
            new_person: Person = Person(**person_data)
        
        except (ValidationError, PydanticCustomError, CustomValidationError) as validation_error:
            validation_error_handler: ValidationErrorHandler = ValidationErrorHandler(
                validation_error
            )
            error_dict: dict = validation_error_handler.error
            code: int = validation_error.get("response_code", 400)
        return error_dict, code

```

---

## validate_model
Function that validates a dictionary against a Pydantic model.  Returns the
validated model if successful, or a dictionary of errors if not. The result of
a successful validation will always be a populated instance of the model.
If a validation error occurs, the error will be returned as a dictionary.
Takes in a dictionary and an uninstantiated Pydantic model as arguments.
Requires Pydantic

example use:
```python
from solidipy.validation import validate_model

from models.validation_models.example import Person


person_data: dict = {"age": 70, "name": "John Doe", }

validation_result: Union[Person, dict] = validate_model(person_data, Person)

```

## validate_request_headers
A decorator to be used as a decorator on functions decorated as a Flask
blueprint to validate incoming request headers.  It takes in an uninstantiated
instance of a Pydantic model as an argument. The decorator has to be applied
under the `@blueprints.route` decorator so that the incoming request is in context.
If the validation is successful, the validated headers can be passed to the
decorated function if a function argument called "request_headers" is supplied.
The object will be the same type as the Pydantic model that was supplied to the
decorator. If a validation error occurs, the error will be returned as a
dictionary alongside a status code. "400" is the default, but a custom status
code can be assigned if a `CustomValidationError` is raised.
Requires Pydantic & Flask

Example that only validates the headers, but does not pass the validated headers
to the function:
```python
from solidipy.validation import validate_request_headers
from flask import blueprints

from example.models import HeadersModel


@blueprintss.route("/some_route", methods=["GET"])
@validate_request_headers(HeadersModel)
def endpoint_function():
    """ Function that does something. """

    pass

```

Example that validates the headers and pass the validated headers to the function:
```python
from solidipy.validation import validate_request_headers
from flask import blueprints

from example.models import HeadersModel


@blueprintss.route("/some_route", methods=["GET"])
@validate_request_headers(HeadersModel)
def endpoint_function(request_headers: HeadersModel):
    """ Function that does something. """

    content_type: str = request_headers.content_type
    # content_type == "application/json"
    accept_language: str = request_headers.accept_language
    # accept_language == "en-US"

```

The `validate_request_headers` & `validate_request_body` decorators can be used
in conjunction with each other.
```python
from solidipy.validation import validate_request_body, validate_request_headers
from flask import blueprints

from example.models import RequestBodyModel, RequestHeadersModel


@blueprintss.route("/some_route", methods=["Post"])
@validate_request_headers(RequestHeadersModel)
@validate_request_body(RequestBodyModel)
def endpoint_function(
    request_headers: HeadersModel, request_body: RequestBodyModel
):
    """ Function that does something. """

    content_type: str = request_headers.content_type
    # content_type == "application/json"
    accept_language: str = request_headers.accept_language
    # accept_language == "en-US"

    action: str = request_body.action
    # action == "resume"
    id: int = request_body.id
    # id == 4242

```

## validate_request_body
A decorator to be used as a decorator on functions decorated as a Flask
blueprint to validate incoming the bodies of incoming requests. It takes in an
uninstantiated instance of a Pydantic model as an argument. The decorator has
to be applied under the `@blueprints.route` decorator so that the incoming request is
in context. If the validation is successful, the validated request body can be
passed to the decorated function if a function argument called "request_body" is
supplied. The object will be the same type as the Pydantic model that was
supplied to the decorator.  If a validation error occurs, the error will be
returned as a dictionary alongside a status code. "400" is the default, but a
custom status code can be assigned if a `CustomValidationError` is raised.
Requires Pydantic & Flask

Example that only validates the body, but does not pass the validated object
to the function:
```python
from solidipy.validation import validate_request_headers
from flask import blueprints

from example.models import RequestBodyModel


@blueprintss.route("/some_route", methods=["POST"])
@validate_request_headers(RequestBodyModel)
def endpoint_function():
    """ Function that does something. """

    pass

```

Example that validates the body and passes the validated object to the function:
```python
from solidipy.validation import validate_request_body
from flask import blueprints

from example.models import RequestBodyModel


@blueprintss.route("/some_route", methods=["Post"])
@validate_request_headers(RequestBodyModel)
def endpoint_function(request_body: RequestBodyModel):
    """ Function that does something. """

    action: str = request_body.action
    # action == "resume"
    id: int = request_body.id
    # id == 4242

```

The `validate_request_headers` & `validate_request_body` decorators can be used
in conjunction with each other.
```python
from solidipy.validation import validate_request_body, validate_request_headers
from flask import blueprints

from example.models import RequestBodyModel, RequestHeadersModel


@blueprintss.route("/some_route", methods=["Post"])
@validate_request_headers(RequestHeadersModel)
@validate_request_body(RequestBodyModel)
def endpoint_function(
    request_headers: HeadersModel, request_body: RequestBodyModel
):
    """ Function that does something. """

    content_type: str = request_headers.content_type
    # content_type == "application/json"
    accept_language: str = request_headers.accept_language
    # accept_language == "en-US"

    action: str = request_body.action
    # action == "resume"
    id: int = request_body.id
    # id == 4242

```

# Future Plans

	• Decorator that enforces strong-typing of function arguments.
	• Utilities for reading and writing to files.



---