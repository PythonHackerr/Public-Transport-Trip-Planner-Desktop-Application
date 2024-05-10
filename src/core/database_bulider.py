import sys
import os

sys.path.append(os.getcwd())
import oracledb
from src.core.database_file_parser import *
from src.core.database_creator_errors import FileNotGivenError



def create_stop_complex_table(cursor) -> None:
    """Create table Stop_Complex in database which will hold information about all stop complexes described in Warsaw's public transport data file.
    Table will hold ID of complex, its name and ID of town in which the complex is.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_stop_complex = """DROP TABLE Stop_Complex"""

    create_stop_complex = """CREATE TABLE Stop_Complex(
    STOP_COMPLEX_ID NUMBER(4) NOT NULL PRIMARY KEY,
    NAME VARCHAR2(70) NOT NULL,
    TOWN_ID VARCHAR2(4) NOT NULL
    )"""

    alter_stop_complex_fk = """ALTER TABLE Stop_Complex
    ADD CONSTRAINT Stop_Complex_FK FOREIGN KEY (TOWN_ID) REFERENCES TOWN(TOWN_ID)"""

    cursor.execute(drop_stop_complex)
    cursor.execute(create_stop_complex)
    cursor.execute(alter_stop_complex_fk)

def create_stop_table(cursor) -> None:
    """Create table Stop in database, which will hold data about all single Stops described in WTP data file.
    This table will hold ID of stop, number of stop within its complex, ID of stop's complex, its latitude and longitude,
    ID of street where this stop is and ID of direction where the vechcle will go from this stop
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_stop = """DROP TABLE Stop"""

    create_stop = """CREATE TABLE Stop(
    STOP_ID NUMBER(6) NOT NULL PRIMARY KEY,
    STOP_NUMBER CHAR(2) NOT NULL,
    STOP_COMPLEX_ID NUMBER(4) NOT NULL,
    LATITUDE NUMBER(8, 6),
    LONGITUDE NUMBER(8, 6),
    STREET NUMBER(4),
    DIRECTION NUMBER(4)
    )"""

    alter_stop_stop_complex_fk = """ALTER TABLE Stop
    ADD CONSTRAINT Stop_Stop_Complex_FK FOREIGN KEY (STOP_COMPLEX_ID) REFERENCES Stop_Complex(STOP_COMPLEX_ID) ON DELETE CASCADE"""

    alter_stop_street_fk = """ALTER TABLE Stop
    ADD CONSTRAINT Stop_Street_Place_FK FOREIGN KEY (Street) REFERENCES Place(Place_ID)"""

    alter_stop_direction_fk = """ALTER TABLE Stop
    ADD CONSTRAINT Stop_Direction_Place_FK FOREIGN KEY (Direction) REFERENCES Place(Place_ID)"""

    cursor.execute(drop_stop)
    cursor.execute(create_stop)
    cursor.execute(alter_stop_stop_complex_fk)
    cursor.execute(alter_stop_street_fk)
    cursor.execute(alter_stop_direction_fk)

def insert_stop_complex_data_into_database(cursor, stop_complex_data: StopComplexParsedData) -> None:
    """Insert data into StopComplex table.

    Args:
        cursor : Cursor holding database connection.
        stop_complex_data (StopComplexParsedData): Data which will be inserted into StopComplex table in database.
        Data must be generated by get_raw_data_stop_complex() function.
    """
    cursor.executemany("""INSERT INTO Stop_Complex VALUES(:1,:2,:3)""", stop_complex_data)

def insert_stop_data_into_database(cursor, stop_data: StopNormalizedData) -> None:
    """Insert data into Stop table.

    Args:
        cursor : Cursor holding database connection.
        stop_data (StopNormalizedData):  Data which will be inserted into Stop table in database.
         Data must be generated by get_raw_data_stop() function and then changed by change_stop_and_variant_places() function.
    """
    cursor.executemany("""INSERT INTO Stop VALUES(:1,:2,:3,:4,:5,:6,:7)""", stop_data)

def drop_constraints(cursor) -> None:
    """Drop all foreign key constraints which are used in database.
    This function is used while dropping all the tables.

    Args:
        cursor : Cursor holding database connection.
    """

    drop_stop_street_place_fk = """ALTER TABLE Stop
    DROP CONSTRAINT Stop_Street_Place_FK"""

    drop_stop_direction_place_fk = """ALTER TABLE Stop
    DROP CONSTRAINT Stop_Direction_Place_FK"""

    drop_stop_stop_complex = """ALTER TABLE Stop
    DROP CONSTRAINT Stop_Stop_Complex_FK"""

    drop_stop_complex_fk = """ALTER TABLE Stop_Complex
    DROP CONSTRAINT Stop_Complex_FK"""

    drop_line_type_fk = """ALTER TABLE LINE
    DROP CONSTRAINT Line_FK"""

    drop_variant_place_fk = """ALTER TABLE Variant
    DROP CONSTRAINT Varaint_dir_description_FK"""

    drop_variant_line_fk = """ALTER TABLE Variant
    DROP CONSTRAINT Variant_Line_FK"""

    drop_stop_course_course_foreign_key = """ALTER TABLE Stop_Course
    DROP CONSTRAINT Stop_Course_Course_FK"""

    drop_stop_course_stop_foreign_key = """ALTER TABLE Stop_Course
    DROP CONSTRAINT Stop_Course_Stop_FK"""

    drop_stop_neighbour_stop_id_fk = """ALTER TABLE Stop_Neighbour
    DROP CONSTRAINT Stop_ID_FK"""

    drop_stop_neighbour_neighbour_id_fk = """ALTER TABLE Stop_Neighbour
    DROP CONSTRAINT Neighbour_ID_FK"""

    drop_stop_variant_variant_fk = """ALTER TABLE Stop_Variant
    DROP CONSTRAINT Stop_Variant_Variant_FK"""

    drop_stop_variant_stop_fk = """ALTER TABLE Stop_Variant
    DROP CONSTRAINT Stop_Variant_Stop_FK"""

    drop_course_day_type_fk = """ALTER TABLE Course
    DROP CONSTRAINT Course_Day_Type_FK"""

    drop_course_variant_fk = """ALTER TABLE Course
    DROP CONSTRAINT Course_Variant_FK"""

    drop_day_line_day_type_fk = """ALTER TABLE Day_Line
    DROP CONSTRAINT Day_Line_Day_FK"""

    drop_day_line_line_fk = """ALTER TABLE Day_Line
    DROP CONSTRAINT Day_Line_Line_FK"""

    cursor.execute(drop_stop_street_place_fk)
    cursor.execute(drop_stop_direction_place_fk)
    cursor.execute(drop_stop_stop_complex)
    cursor.execute(drop_stop_complex_fk)
    cursor.execute(drop_line_type_fk)
    cursor.execute(drop_variant_place_fk)
    cursor.execute(drop_variant_line_fk)
    cursor.execute(drop_stop_course_course_foreign_key)
    cursor.execute(drop_stop_course_stop_foreign_key)
    cursor.execute(drop_stop_neighbour_stop_id_fk)
    cursor.execute(drop_stop_neighbour_neighbour_id_fk)
    cursor.execute(drop_stop_variant_variant_fk)
    cursor.execute(drop_stop_variant_stop_fk)
    cursor.execute(drop_course_day_type_fk)
    cursor.execute(drop_course_variant_fk)
    cursor.execute(drop_day_line_day_type_fk)
    cursor.execute(drop_day_line_line_fk)

def create_variant_table(cursor) -> None:
    """Create Variant table which will hold information about all variants of all lines.
    This table will hold information about variant's ID, its line, name, direction (either A or B), level ("importance" of variant), descripition of direction and flag wheter this variant is 'normal' one.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_variant = """DROP TABLE Variant"""

    create_variant = """CREATE TABLE Variant(
    Variant_ID NUMBER(4) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Variant_PK PRIMARY KEY,
    Line_ID VARCHAR2(4) NOT NULL,
    Variant_name VARCHAR2(8) NOT NULL,
    Direction CHAR(1),
    Dir_level NUMBER(1),
    Dir_description NUMBER(4),
    Is_basic NUMBER(1) NOT NULL,
    CONSTRAINT variant_direction CHECK (Direction IN ('A', 'B')),
    CONSTRAINT variant_is_basic CHECK (Is_basic IN (0, 1))
    )"""

    alter_variant_desc = """ALTER TABLE Variant
    ADD CONSTRAINT Varaint_dir_description_FK FOREIGN KEY (Dir_description) REFERENCES Place(Place_ID)"""

    alter_variant_line = """ALTER TABLE Variant
    ADD CONSTRAINT Variant_Line_FK FOREIGN KEY (Line_ID) REFERENCES Line(Line_ID)
    """

    cursor.execute(drop_variant)
    cursor.execute(create_variant)
    cursor.execute(alter_variant_desc)
    cursor.execute(alter_variant_line)

def insert_variant_data_into_table(cursor, variant_data: VariantNormalizedData) ->  None:
    """Insert data into Variant table.

    Args:
        cursor : Cursor holding database connection.
        variant_data (VariantNormalizedData): Data which will be inserted into Variant table in database.
        Data must be generated by get_raw_variant_and_line_data() function and then changed by change_stop_and_variant_places() function.
    """
    cursor.executemany("""INSERT INTO Variant VALUES(DEFAULT, :1,:2,:3,:4,:5,:6)""", variant_data)

def create_stop_course_table(cursor) -> None:
    """Crete table Stop_Course, which will hold information about every single stop on every single course and time of arrival on this stop given course.
        This table also holds data about chunk of given stop in course: two rows in stop_course have the same chunk number, if they stops are in similar positions
        and time of departure are on slimar time. Chunks are used to download data to create navigation.
        This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.

    """

    drop_stop_course = """DROP TABLE Stop_Course"""

    create_stop_course = """CREATE TABLE Stop_Course(
    SC_ID NUMBER(7) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Stop_Course_PK PRIMARY KEY,
    Course_ID NUMBER(6) NOT NULL,
    Stop_ID NUMBER(6) NOT NULL,
    Departure_time NUMBER(4),
    Chunk NUMBER(5)
    )"""
    alter_stop_course_stop = """ALTER TABLE Stop_Course
    ADD CONSTRAINT Stop_Course_Stop_FK FOREIGN KEY (Stop_ID) REFERENCES Stop(Stop_ID)
    """
    alter_stop_course_course = """ALTER TABLE Stop_Course
    ADD CONSTRAINT Stop_Course_Course_FK FOREIGN KEY (Course_ID) REFERENCES Course(Course_ID)
    """

    cursor.execute(drop_stop_course)
    cursor.execute(create_stop_course)
    cursor.execute(alter_stop_course_stop)
    cursor.execute(alter_stop_course_course)

def insert_stop_course_data_into_table(cursor, stop_course_data: StopCourseParsedData) -> None:
    """ Insert data into Stop_Course table

    Args:
        cursor : Cursor holding database connection.
        stop_course_data (StopCourseParsedData): Data which will be inserted into Stop_Course table in database.
        Data must be generated by get_raw_data_stop_course() function.
    """
    cursor.executemany("""INSERT INTO Stop_Course VALUES(DEFAULT, :1, :2, :3, :4)""", stop_course_data)

def create_stop_neighbour_table(cursor) -> None:
    """Crete table Stop_Neighbour, which will hold information about all closest another stops of given stop and distance between them.
    Data is stored as: stop_ID, neighbour_ID and distance in meters.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_stop_neighbour = """DROP TABLE Stop_Neighbour"""

    create_stop_neighbour = """CREATE TABLE Stop_Neighbour (
    SN_ID NUMBER (7) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Stop_Neighbour_PK PRIMARY KEY,
    Stop_ID NUMBER(6) NOT NULL,
    Neighbour_ID NUMBER(6) NOT NULL,
    Distance NUMBER(10, 6) NOT NULL
    )"""

    alter_stop_neighbour_stop_id_fk = """ALTER TABLE Stop_Neighbour
    ADD CONSTRAINT Stop_ID_FK FOREIGN KEY (Stop_ID) REFERENCES Stop(Stop_ID)"""

    alter_stop_neighbour_neighbour_id_fk = """ALTER TABLE Stop_Neighbour
    ADD CONSTRAINT Neighbour_ID_FK FOREIGN KEY (Neighbour_ID) REFERENCES Stop(Stop_ID)"""

    cursor.execute(drop_stop_neighbour)
    cursor.execute(create_stop_neighbour)
    cursor.execute(alter_stop_neighbour_stop_id_fk)
    cursor.execute(alter_stop_neighbour_neighbour_id_fk)

def insert_data_into_stop_neighbour(cursor, stop_neighbour_data: StopNeighbourParsedData) -> None:
    """ Insert data into Stop_Neighbour table.

    Args:
        cursor : Cursor holding database connection.
        stop_neighbour_data (StopNeighbourParsedData):  Data which will be inserted into Stop_Neighbour table in database.
        Data must be generated by get_sttop_neighbours() function.
    """
    cursor.executemany("INSERT INTO Stop_Neighbour VALUES (DEFAULT, :1, :2, :3)", stop_neighbour_data)


def create_stop_variant_table(cursor):
    """Create table Stop_Variant, which will describe information about stops which will be encountered on given variant.
    Data is stored as follows: Variant_ID, order of Stop on given variant, Id of Stop, flag whether stop is on request, and number of zone of this stop.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """
    drop_stop_variant = """DROP TABLE Stop_Variant"""

    create_stop_variant = """CREATE TABLE Stop_Variant(
    SV_ID NUMBER(6) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Stop_Varaint_PK PRIMARY KEY,
    Variant_ID NUMBER(4) NOT NULL,
    Variant_Order NUMBER(2) NOT NULL,
    Stop_ID NUMBER(6) NOT NULL,
    On_request NUMBER(1),
    Zone_number NUMBER(1),
    CONSTRAINT sv_on_request CHECK (On_request IN (0,1)),
    CONSTRAINT sv_zone CHECK(Zone_number IN (1,2))
    )"""

    alter_stop_variant_variant_fk = """ALTER TABLE Stop_Variant
    ADD CONSTRAINT Stop_Variant_Variant_FK FOREIGN KEY (Variant_ID) REFERENCES Variant(Variant_ID)"""

    alter_stop_variant_stop_fk = """ALTER TABLE Stop_Variant
    ADD CONSTRAINT Stop_Variant_Stop_FK FOREIGN KEY (Stop_ID) REFERENCES Stop(Stop_ID)"""

    cursor.execute(drop_stop_variant)
    cursor.execute(create_stop_variant)
    cursor.execute(alter_stop_variant_variant_fk)
    cursor.execute(alter_stop_variant_stop_fk)

def insert_data_into_stop_variant(cursor, stop_variant_data: StopVaraintParsedData) -> None:
    """Insert data into Stop_Neighbour table.

    Args:
        cursor : Cursor holding database connection.
        stop_variant_data (StopVaraintParsedData): Data which will be inserted into Stop_Variant table in database.
        Data must be generated by get_raw_data_stop_variant() function.
    """
    cursor.executemany("""INSERT INTO Stop_Variant VALUES (DEFAULT, get_variant_id_by_line_and_var_name(:1, :2), :3,:4,:5,:6)""", stop_variant_data)

def create_get_variant_id_by_line_and_var_name_function(cursor) -> None:
    """Create and compile SQL/PL function  get_variant_id_by_line_and_var_name() which will return Id of Variant given its line number and variant name.

    Args:
        cursor : Cursor holding database connection.
    """

    create_function = """
    CREATE OR replace FUNCTION get_variant_id_by_line_and_var_name(line VARCHAR2, var_name VARCHAR2)
    RETURN NUMBER
    AS
        var_id NUMBER;
    BEGIN
        SELECT Variant_ID
        INTO var_id
        FROM Variant
        WHERE Line_ID = line AND variant_name = var_name;

        RETURN var_id;
    END;
    """
    cursor.execute(create_function)

def create_course_table(cursor) -> None:
    """Create Course table, which will hold information about all the courses of given line and variant.
    Data is stored as follows: course numeric ID, Varaint_ID, day_type ID and time of start of this course.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_course = """DROP TABLE Course"""

    create_course = """CREATE TABLE Course(
    Course_ID NUMBER(6) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Course_PK PRIMARY KEY,
    Variant_ID NUMBER(4) NOT NULL,
    Day_Type_ID CHAR(2) NOT NULL,
    Start_time NUMBER(4) NOT NULL
    )"""

    alter_course_variant_fk = """ALTER TABLE Course
    ADD CONSTRAINT Course_Variant_FK FOREIGN KEY (Variant_ID) REFERENCES Variant(Variant_ID)"""

    alter_course_day_type = """ALTER TABLE Course
    ADD CONSTRAINT Course_Day_Type_FK FOREIGN KEY (Day_Type_ID) REFERENCES Day_Type(Day_Type_ID)"""

    cursor.execute(drop_course)
    cursor.execute(create_course)
    cursor.execute(alter_course_variant_fk)
    cursor.execute(alter_course_day_type)

def insert_data_into_course_table(cursor, course_data: CourseParsedData) -> None:
    """Insert data into Course table in database.

    Args:
        cursor : Cursor holding database connection.
        course_data (CourseParsedData): Data which will be inserted into Course table in database.
        Data must be generated by get_raw_data_course() function.
    """
    cursor.executemany("""INSERT INTO Course VALUES(DEFAULT, get_variant_id_by_line_and_var_name(:1,:2),:3,:4)""", course_data)

def create_place_table(cursor) -> None:
    """Create table Place which will hold information about various places which are mentioned in WTP data file.
    Data is stored as follows:  numeric ID and name of the place.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """
    drop_place = """DROP TABLE Place"""

    create_place = """CREATE TABLE Place(
    Place_ID NUMBER(4) NOT NULL CONSTRAINT Place_PK PRIMARY KEY,
    Place_Name VARCHAR2(35) NOT NULL
    )"""

    cursor.execute(drop_place)
    cursor.execute(create_place)

def insert_place_data_into_table(cursor, place_data: PlaceParsedData) -> None:
    """Insert data into Place table in database.

    Args:
        cursor : Cursor holding database connection.
        place_data (CourseParsedData): Data which will be inserted into Place table in database.
        Data must be generated by change_stop_and_variant_places() function.
    """
    cursor.executemany("""INSERT INTO Place VALUES(:1, :2)""", place_data)

def create_line_table(cursor):
    """Create table which will hold information about lines which are described in WTP data file.
    Data is stored as follows: Line name and line type.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """
    drop_line_table = """ DROP TABLE LINE
    """
    create_line_table = """CREATE TABLE LINE(
    LINE_ID VARCHAR2(4) NOT NULL CONSTRAINT LINE_PK PRIMARY KEY,
    LINE_TYPE_ID NUMBER(2) NOT NULL
    )"""

    alter_line_table = """ALTER TABLE LINE
    ADD CONSTRAINT Line_FK FOREIGN KEY (LINE_TYPE_ID) REFERENCES LINE_TYPE(TYPE_ID)
    """
    cursor.execute(drop_line_table)
    cursor.execute(create_line_table)
    cursor.execute(alter_line_table)

def create_line_type_table(cursor) -> None:
    """Create Line_Type table which will hold information about line types which occurs in WTP data file.
    Data is stored as follows: line type numeric ID and then its name.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """
    drop_line_type = """DROP TABLE LINE_TYPE"""

    create_line_type = """CREATE TABLE LINE_TYPE(
    TYPE_ID NUMBER(2) NOT NULL CONSTRAINT LINE_TYPE_PK PRIMARY KEY,
    TYPE_NAME VARCHAR2(50) NOT NULL
    )
    """

    cursor.execute(drop_line_type)
    cursor.execute(create_line_type)

def insert_data_into_line_type_table(cursor, line_type_data: LineTypeParsedData) -> None:
    """Insert data into LineType table in database.

    Args:
        cursor : Cursor holding database connection.
        place_data (LineTypeParsedData): Data which will be inserted into LineType table in database.
        Data must be generated by parse_line_data() function, which requires data from get_raw_variant_and_line_data() function.
    """
    cursor.executemany("INSERT INTO Line_Type VALUES(:1, :2)", line_type_data)

def insert_data_into_line_table(cursor, line_data: LineParsedData) -> None:
    """Insert data into Line table in database.

    Args:
        cursor (_type_): Cursor holding database connection.
        line_data (LineParsedData):  Data which will be inserted into Line table in database.
        Data must be generated by parse_line_data() function, which requires data from get_raw_variant_and_line_data() function.
    """
    cursor.executemany("INSERT INTO Line VALUES(:1, :2)", line_data)

def create_town_table(cursor) -> None:
    """ Create Town table, which will hold information about towns in which there are stop complexes.
    Data is stored as follows: two-leeter ID of town and town name.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_town = """DROP TABLE Town
    """

    create_town = """CREATE TABLE Town(
    TOWN_ID VARCHAR2(4) NOT NULL CONSTRAINT TOWN_PK PRIMARY KEY,
    TOWN_NAME VARCHAR2(35) NOT NULL
    )"""

    cursor.execute(drop_town)
    cursor.execute(create_town)

def insert_town_data_into_databse(cursor, town_data: TownParsedData) -> None:
    """Insert data into Town table.

    Args:
        cursor : Cursor holding database connection.
        town_data (TownParsedData): Data which will be inserted into Town table in database.
        Data must be generated by get_raw_data_town() function.
    """
    cursor.executemany("""INSERT INTO Town VALUES(:1, :2)""", town_data)

def create_day_type_table(cursor) -> None:
    """Create table Day_Type, which will hold information about what day types are used in choosing which courses are going on which day.
    Data is stored as follows: two-leeter ID of day type and day type name.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """
    drop_day_type = """DROP TABLE Day_Type"""

    create_day_type_table = """CREATE TABLE Day_Type(
    DAY_TYPE_ID CHAR(2) NOT NULL CONSTRAINT DAY_TYPE_PK PRIMARY KEY,
    DAY_TYPE_NAME VARCHAR2(35) NOT NULL
    )"""

    cursor.execute(drop_day_type)
    cursor.execute(create_day_type_table)

def insert_day_type_data_into_databse(cursor, day_type_data: DayTypeParsedData) -> None:
    """ Insert data into Day_Type database.

    Args:
        cursor : Cursor holding database connection.
        day_type_data (DayTypeParsedData): Data which will be inserted into Day_Type table in database.
        Data must be generated by get_raw_data_day_type() function.
    """
    cursor.executemany("""INSERT INTO Day_Type VALUES(:1, :2)""", day_type_data)

def create_day_line_table(cursor) -> None:
    """Create table Day_Line, which will hold information about which timetable (day type) will be used by given line on given day.
    Data is stored as follows: numeric ID of row, day, line number and day type which will be used by this line on that day.
    This function will drop previous table, create a new, empty one and add appropriate constraints to this table if needed (in that order).

    Args:
        cursor : Cursor holding database connection.
    """

    drop_day_line = """DROP TABLE DAY_LINE"""

    create_day_line = """CREATE TABLE Day_Line(
    DL_ID NUMBER(5) GENERATED BY DEFAULT ON NULL AS IDENTITY START WITH 1 CONSTRAINT Day_Line_PK PRIMARY KEY,
    Day DATE,
    Line_ID VARCHAR2(4) NOT NULL,
    Day_Type_ID CHAR(2)
    )"""

    alter_day_type_fk = """ALTER TABLE Day_Line
    ADD CONSTRAINT Day_Line_Day_FK FOREIGN KEY (Day_Type_ID) REFERENCES Day_Type(Day_Type_ID)"""

    alter_line_fk = """ALTER TABLE Day_Line
    ADD CONSTRAINT Day_Line_Line_FK FOREIGN KEY (Line_ID) REFERENCES Line(Line_ID)"""

    cursor.execute(drop_day_line)
    cursor.execute(create_day_line)
    cursor.execute(alter_day_type_fk)
    cursor.execute(alter_line_fk)

def insert_day_line_data_into_table(cursor, day_line_data: DayLineParsedData) -> None:
    """Insert Day_Line data into databse.

    Args:
        cursor : Cursor holding database connection.
        day_line_data (DayLineParsedData): Data which will be inserted into Day_Line table in database.
        Data must be generated by get_raw_data_day_line() function.
    """
    cursor.executemany("INSERT INTO Day_Line VALUES(DEFAULT, to_date(:1, 'YYYY-MM-DD'), :2, :3)", day_line_data)

def build_whole_database(cursor, database_file: str) -> None:
    """Generate whole database, by removing old data and tables, creataing new tables, generating new data into database and then inserting new data into new database
    (in that order).

    Args:
        cursor : Cursor holding database connection.
        database_file (str): Address of WTP data file from which data will be used in database. File must be properly formatted: file must be divided into sections
        and must have all required sections of data in it.
    """

    drop_constraints(cursor)

    create_town_table(cursor)
    create_place_table(cursor)
    create_stop_complex_table(cursor)
    create_stop_table(cursor)
    create_line_type_table(cursor)
    create_line_table(cursor)
    create_variant_table(cursor)
    create_day_type_table(cursor)
    create_course_table(cursor)
    create_stop_course_table(cursor)
    create_stop_neighbour_table(cursor)
    create_stop_variant_table(cursor)
    create_day_line_table(cursor)

    create_get_variant_id_by_line_and_var_name_function(cursor)

    with open(database_file, "r", encoding="cp1250") as file_handle:

        working_index = 0

        day_type_data, working_index = get_raw_data_day_type(file_handle, working_index)
        day_line_working_index = working_index

        stop_complex_data, working_index = get_raw_data_stop_complex(file_handle, working_index)

        stop_data, working_index = get_raw_data_stop(file_handle, working_index)

        town_data, working_index = get_raw_data_town(file_handle, working_index)

        variant_data, line_data, _ = get_raw_variant_and_line_data(file_handle, working_index)
        line_data, line_type_data = parse_line_data(line_data)

        lines_list = prepare_line_list(line_data)

        day_line_data, _ = get_raw_data_day_line(file_handle, day_line_working_index, lines_list)

        stop_data, variant_data, place_data = change_stop_and_variant_places(stop_data, variant_data)

        sv_stop_data, sv_variant_data = get_foreign_keys_for_stop_variant(stop_data, variant_data)
        stop_variant_data, _ = get_raw_data_stop_variant(file_handle, sv_stop_data, sv_variant_data, working_index)

        course_data, _ = get_raw_data_course(file_handle, working_index)

        course_dict = get_dict_for_stop_course(course_data)

        stop_course_data, working_index = get_raw_data_stop_course(file_handle, working_index, course_dict, stop_data)

        stop_course_data = reduce_stop_course_data(stop_course_data, course_data, course_dict, lines_list)

        stop_neighbour_data = get_stop_neighbours(stop_data)

        file_handle.close()

    insert_place_data_into_table(cursor, place_data)
    insert_town_data_into_databse(cursor, town_data)
    insert_day_type_data_into_databse(cursor, day_type_data)
    insert_stop_complex_data_into_database(cursor, stop_complex_data)
    insert_stop_data_into_database(cursor, stop_data)
    insert_data_into_line_type_table(cursor, line_type_data)
    insert_data_into_line_table(cursor, line_data)
    insert_variant_data_into_table(cursor, variant_data)
    insert_data_into_stop_neighbour(cursor, stop_neighbour_data)
    insert_data_into_stop_variant(cursor, stop_variant_data)
    insert_data_into_course_table(cursor, course_data)
    insert_stop_course_data_into_table(cursor, stop_course_data)
    insert_day_line_data_into_table(cursor, day_line_data)


    connection.commit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise FileNotGivenError()

    dsn = oracledb.makedsn("ora4.ii.pw.edu.pl", 1521, service_name="pdb1.ii.pw.edu.pl")
    connection = oracledb.connect(user='z14', password="dn7xv3", dsn=dsn)
    cursor = connection.cursor()
    build_whole_database(cursor, sys.argv[1])