class FileNotGivenError(Exception):
    """
    An error which occurs when no file is given in command line when programm is being run.
    """
    def __init__(self) -> None:
        super().__init__("A data file location must be given as a command line argument.")

class SectionNotFoundError(Exception):
    """An error which occurs when during creating data for database from file
    programm could not find a <section_name> section in this file.
    """
    def __init__(self, section_name: str) -> None:
        super().__init__(f"Could not find required section: {section_name}")

class WorkingIndexOutOfRange(Exception):
    """An error which occurs when there was attempt to get section data from given
    data(as a list[str] or file_handle) and working index was out of range of data.
    """
    def __init__(self, function_name) -> None:
        super().__init__(f"Working index in function {function_name} is out of range.")

class NumericTypeExpectedError(Exception):
    """An error which occurs when programm expected in some place a numeric type
    of data from data from file.
    """
    def __init__(self) -> None:
        super().__init__(f"Expected a numeric data.")

class StopIDOutOfRange(Exception):
    """An error which occurs in get_stop_neighbours() function, when you cannot approximate
    location of stop (using stop complexes with lower ID), due to lack of data."""
    def __init__(self) -> None:
        super().__init__("Aprroximation of location to stop complex with lower ID failed - lack of data.")