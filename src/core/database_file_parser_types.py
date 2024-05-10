from typing import List, Tuple, IO, Dict, Any, Union

# This is a list of all types used for generating data for databse.
# These types may be find in database_builder and database_file_parser

CourseParsedData =          List[Tuple[str, str, str, int]]
DayLineParsedData =         List[Tuple[str, str, str]]
DayTypeParsedData =         List[Tuple[str, str]]
FileHandle =                IO
LineNormalizedData =        List[Tuple[str, int]]
LineParsedData =            List[Tuple[str, str]]
LinesList =                 List[str]
LineTypeParsedData =        List[Tuple[int, str]]
PlaceParsedData =           List[Tuple[int, str]]
RawText =                   List[str]
StopComplexParsedData =     List[Tuple[int, str, str]]
StopCourseParsedData =      List[Tuple[int, int, int]]
StopNeighbourParsedData =   List[Tuple[int, int, float]]
StopNormalizedData =        List[Tuple[int, str, int, float, float, int, int]]
StopParsedData =            List[Tuple[int, str, int, float, float, str, str]]
StopVaraintParsedData =     List[Tuple[str, str, int, int, int, int]]
TownParsedData =            List[Tuple[str, str]]
VaraintParsedData =         List[Tuple[str, str, str, int, str, int]]
VariantNormalizedData =     List[Tuple[str, str, str, int, int, int]]
