# utilities/exceptions/exception_values.py

"""
Module of Error constants used in the exception handler.
Exceptions are listed in order of inheritance.
"""

from binascii import Error as BinasciiError, Incomplete as BinasciiIncompleteError
from importlib.util import find_spec
from json import JSONDecodeError

# ------------------ Generic' error message constants -------------------
GENERIC_ERROR_KEY: str = "Error"
GENERIC_MESSAGE_KEY: str = "Message"
GENERIC_DESCRIPTION_KEY: str = "Description"
GENERIC_CODE_KEY: str = "Code"
GENERIC_ERROR_NAME_VALUE: str = "Generic error"
GENERIC_ERROR_DESCRIPTION_VALUE: str = "An error outside of the scope of the error handler has occurred."

# -----------------------------------------------------------------------
# ------------------------ Begin error messages -------------------------
# -----------------------------------------------------------------------


# ------------- 'Unicode' error message constants ------------------------
UNICODE_TRANSL_ERROR_DESCRIPTION: str = "A unicode error occurred during translation."
UNICODE_ENCODE_ERROR_DESCRIPTION: str = "An error occurred related to unicode encoding."
UNICODE_DECODE_ERROR_DESCRIPTION: str = "An error occurred related to unicode decoding."
UNICODE_ERROR_DESCRIPTION: str = "An error occurred related to unicode encoding or decoding."
BINASCII_ERROR_DESCRIPTION: str = "An error occurred related to binary encoding or decoding."
JSON_DECODE_ERROR_DESCRIPTION: str = "Data could not be decoded as valid JSON."

# ----------------- 'Standard' error message constants -------------------
VALUE_ERROR_DESCRIPTION: str = "An operation or function received an argument that has the right type but an inappropriate value. The situation is not an IndexError."
TYPE_ERROR_DESCRIPTION: str = "An error occurred due to type mismatch."
SYSTEM_ERROR_DESCRIPTION: str = "The interpreter found a non-critical internal error. This should be reported to the author or maintainer of your Python interpreter."
TAB_ERROR_DESCRIPTION: str = "Incorrect use of Tabs and Spaces."
INDENTATION_ERROR_DESCRIPTION: str = "Incorrect indentation detected."
SYNTAX_ERROR_DESCRIPTION: str = "Syntax error encountered."
STOP_ITERATION_ERROR_DESCRIPTION: str = "The iterator has no more items to return."
STOP_ASYNC_ITERATION_DESCRIPTION: str = "The asynchronous iterator has no more items to return."
RECURSION_ERROR_DESCRIPTION: str = "Maximum recursion depth has been exceeded."
NOT_IMPLEMENTED_ERROR_DESCRIPTION: str = "This method or function should be implemented in the derived class."
RUN_TIME_ERROR_DESCRIPTION: str = "An error has been detected at runtime that does not fall in any of the other categories."
REFERENCE_ERROR_DESCRIPTION: str = "Attempt to access a deleted reference."

# ------------------- 'os' error message constants -----------------------
TIMEOUT_ERROR_DESCRIPTION: str = "A system function timed out at the system level."
PROCESS_LOOKUP_ERROR_DESCRIPTION: str = "Failed to find the given process."
PERMISSION_ERROR_DESCRIPTION: str = "An operation was not permitted."
NOT_A_DIRECTORY_ERROR_DESCRIPTION: str = "Expected a directory but got something else."
IS_A_DIRECTORY_ERROR_DESCRIPTION: str = "Expected something other than a directory but got a directory."
INTERRUPTED_ERROR_DESCRIPTION: str = "A system call has been interrupted by an incoming signal."
FILE_NOT_FOUND_ERROR_DESCRIPTION: str = "The specified file was not found."
FILE_EXISTS_ERROR_DESCRIPTION: str = "The file already exists."
CONNECTION_RESET_ERROR_DESCRIPTION: str = "Connection has been reset by the peer."
CONNECTION_REFUSED_ERROR_DESCRIPTION: str = "Connection has been refused by the peer."
CONNECTION_ABORTED_ERROR_DESCRIPTION: str = "Connection has been aborted by the peer."
BROKEN_PIPE_ERROR_DESCRIPTION: str = "Tried to write on a pipe while the other end was closed or tried to write on a socket that was shutdown for writing."
CONNECTION_ERROR_DESCRIPTION: str = "An unknown connection-related issue occurred."
CHILD_PROCESS_ERROR_DESCRIPTION: str = "An operation on a child process has failed."
BLOCKING_IO_ERROR_DESCRIPTION: str = "An operation would have blocked on an object that has non-blocking operation enabled."

# -------------- 'Standard' error message constants (Cont.) --------------
OS_ERROR_DESCRIPTION: str = "A system function has returned a system-related error, this could include I/O failures such as “file not found” or “disk full” (not for illegal argument types or other incidental errors)."
UNBOUND_LOCAL_ERROR_DESCRIPTION: str = "Referenced a local variable before it was defined."
NAME_ERROR_DESCRIPTION: str = "A local or global name was not found. This applies only to unqualified names."
MEMORY_ERROR_DESCRIPTION: str = "An operation has run out of memory but the situation may still be rescued by deleting some objects."
KEY_ERROR_DESCRIPTION: str = "Mapping (dictionary) key not found in the set of existing keys."
INDEX_ERROR_DESCRIPTION: str = "Sequence subscript is out of range."
LOOKUP_ERROR_DESCRIPTION: str = "A key or index used on a mapping or sequence is invalid: IndexError or KeyError."
MODULE_NOT_FOUND_ERROR_DESCRIPTION: str = "The specified module could not be found."
IMPORT_ERROR_DESCRIPTION: str = "Failed to import a module or its part."
EOF_ERROR_DESCRIPTION: str = "End of file reached without reading any data."
BUFFER_ERROR_DESCRIPTION: str = "A buffer-related operation cannot be performed."
ATTRIBUTE_ERROR_DESCRIPTION: str = "An attribute reference or assignment has failed."
ASSERTION_ERROR_DESCRIPTION: str = "Assertion failed."
ZERO_DIVISION_ERROR_DESCRIPTION: str = "The second argument of a division or modulo operation is zero."
OVERFLOW_ERROR_DESCRIPTION: str = "Result of an arithmetic operation is too large to be represented."
FLOATING_POINT_ERROR_DESCRIPTION: str = "Floating point operation has failed."
ARITHMETIC_ERROR_DESCRIPTION: str = "An arithmetic error has occurred. OverflowError, ZeroDivisionError, or FloatingPointError."
BINASCII_INCOMPLETE_ERROR_DESCRIPTION: str = "Incomplete input data."
BASE_EXCEPTION_ERROR_DESCRIPTION: str = "A system-exiting exception has occurred."
EXCEPTION_ERROR_DESCRIPTION: str = "A non-system-exiting exception has occurred."
GENERATOR_EXIT_ERROR_DESCRIPTION: str = "Operation was performed on an active generator that was already closed."

# ------------------------------------------------------------------------
# -------------------------- Begin error codes ---------------------------
# ------------------------------------------------------------------------

# -------------------- 'Generic' error code constants --------------------
GENERIC_ERROR_CODE: str = "GENERIC ERROR CODE"


# --------------------'os' error code constants --------------------------
TIMEOUT_ERROR_CODE: str = "errno ETIMEDOUT"
INTERRUPTED_ERROR_CODE: str = "errno EINTR"
CONNECTION_RESET_ERROR_CODE: str = "errno ECONNRESET"
CONNECTION_REFUSED_ERROR_CODE: str = "errno ECONNRESET"
CONNECTION_ABORTED_ERROR_CODE: str = "errno ECONNABORTED"
BROKEN_PIPE_ERROR_CODE: str = "errno EPIPE, errno ESHUTDOWN"
CHILD_PROCESS_ERROR_CODE: str = "errno ECHILD"
BLOCKING_IO_CODE: str = "errno EAGAIN, errno EALREADY, errno EWOULDBLOCK, errno EINPROGRESS"
PERMISSION_ERROR_CODE: str = "errno EACCES, EPERM"

# -----------------------------------------------------------------------
# ------------------- Begin Exception Values -----------------------
# ------------------------------------------------------------------------

# -----------------------------------------------------------------------
# ------------------- Begin Exception dictionaries -----------------------
# ------------------------------------------------------------------------

# --------------------- 'Generic' error dictionaries ---------------------
GENERIC_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: GENERIC_ERROR_NAME_VALUE,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: GENERIC_ERROR_DESCRIPTION_VALUE,
}

# --------------------- 'unicode' error dictionaries ---------------------
UNICODE_TRANSL_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: UnicodeTranslateError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: UNICODE_TRANSL_ERROR_DESCRIPTION,
}
UNICODE_ENCODE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: UnicodeEncodeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: UNICODE_ENCODE_ERROR_DESCRIPTION,
}
UNICODE_DECODE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: UnicodeDecodeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: UNICODE_DECODE_ERROR_DESCRIPTION,
}
UNICODE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: UnicodeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: UNICODE_ERROR_DESCRIPTION,
}
BINASCII_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: BinasciiError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BINASCII_ERROR_DESCRIPTION,
}
JSON_DECODE_DICT: dict = {
	GENERIC_ERROR_KEY: JSONDecodeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: JSON_DECODE_ERROR_DESCRIPTION,
}

# -------------------- 'Standard' error dictionaries ---------------------
VALUE_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ValueError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: VALUE_ERROR_DESCRIPTION,
}
TYPE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: TypeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: TYPE_ERROR_DESCRIPTION,
}
SYSTEM_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: SystemError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: SYSTEM_ERROR_DESCRIPTION,
}
TAB_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: TabError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: TAB_ERROR_DESCRIPTION,
}
INDENTATION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: IndentationError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: INDENTATION_ERROR_DESCRIPTION,
}
SYNTAX_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: SyntaxError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: SYNTAX_ERROR_DESCRIPTION,
}
STOP_ITERATION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: StopIteration.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: STOP_ITERATION_ERROR_DESCRIPTION,
}
STOP_ASYNC_ITERATION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: StopAsyncIteration.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: STOP_ASYNC_ITERATION_DESCRIPTION,
}
RECURSION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: RecursionError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: RECURSION_ERROR_DESCRIPTION,
}
NOT_IMPLEMENTED_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: NotImplementedError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: NOT_IMPLEMENTED_ERROR_DESCRIPTION,
}
RUN_TIME_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: RuntimeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: RUN_TIME_ERROR_DESCRIPTION,
}
REFERENCE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ReferenceError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: REFERENCE_ERROR_DESCRIPTION,
}
TIMEOUT_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: TimeoutError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: TIMEOUT_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: TIMEOUT_ERROR_CODE,
}
PROCESS_LOOKUP_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ProcessLookupError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: PROCESS_LOOKUP_ERROR_DESCRIPTION,
}
PERMISSION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: PermissionError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: PERMISSION_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: PERMISSION_ERROR_CODE,
}
NOT_A_DIRECTORY_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: NotADirectoryError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: NOT_A_DIRECTORY_ERROR_DESCRIPTION,
}
IS_A_DIRECTORY_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: IsADirectoryError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: IS_A_DIRECTORY_ERROR_DESCRIPTION,
}
INTERRUPTED_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: InterruptedError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: INTERRUPTED_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: INTERRUPTED_ERROR_CODE,
}
FILE_NOT_FOUND_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: FileNotFoundError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: FILE_NOT_FOUND_ERROR_DESCRIPTION,
}
FILE_EXISTS_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: FileExistsError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: FILE_EXISTS_ERROR_DESCRIPTION,
}
CONNECTION_RESET_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ConnectionResetError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: CONNECTION_RESET_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: CONNECTION_RESET_ERROR_CODE,
}
CONNECTION_REFUSED_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ConnectionRefusedError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: CONNECTION_REFUSED_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: CONNECTION_REFUSED_ERROR_CODE,
}
CONNECTION_ABORTED_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ConnectionAbortedError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: CONNECTION_ABORTED_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: CONNECTION_ABORTED_ERROR_CODE,
}
BROKEN_PIPE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: BrokenPipeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BROKEN_PIPE_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: BROKEN_PIPE_ERROR_CODE,
}
CONNECTION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ConnectionError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: CONNECTION_ERROR_DESCRIPTION,
}
CHILD_PROCESS_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ChildProcessError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: CHILD_PROCESS_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: CHILD_PROCESS_ERROR_CODE,
}
BLOCKING_IO_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: BlockingIOError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BLOCKING_IO_ERROR_DESCRIPTION,
	GENERIC_CODE_KEY: BLOCKING_IO_CODE,
}
OS_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: OSError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: OS_ERROR_DESCRIPTION,
}
UNBOUND_LOCAL_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: UnboundLocalError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: UNBOUND_LOCAL_ERROR_DESCRIPTION,
}
NAME_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: NameError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: NAME_ERROR_DESCRIPTION,
}
MEMORY_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: MemoryError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: MEMORY_ERROR_DESCRIPTION,
}
KEY_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: KeyError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: KEY_ERROR_DESCRIPTION,
}
INDEX_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: IndexError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: INDEX_ERROR_DESCRIPTION,
}
LOOKUP_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: LookupError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: LOOKUP_ERROR_DESCRIPTION,
}
MODULE_NOT_FOUND_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ModuleNotFoundError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: MODULE_NOT_FOUND_ERROR_DESCRIPTION,
}
IMPORT_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ImportError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: IMPORT_ERROR_DESCRIPTION,
}
END_OF_FILE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: EOFError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: EOF_ERROR_DESCRIPTION,
}
BUFFER_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: BufferError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BUFFER_ERROR_DESCRIPTION,
}
ATTRIBUTE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: AttributeError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: ATTRIBUTE_ERROR_DESCRIPTION,
}
ASSERTION_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: AssertionError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: ASSERTION_ERROR_DESCRIPTION,
}
ZERO_DIVISION_ERROR_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ZeroDivisionError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: ZERO_DIVISION_ERROR_DESCRIPTION,
}
OVERFLOW_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: OverflowError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: OVERFLOW_ERROR_DESCRIPTION,
}
FLOATING_POINT_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: FloatingPointError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: FLOATING_POINT_ERROR_DESCRIPTION,
}
ARITHMETIC_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: ArithmeticError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: ARITHMETIC_ERROR_DESCRIPTION,
}
BINASCII_INCOMPLETE_ERROR_DICT: dict = {
	GENERIC_ERROR_KEY: BinasciiIncompleteError.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BINASCII_INCOMPLETE_ERROR_DESCRIPTION,
}
BASE_EXCEPTION_DICT: dict = {
	GENERIC_ERROR_KEY: BaseException.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: BASE_EXCEPTION_ERROR_DESCRIPTION,
}
EXCEPTION_DICT: dict = {
	GENERIC_ERROR_KEY: Exception.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: EXCEPTION_ERROR_DESCRIPTION,
}
GENERATOR_EXIT_DICT: dict = {
	GENERIC_ERROR_KEY: GeneratorExit.__name__,
	GENERIC_MESSAGE_KEY: "",
	GENERIC_DESCRIPTION_KEY: GENERATOR_EXIT_ERROR_DESCRIPTION,
}

# -------------------- 'Master' error dictionary ---------------------
MASTER_EXCEPTION_DICT: dict = {
	UnicodeTranslateError.__name__: UNICODE_TRANSL_ERROR_DICT,
	UnicodeEncodeError.__name__: UNICODE_ENCODE_ERROR_DICT,
	UnicodeDecodeError.__name__: UNICODE_DECODE_ERROR_DICT,
	UnicodeError.__name__: UNICODE_ERROR_DICT,
	BinasciiError.__name__: BINASCII_ERROR_DICT,
	JSONDecodeError.__name__: JSON_DECODE_DICT,
	ValueError.__name__: VALUE_ERROR_ERROR_DICT,
	TypeError.__name__: TYPE_ERROR_DICT,
	SystemError.__name__: SYSTEM_ERROR_ERROR_DICT,
	TabError.__name__: TAB_ERROR_DICT,
	IndentationError.__name__: INDENTATION_ERROR_DICT,
	SyntaxError.__name__: SYNTAX_ERROR_DICT,
	StopIteration.__name__: STOP_ITERATION_ERROR_DICT,
	StopAsyncIteration.__name__: STOP_ASYNC_ITERATION_ERROR_DICT,
	RecursionError.__name__: RECURSION_ERROR_DICT,
	NotImplementedError.__name__: NOT_IMPLEMENTED_ERROR_DICT,
	RuntimeError.__name__: RUN_TIME_ERROR_ERROR_DICT,
	ReferenceError.__name__: REFERENCE_ERROR_DICT,
	TimeoutError.__name__: TIMEOUT_ERROR_DICT,
	ProcessLookupError.__name__: PROCESS_LOOKUP_ERROR_DICT,
	PermissionError.__name__: PERMISSION_ERROR_DICT,
	NotADirectoryError.__name__: NOT_A_DIRECTORY_ERROR_DICT,
	IsADirectoryError.__name__: IS_A_DIRECTORY_ERROR_DICT,
	InterruptedError.__name__: INTERRUPTED_ERROR_DICT,
	FileNotFoundError.__name__: FILE_NOT_FOUND_ERROR_DICT,
	FileExistsError.__name__: FILE_EXISTS_ERROR_DICT,
	ConnectionResetError.__name__: CONNECTION_RESET_ERROR_DICT,
	ConnectionRefusedError.__name__: CONNECTION_REFUSED_ERROR_DICT,
	ConnectionAbortedError.__name__: CONNECTION_ABORTED_ERROR_DICT,
	BrokenPipeError.__name__: BROKEN_PIPE_ERROR_DICT,
	ConnectionError.__name__: CONNECTION_ERROR_DICT,
	ChildProcessError.__name__: CHILD_PROCESS_ERROR_DICT,
	BlockingIOError.__name__: BLOCKING_IO_ERROR_DICT,
	OSError.__name__: OS_ERROR_ERROR_DICT,
	UnboundLocalError.__name__: UNBOUND_LOCAL_ERROR_DICT,
	NameError.__name__: NAME_ERROR_ERROR_DICT,
	MemoryError.__name__: MEMORY_ERROR_ERROR_DICT,
	KeyError.__name__: KEY_ERROR_DICT,
	IndexError.__name__: INDEX_ERROR_ERROR_DICT,
	LookupError.__name__: LOOKUP_ERROR_ERROR_DICT,
	ModuleNotFoundError.__name__: MODULE_NOT_FOUND_ERROR_DICT,
	ImportError.__name__: IMPORT_ERROR_DICT,
	EOFError.__name__: END_OF_FILE_ERROR_DICT,
	BufferError.__name__: BUFFER_ERROR_DICT,
	AttributeError.__name__: ATTRIBUTE_ERROR_DICT,
	AssertionError.__name__: ASSERTION_ERROR_DICT,
	ZeroDivisionError.__name__: ZERO_DIVISION_ERROR_ERROR_DICT,
	OverflowError.__name__: OVERFLOW_ERROR_DICT,
	FloatingPointError.__name__: FLOATING_POINT_ERROR_DICT,
	ArithmeticError.__name__: ARITHMETIC_ERROR_DICT,
	BinasciiIncompleteError.__name__: BINASCII_INCOMPLETE_ERROR_DICT,
	Exception.__name__: EXCEPTION_DICT,
	GeneratorExit.__name__: GENERATOR_EXIT_DICT,
	BaseException.__name__: BASE_EXCEPTION_DICT,
}
"""
Main mapping dict that holds exceptions and their associated error sub dicts.
Exceptions are listed in order of inheritance.
"""

EXCEPTION_TUPLE: tuple = (
	UnicodeTranslateError,
	UnicodeEncodeError,
	UnicodeDecodeError,
	UnicodeError,
	BinasciiError,
	JSONDecodeError,
	ValueError,
	TypeError,
	SystemError,
	TabError,
	IndentationError,
	SyntaxError,
	StopIteration,
	StopAsyncIteration,
	RecursionError,
	NotImplementedError,
	RuntimeError,
	ReferenceError,
	TimeoutError,
	ProcessLookupError,
	PermissionError,
	NotADirectoryError,
	IsADirectoryError,
	InterruptedError,
	FileNotFoundError,
	FileExistsError,
	ConnectionResetError,
	ConnectionRefusedError,
	ConnectionAbortedError,
	BrokenPipeError,
	ConnectionError,
	ChildProcessError,
	BlockingIOError,
	OSError,
	UnboundLocalError,
	NameError,
	MemoryError,
	KeyError,
	IndexError,
	LookupError,
	ModuleNotFoundError,
	ImportError,
	EOFError,
	BufferError,
	AttributeError,
	AssertionError,
	ZeroDivisionError,
	OverflowError,
	FloatingPointError,
	ArithmeticError,
	BinasciiIncompleteError,
	Exception,
	GeneratorExit,
	BaseException
)
"""
Tuple of exceptions listed in order of inheritance
with child classes being listed first.
"""

MASTER_EXCEPTION_TUPLE: tuple = EXCEPTION_TUPLE
"""
Tuple of all exceptions listed in order of inheritance
with child classes being listed first.
"""

SQLALCHEMY_AVAILABLE: bool = find_spec("sqlalchemy") is not None
if SQLALCHEMY_AVAILABLE:
	from sqlalchemy.exc import (
		AmbiguousForeignKeysError,
		ArgumentError,
		CircularDependencyError,
		CompileError,
		DBAPIError,
		DataError,
		DatabaseError,
		DisconnectionError,
		IdentifierError,
		IntegrityError,
		InterfaceError,
		InternalError,
		InvalidRequestError,
		InvalidatePoolError,
		MultipleResultsFound,
		NoForeignKeysError,
		NoInspectionAvailable,
		NoReferenceError,
		NoReferencedColumnError,
		NoReferencedTableError,
		NoResultFound,
		NoSuchColumnError,
		NoSuchModuleError,
		NoSuchTableError,
		NotSupportedError,
		ObjectNotExecutableError,
		OperationalError,
		PendingRollbackError,
		ProgrammingError,
		ResourceClosedError,
		SADeprecationWarning,
		SAPendingDeprecationWarning,
		SAWarning,
		SQLAlchemyError,
		StatementError,
		UnboundExecutionError,
		UnreflectableTableError,
		UnsupportedCompilationError,
	)

	# ------------------ 'SQLAlchemy' error message constants ---------------
	NO_SUCH_MODULE_ERROR_DESCRIPTION: str = "A dynamically-loaded database module of a particular name cannot be located."
	OBJECT_NOT_EXECUTABLE_ERROR_DESCRIPTION: str = "An object was passed to .execute() that can't be executed as SQL."
	NO_FOREIGN_KEYS_ERROR_DESCRIPTION: str = "During a join, no foreign keys could be located between two selectables."
	AMBIGUOUS_FOREIGN_KEYS_ERROR_DESCRIPTION: str = "During a join, more than one matching foreign key was located between two selectables."
	ARGUMENT_ERROR_DESCRIPTION: str = "Invalid or conflicting function argument was supplied."
	CIRCULAR_DEPENDENCY_ERROR_DESCRIPTION: str = "Topological sorts detected a circular dependency."
	UNSUPPORTED_COMPILATION_ERROR_DESCRIPTION: str = "Operation is not supported by the given compiler."
	COMPILE_ERROR_DESCRIPTION: str = "An error occurred during SQL compilation."
	IDENTIFIER_ERROR_DESCRIPTION: str = "Schema name is beyond the max character limit."
	INVALIDATE_POOL_ERROR_DESCRIPTION: str = "The connection pool should invalidate all stale connections."
	DISCONNECTION_ERROR_DESCRIPTION: str = "A disconnect was detected on a raw DB-API connection."
	NO_INSPECTION_AVAILABLE_ERROR_DESCRIPTION: str = "Subject produced no context for inspection."
	PENDING_ROLLBACK_ERROR_DESCRIPTION: str = "A transaction has failed and needs to be rolled back before; continuing."
	RESOURCE_CLOSED_ERROR_DESCRIPTION: str = "An operation was requested from a connection, cursor, or other object that's in a closed state."
	NO_SUCH_COLUMN_ERROR_DESCRIPTION: str = "A nonexistent column was requested from a `Row `."
	NO_RESULT_FOUND_ERROR_DESCRIPTION: str = "A database result was required, but none was found."
	MULTIPLE_RESULTS_FOUND_ERROR_DESCRIPTION: str = "A single database result was required, but more than one were found."
	NO_REFERENCED_TABLE_ERROR_DESCRIPTION: str = "`Foreign Key` references a `Table` that cannot be located."
	NO_REFERENCED_COLUMN_ERROR_DESCRIPTION: str = "`Foreign Key` references a `Column` that cannot be located."
	NO_REFERENCE_ERROR_DESCRIPTION: str = "`Foreign Key` references an unresolved attribute."
	NO_SUCH_TABLE_ERROR_DESCRIPTION: str = "`Table` does not exist or is not visible to a connection."
	UNREFLECTABLE_TABLE_ERROR_DESCRIPTION: str = "`Table` exists but can't be reflected."
	UNBOUND_EXECUTION_ERROR_DESCRIPTION: str = "SQL execution was attempted without a database connection to execute it on."
	INVALID_REQUEST_ERROR_DESCRIPTION: str = "SQLAlchemy was asked to do something it can't do."
	INTERFACE_ERROR_DESCRIPTION: str = "A DB-API InterfaceError occurred."
	DATA_ERROR_DESCRIPTION: str = "There was a problem with the data received from the DB-API"
	STATEMENT_ERROR_DESCRIPTION: str = "An error occurred during execution of a SQL statement."
	SQLALCHEMY_ERROR_DESCRIPTION: str = "A generic error occurred in SQLAlchemy."
	OPERATIONAL_ERROR_DESCRIPTION: str = "There was an operational error between SQLAlchemy and the DB-API"
	INTEGRITY_ERROR_DESCRIPTION: str = "The Integrity of the connection between SQLAlchemy and the DB-API was compromised."
	INTERNAL_ERROR_DESCRIPTION: str = "An internal error occurred between SQLAlchemy and the DB-API."
	PROGRAMMING_ERROR_DESCRIPTION: str = "A programming error occurred between SQLAlchemy and the DB-API."
	NOT_SUPPORTED_ERROR_DESCRIPTION: str = "SQLAlchemy attempted to use an unsupported function of the DB-API."
	DATABASE_ERROR_DESCRIPTION: str = "The DB-API has raised a DatabaseError."
	DBAPI_ERROR_DESCRIPTION: str = "An error occurred in the DB-API."
	SA_WARNING_DESCRIPTION: str = "Dubious SQLAlchemy runtime error detected."
	SA_PENDING_DEPRECATION_WARNING_DESCRIPTION: str = "SQLAlchemy features in use that will soon be marked as deprecated."
	SA_DEPRECATION_WARNING_DESCRIPTION: str = "SQLAlchemy features in use that have been marked as deprecated."

	# ------------------ 'SQLAlchemy' error code constants -------------------
	UNSUPPORTED_COMPILATION_ERROR_CODE: str = "l7de"
	SQLALCHEMY_ERROR_CODE: str = "code"
	INTERFACE_ERROR_CODE: str = "rvf5"
	DATABASE_ERROR_CODE: str = "4xp6"
	DATA_ERROR_CODE: str = "9h9h"
	OPERATIONAL_ERROR_CODE: str = "e3q8"
	INTEGRITY_ERROR_CODE: str = "gkpj"
	INTERNAL_ERROR_CODE: str = "2j85"
	PROGRAMMING_ERROR_CODE: str = "f405"
	NOT_SUPPORTED_ERROR_CODE: str = "tw8g"
	DB_API_ERROR_CODE: str = "dbapi"

	# ------------------- 'SQLAlchemy' error dictionaries --------------------
	OBJECT_NOT_EXECUTABLE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: ObjectNotExecutableError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: OBJECT_NOT_EXECUTABLE_ERROR_DESCRIPTION,
	}
	NO_SUCH_MODULE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoSuchModuleError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_SUCH_MODULE_ERROR_DESCRIPTION,
	}
	NO_FOREIGN_KEYS_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoForeignKeysError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_FOREIGN_KEYS_ERROR_DESCRIPTION,
	}
	AMBIGUOUS_FOREIGN_KEYS_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: AmbiguousForeignKeysError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: AMBIGUOUS_FOREIGN_KEYS_ERROR_DESCRIPTION,
	}
	ARGUMENT_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: ArgumentError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: ARGUMENT_ERROR_DESCRIPTION,
	}
	CIRCULAR_DEPENDENCY_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: CircularDependencyError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: CIRCULAR_DEPENDENCY_ERROR_DESCRIPTION,
	}
	UNSUPPORTED_COMPILATION_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: UnsupportedCompilationError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: UNSUPPORTED_COMPILATION_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: UNSUPPORTED_COMPILATION_ERROR_CODE
	}
	COMPILE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: CompileError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: COMPILE_ERROR_DESCRIPTION,
	}
	IDENTIFIER_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: IdentifierError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: IDENTIFIER_ERROR_DESCRIPTION,
	}
	INVALIDATE_POOL_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: InvalidatePoolError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: INVALIDATE_POOL_ERROR_DESCRIPTION,
	}
	DISCONNECTION_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: DisconnectionError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: DISCONNECTION_ERROR_DESCRIPTION,
	}
	NO_INSPECTION_AVAILABLE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoInspectionAvailable.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_INSPECTION_AVAILABLE_ERROR_DESCRIPTION,
	}
	PENDING_ROLLBACK_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: PendingRollbackError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: PENDING_ROLLBACK_ERROR_DESCRIPTION,
	}
	RESOURCE_CLOSED_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: ResourceClosedError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: RESOURCE_CLOSED_ERROR_DESCRIPTION,
	}
	NO_SUCH_COLUMN_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoSuchColumnError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_SUCH_COLUMN_ERROR_DESCRIPTION,
	}
	NO_RESULT_FOUND_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoResultFound.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_RESULT_FOUND_ERROR_DESCRIPTION,
	}
	MULTIPLE_RESULTS_FOUND_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: MultipleResultsFound.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: MULTIPLE_RESULTS_FOUND_ERROR_DESCRIPTION,
	}
	NO_REFERENCED_TABLE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoReferencedTableError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_REFERENCED_TABLE_ERROR_DESCRIPTION,
	}
	NO_REFERENCED_COLUMN_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoReferencedColumnError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_REFERENCED_COLUMN_ERROR_DESCRIPTION,
	}
	NO_REFERENCE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoReferenceError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_REFERENCE_ERROR_DESCRIPTION,
	}
	NO_SUCH_TABLE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NoSuchTableError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NO_SUCH_TABLE_ERROR_DESCRIPTION,
	}
	UNREFLECTABLE_TABLE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: UnreflectableTableError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: UNREFLECTABLE_TABLE_ERROR_DESCRIPTION,
	}
	UNBOUND_EXECUTION_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: UnboundExecutionError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: UNBOUND_EXECUTION_ERROR_DESCRIPTION,
	}
	INVALID_REQUEST_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: InvalidRequestError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: INVALID_REQUEST_ERROR_DESCRIPTION,
	}
	INTERFACE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: InterfaceError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: INTERFACE_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: INTERFACE_ERROR_CODE
	}
	DATA_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: DataError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: DATA_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: DATA_ERROR_CODE
	}
	STATEMENT_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: StatementError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: STATEMENT_ERROR_DESCRIPTION,
	}
	SQLALCHEMY_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: SQLAlchemyError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: SQLALCHEMY_ERROR_DESCRIPTION,
	}
	OPERATIONAL_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: OperationalError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: OPERATIONAL_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: OPERATIONAL_ERROR_CODE
	}
	INTEGRITY_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: IntegrityError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: INTEGRITY_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: INTEGRITY_ERROR_CODE
	}
	INTERNAL_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: InternalError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: INTERNAL_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: INTERNAL_ERROR_CODE
	}
	PROGRAMMING_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: ProgrammingError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: PROGRAMMING_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: PROGRAMMING_ERROR_CODE
	}
	NOT_SUPPORTED_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: NotSupportedError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: NOT_SUPPORTED_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: NOT_SUPPORTED_ERROR_CODE
	}
	DATABASE_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: DatabaseError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: DATABASE_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: DATABASE_ERROR_CODE
	}
	DBAPI_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: DBAPIError.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: DBAPI_ERROR_DESCRIPTION,
		GENERIC_CODE_KEY: DB_API_ERROR_CODE
	}
	SA_DEPRECATION_WARNING_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: SADeprecationWarning.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: SA_DEPRECATION_WARNING_DESCRIPTION,
	}
	SA_PENDING_DEPRECATION_WARNING_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: SAPendingDeprecationWarning.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: SA_PENDING_DEPRECATION_WARNING_DESCRIPTION,
	}
	SA_WARNING_ERROR_DICT: dict = {
		GENERIC_ERROR_KEY: SAWarning.__name__,
		GENERIC_MESSAGE_KEY: "",
		GENERIC_DESCRIPTION_KEY: SA_WARNING_DESCRIPTION,
	}

	MASTER_EXCEPTION_DICT.update(
		{
			ObjectNotExecutableError.__name__: OBJECT_NOT_EXECUTABLE_ERROR_DICT,
			NoSuchModuleError.__name__: NO_SUCH_MODULE_ERROR_DICT,
			NoForeignKeysError.__name__: NO_FOREIGN_KEYS_ERROR_DICT,
			AmbiguousForeignKeysError.__name__: AMBIGUOUS_FOREIGN_KEYS_ERROR_DICT,
			ArgumentError.__name__: ARGUMENT_ERROR_DICT,
			CircularDependencyError.__name__: CIRCULAR_DEPENDENCY_ERROR_DICT,
			UnsupportedCompilationError.__name__: UNSUPPORTED_COMPILATION_ERROR_DICT,
			CompileError.__name__: COMPILE_ERROR_DICT,
			IdentifierError.__name__: IDENTIFIER_ERROR_DICT,
			InvalidatePoolError.__name__: INVALIDATE_POOL_ERROR_DICT,
			DisconnectionError.__name__: DISCONNECTION_ERROR_DICT,
			NoInspectionAvailable.__name__: NO_INSPECTION_AVAILABLE_ERROR_DICT,
			PendingRollbackError.__name__: PENDING_ROLLBACK_ERROR_DICT,
			ResourceClosedError.__name__: RESOURCE_CLOSED_ERROR_DICT,
			NoSuchColumnError.__name__: NO_SUCH_COLUMN_ERROR_DICT,
			NoResultFound.__name__: NO_RESULT_FOUND_ERROR_DICT,
			MultipleResultsFound.__name__: MULTIPLE_RESULTS_FOUND_ERROR_DICT,
			NoReferencedTableError.__name__: NO_REFERENCED_TABLE_ERROR_DICT,
			NoReferencedColumnError.__name__: NO_REFERENCED_COLUMN_ERROR_DICT,
			NoReferenceError.__name__: NO_REFERENCE_ERROR_DICT,
			NoSuchTableError.__name__: NO_SUCH_TABLE_ERROR_DICT,
			UnreflectableTableError.__name__: UNREFLECTABLE_TABLE_ERROR_DICT,
			UnboundExecutionError.__name__: UNBOUND_EXECUTION_ERROR_DICT,
			InvalidRequestError.__name__: INVALID_REQUEST_ERROR_DICT,
			InterfaceError.__name__: INTERFACE_ERROR_DICT,
			DataError.__name__: DATA_ERROR_DICT,
			StatementError.__name__: STATEMENT_ERROR_DICT,
			SQLAlchemyError.__name__: SQLALCHEMY_ERROR_DICT,
			OperationalError.__name__: OPERATIONAL_ERROR_DICT,
			IntegrityError.__name__: INTEGRITY_ERROR_DICT,
			InternalError.__name__: INTERNAL_ERROR_DICT,
			ProgrammingError.__name__: PROGRAMMING_ERROR_DICT,
			NotSupportedError.__name__: NOT_SUPPORTED_ERROR_DICT,
			DatabaseError.__name__: DATABASE_ERROR_DICT,
			DBAPIError.__name__: DBAPI_ERROR_DICT,
			SADeprecationWarning.__name__: SA_DEPRECATION_WARNING_ERROR_DICT,
			SAPendingDeprecationWarning.__name__: SA_PENDING_DEPRECATION_WARNING_ERROR_DICT,
			SAWarning.__name__: SA_WARNING_ERROR_DICT,
		}
	)

	SA_EXCEPTION_TUPLE: tuple = (
		ObjectNotExecutableError,
		NoSuchModuleError,
		NoForeignKeysError,
		AmbiguousForeignKeysError,
		ArgumentError,
		CircularDependencyError,
		UnsupportedCompilationError,
		CompileError,
		IdentifierError,
		InvalidatePoolError,
		DisconnectionError,
		NoInspectionAvailable,
		PendingRollbackError,
		ResourceClosedError,
		NoSuchColumnError,
		NoResultFound,
		MultipleResultsFound,
		NoReferencedTableError,
		NoReferencedColumnError,
		NoReferenceError,
		NoSuchTableError,
		UnreflectableTableError,
		UnboundExecutionError,
		InvalidRequestError,
		InterfaceError,
		DataError,
		StatementError,
		SQLAlchemyError,
		OperationalError,
		IntegrityError,
		InternalError,
		ProgrammingError,
		NotSupportedError,
		DatabaseError,
		DBAPIError,
		SADeprecationWarning,
		SAPendingDeprecationWarning,
		SAWarning,
	)
	"""
	Tuple of SQLAlchemy exceptions listed in order of inheritance
	with child classes being listed first.
	"""

	MASTER_EXCEPTION_TUPLE = (SA_EXCEPTION_TUPLE + EXCEPTION_TUPLE)
