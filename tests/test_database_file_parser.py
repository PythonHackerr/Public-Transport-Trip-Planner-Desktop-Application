from src.core.database_file_parser import *
import pytest
import io
import os


def test_get_raw_lines_of_handle(monkeypatch):
    mock_file = io.StringIO("""
    *TE
    Line1
    Line2
    #TE
    *ST
    Line3
    Line4
    Line5
    #ST
    """)
    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
    def mock_size(a):
        return mock()

    monkeypatch.setattr('os.stat', mock_size)

    lines_te, new_index = get_raw_lines_of_handle("TE", mock_file, 0)
    assert(len(lines_te) == 2)
    assert(new_index == 37)

    no_lines = get_raw_lines_of_handle("TT", mock_file, 0)
    assert(not no_lines)

    lines_st, new_index =  get_raw_lines_of_handle("ST", mock_file, new_index)

    assert(len(lines_st) == 3)
    assert(new_index == 83)

    lines_st2 = get_raw_lines_of_handle("ST", mock_file, new_index)
    assert(not lines_st2)

    with pytest.raises(WorkingIndexOutOfRange):
        _ = get_raw_lines_of_handle("ST", mock_file, 137)

def test_get_raw_lines_of_text():
    mock_file =[
    "*TE",
    "Line1",
    "Line2",
    "#TE",
    "*ST",
    "Line3",
    "Line4",
    "Line5",
    "#ST"
    ]

    lines_te, new_index = get_raw_lines_of_text("TE", mock_file, start_index=0)
    assert(len(lines_te) == 2)
    assert(new_index == 3)

    no_lines = get_raw_lines_of_text("TT", mock_file, start_index=0)
    assert(not no_lines)

    lines_st, new_index =  get_raw_lines_of_text("ST", mock_file, start_index=new_index)

    assert(len(lines_st) == 3)
    assert(new_index == 8)

    lines_st2 = get_raw_lines_of_text("ST", mock_file, start_index=new_index)
    assert(not lines_st2)

    with pytest.raises(WorkingIndexOutOfRange):
        _ = get_raw_lines_of_text("ST", mock_file, start_index=9)


def test_raw_data_stop_complex(monkeypatch):
    mock_file = io.StringIO("""
*ZA 5
   4009   1 Sierpnia,                         --  WARSZAWA
   2293   1.Praskiego Pułku,                  --  WARSZAWA
   1076   11 Listopada,                       --  WARSZAWA
   1710   11 Listopada,                       KB  KOBYŁKA
   6658   11 Listopada,                       ŁM  ŁOMIANKI
#ZA
   1192   3 Maja,                             LG  LEGIONOWO
   """)
    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    stop_complex_data, _ = get_raw_data_stop_complex(mock_file, 0)
    assert(len(stop_complex_data) == 5)
    assert(len(stop_complex_data[0]) == 3)
    assert(stop_complex_data[0] == [4009, '1 Sierpnia', '--'])
    assert([6658, '11 Listopada', 'ŁM'] in stop_complex_data)
    assert([1192, '3 Maja', 'LG'] not in stop_complex_data)

    empty_mock_file = io.StringIO("""
   4009   1 Sierpnia,                         --  WARSZAWA
   2293   1.Praskiego Pułku,                  --  WARSZAWA
   1076   11 Listopada,                       --  WARSZAWA
   1710   11 Listopada,                       KB  KOBYŁKA
   6658   11 Listopada,                       ŁM  ŁOMIANKI
   """)
    empty_mock_file.name = ""
    with pytest.raises(SectionNotFoundError):
        get_raw_data_stop(empty_mock_file, 0)

    test_not_int = io.StringIO("""
*ZA 5
   A023   Młociny,                         --  WARSZAWA
#ZA
   """)
    test_not_int.name = ""
    with pytest.raises(NumericTypeExpectedError):
        get_raw_data_stop_complex(test_not_int, 0)

def test_get_raw_data_stop(monkeypatch):
    mock_file = io.StringIO("""
*ZP
    6057   Sokratesa,                       --  WARSZAWA
      *PR  4
         605701   2      Ul./Pl.: Sokratesa,                        Kier.: Wólczyńska,                       Y= 52.288374     X= 20.932843     Pu=0
            L  6  - stały:              114   121   203   210   250   712
            L  4  - na żądanie:         N01   N02   N41   N58
         605702   2      Ul./Pl.: Przy Agorze,                      Kier.: Wrzeciono,                        Y= 52.289577     X= 20.934647     Pu=0
            L  3  - stały:              103   121   303
            L  2  - na żądanie:         N41   N46
         605703   2      Ul./Pl.: Kasprowicza,                      Kier.: Metro Wawrzyszew,                 Y= 52.288540     X= 20.934157     Pu=0
            L  3  - stały:              156   184   303
            L  1  - na żądanie:         N44
         605704   2      Ul./Pl.: Kasprowicza,                      Kier.: Metro Młociny,                    Y= 52.289517     X= 20.933182     Pu=0
            L  9  - stały:              103   114   156   184   203   210   250   712   850
            L  6  - na żądanie:         N01   N02   N41^  N44   N46   N58
      #PR
   6058   Nocznickiego,                    --  WARSZAWA
      *PR  2
         605801   1      Ul./Pl.: Nocznickiego,                     Kier.: Popiela,                          Y= 52.284872     X= 20.922982     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
         605802   1      Ul./Pl.: Nocznickiego,                     Kier.: Metro Młociny,                    Y= 52.284735     X= 20.922889     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
      #PR
#ZP""")

    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    stop_data, _ = get_raw_data_stop(mock_file, 0)
    assert(len(stop_data) == 6)
    assert(stop_data[0] == [605701, '01', 6057, 52.288374, 20.932843, "Sokratesa", "Wólczyńska"])
    assert(stop_data[5] == [605802, '02', 6058, 52.284735, 20.922889, "Nocznickiego", "Metro Młociny"])

    test_lack_of_data = io.StringIO("""
*ZP
    1067   Konopacka,                       --  WARSZAWA
      *PR  4
         106701   2      Ul./Pl.: Stalowa,                          Kier.: Inżynierska,                      Y= 52.259464     X= 21.039320     Pu=0
            L  2  - stały:               23   135
            L  3  - na żądanie:         N03   N14   N64
         106702   2      Ul./Pl.: Stalowa,                          Kier.: Środkowa,                         Y= 52.259611     X= 21.039768     Pu=0
            L  1  - stały:               23
            L  2  - na żądanie:         N03   N14
         106781   1      Ul./Pl.: Stalowa,                          Kier.: ************                      Y=yyy.yyyyyyyy   X=xxx.xxxxxxxx   Pu=?
            L  2  - na żądanie:         N14   N64
         106782   1      Ul./Pl.: Stalowa,                          Kier.: *********                         Y=yyy.yyyyyyyy   X=xxx.xxxxxxxx   Pu=?
            L  1  - na  żądanie:         N64
      #PR
#ZP
    """)
    test_lack_of_data.name = ""
    stop_lack_data, _ = get_raw_data_stop(test_lack_of_data, 0)

    assert(len(stop_lack_data) == 4)
    assert(not stop_lack_data[3][3])
    assert(not stop_lack_data[3][4])
    assert(not stop_lack_data[3][6])

def test_get_raw_varint_and_line_data(monkeypatch):
    mock_file = io.StringIO("""
*LL 332
   Linia:   1  - LINIA TRAMWAJOWA
      *TR  5
         TP-ANN  ,       Banacha,                        --  ==>  Annopol,                        --       Kier. A   Poz. 0
            *LW  30
            #LW
      #TR
      *TR
         TP-MMLB ,       Tarchomin Kościelny,            --  ==>  Metro Młociny,                  --       Kier. A   Poz. 1
            *LW  30
            #LW
      #TR
      *WK 12604
         TD-4TAKB/DP/06.09  606105 DP  6.10
         TD-4TAKB/DP/06.09  146904 DP  6.13
         TD-4TAKB/DP/06.09  112204 DP  6.14
         TD-4TAKB/DP/06.09  152102 DP  6.15
      #WK
#LL

    """)

    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    raw_variants, raw_lines, _ = get_raw_variant_and_line_data(mock_file, 0)

    assert(len(raw_variants) == 3)
    assert(raw_variants[0] == ['1', 'TP-ANN', 'A', 0, 'Annopol',1])
    assert(raw_variants[2] == ['1', 'TD-4TAKB', None, None, None, 0])

    assert(len(raw_lines) == 1)
    assert(raw_lines[0] == ['1', 'LINIA TRAMWAJOWA'])

def test_get_previous_line_with():
    test_text = [
    "Linia",
    "Metro",
    "Młociny"]
    index = len(test_text) - 1

    num = get_previous_line_with("Lin", test_text, index-1)
    assert(num == 'Linia')

    data_after = get_previous_line_with('Młociny', test_text , 1)
    assert(not data_after)

    not_in = get_previous_line_with('Wawrzyszew', test_text, index-1)
    assert(not not_in)


def test_raw_data_stop_course(monkeypatch):
    mock_text = io.StringIO("""
*LL 332
    Linia: 1
      *WK 12604
         TD-4TAKB/DP/06.09  606105 DP  0.10
         TD-4TAKB/DP/06.09  146904 DP  6.13
         TD-4TAKB/DP/06.09  112204 DP  6.14
         TD-4TAKB/DP/06.09  152102 DP  6.15
      #WK
    Linia: L10
      *WK
         TZ-TAK4B/DP/18.07  150701 DP 18.00
         TZ-TAK4B/DP/18.07  119505 DP 18.08
         TZ-TAK4B/DP/18.07  127705 DP 18.09
         TZ-TAK4B/DP/18.07  125605 DP 18.11
      #WK
#LL

    """)

    mock_stop_file = io.StringIO("""
*ZP
    6057   Sokratesa,                       --  WARSZAWA
      *PR  4
         606105   2      Ul./Pl.: Sokratesa,                        Kier.: Wólczyńska,                       Y= 52.288374     X= 20.932843     Pu=0
            L  6  - stały:              114   121   203   210   250   712
            L  4  - na żądanie:         N01   N02   N41   N58
         150701   2      Ul./Pl.: Przy Agorze,                      Kier.: Wrzeciono,                        Y= 52.289577     X= 20.934647     Pu=0
            L  3  - stały:              103   121   303
            L  2  - na żądanie:         N41   N46
         119505   2      Ul./Pl.: Kasprowicza,                      Kier.: Metro Wawrzyszew,                 Y= 52.288540     X= 20.934157     Pu=0
            L  3  - stały:              156   184   303
            L  1  - na żądanie:         N44
         125605   2      Ul./Pl.: Kasprowicza,                      Kier.: Metro Młociny,                    Y= 52.289517     X= 20.933182     Pu=0
            L  9  - stały:              103   114   156   184   203   210   250   712   850
            L  6  - na żądanie:         N01   N02   N41^  N44   N46   N58
      #PR
   6058   Nocznickiego,                    --  WARSZAWA
      *PR  2
         127705   1      Ul./Pl.: Nocznickiego,                     Kier.: Popiela,                          Y= 52.284872     X= 20.922982     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
         146904   1      Ul./Pl.: Nocznickiego,                     Kier.: Metro Młociny,                    Y= 52.284735     X= 20.922889     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
      #PR
    1234   Nieistniejąca,                    --  WARSZAWA
      *PR  2
         112204   1      Ul./Pl.: Nocznickiego,                     Kier.: Popiela,                          Y= 52.284872     X= 20.922982     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
         152102   1      Ul./Pl.: Nocznickiego,                     Kier.: Metro Młociny,                    Y= 52.284735     X= 20.922889     Pu=0
            L  8  - stały:               22^   23^   24^   26    28^   33    35^   78^
      #PR
#ZP""")

    course_dict = {('1', 'TD-4TAKB/DP/06.09'): 1,
                   ('L10','TZ-TAK4B/DP/18.07'): 2}

    mock_text.name = ""
    mock_stop_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)


    stop_raw_data, _ = get_raw_data_stop(mock_stop_file, 0)
    stop_course, _ = get_raw_data_stop_course(mock_text, 0, course_dict, stop_raw_data)

    assert(len(stop_course) == 8)
    assert(stop_course[0] == [1, 606105, 10, 20960])
    assert(stop_course[4] == [2, 150701, 1080, 20979])

def test_stop_neighbour():
    stop_parsed_data = [
        [100101, '01', 1001, 10, 10],
        [100102, '02', 1001, 10.0001, 10.0001],
        [100103, '03', 1001, 10.0002, 10.0002],
        [100104, '04', 1001, 10.0003, 10.0003],
        [100105, '05', 1001, 10.0004, 10.0004],
        [100106, '06', 1001, 10.0005, 10.0005],
        [100107, '07', 1001, 10.0006, 10.0006],
        [100108, '08', 1001, 11, 11]
    ]
    neighbours = get_stop_neighbours(stop_parsed_data)
    assert(len(neighbours) == 47)
    assert((100101, 100102, 15.60697) in neighbours)
    only_stops = [[row[0], row[1]] for row in neighbours]
    assert ([100108, 100101] not in only_stops)
    assert ([100108, 100103] in only_stops)
    count_stops = [row[0] for row in neighbours]
    assert(count_stops.count(100101) == 6)
    assert(count_stops.count(100108) == 5)

def test_get_raw_data_stop_variant(monkeypatch):
    mock_file = io.StringIO("""
*LL 332
   Linia:   1  - LINIA TRAMWAJOWA
      *TR  5
         TP-ANN  ,       Banacha,                        --  ==>  Annopol,                        --       Kier. A   Poz. 0
            *LW
               Grochowska,                     r 201404  Gocławek,                       -- 04      | 0| 0|
                                               r 201407  Gocławek,                       -- 07      | 0| 0|
                                               r 201303  Kwatery Głównej,                -- 03      | 1| 1|
                                               r 201203  Żółkiewskiego,                  -- 03      | 2| 2|
                                               r 201103  pl.Szembeka,                    -- 03      | 3| 3|
                                               r 201003  Wspólna Droga,                  -- 03      | 4| 4|
                                               r 200901  Czapelska,                      -- 01      | 5| 5|
            #LW
      #TR
      *TR
         TP-MMLB ,       Tarchomin Kościelny,            --  ==>  Metro Młociny,                  --       Kier. A   Poz. 1
            *LW
               ====== S T R E F A   2 =======                                                       |  |  |
               --------- LEGIONOWO ----------                                                       |  |  |
               Olszankowa,                     r 120801  os.Młodych,                     LG 01      | 0| 0|
               Suwalna,                        r 126401  Orzechowa,                      LG 01  NŻ  | 1| 1|
               Cynkowa,                                                                             |  |  |
               al.Legionów,                    r 137701  Cynkowa,                        LG 01  NŻ  | 2| 3|
                                               r 126301  Cmentarz,                       LG 01  NŻ  | 3| 4|
                                               r 137601  Bandurskiego,                   LG 01  NŻ  | 4| 5|
                                               r 137501  PKP Legionowo Piaski,           LG 01      | 5| 6|
               Piaskowa,                       r 137401  Piaskowa,                       LG 01  NŻ  | 6| 7|
            #LW
      #TR
      *WK 12604
         TD-4TAKB/DP/06.09  606105 DP  6.10
         TD-4TAKB/DP/06.09  146904 DP  6.13
         TD-4TAKB/DP/06.09  112204 DP  6.14
         TD-4TAKB/DP/06.09  152102 DP  6.15
         TD-4TAKB/DP/07.15  152103 DP  6.20
      #WK
#LL

    """)

    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    stops_list = [201404,201407,201303,201203,201103,201003,200901,120801,
                  126401,137701,126301,137601,137501,606105,146904,152102,152103]

    special_variants_list = [('1', 'TD-4TAKB')]

    stop_variant, _ = get_raw_data_stop_variant(mock_file, stops_list, special_variants_list, 0)

    assert(len(stop_variant) == 16)
    assert(stop_variant[0] == ['1', 'TP-ANN', 1, 201404, 0, 1])
    assert(['1', "TP-MMLB", 1, 120801, 0, 2] in stop_variant)
    assert(['1', "TP-MMLB", 2, 126401, 1, 2] in stop_variant)
    used_stops_id = [line[3] for line in stop_variant]
    assert(137401 not in used_stops_id)
    assert(112204 not in used_stops_id)
    assert(152103 not in used_stops_id)


def test_get_foreign_keys_for_stop_variant():
    variants = [['1', 'TP-ANN', 'A', 0, 'Annopol',1],
    ['1', 'TD-4TAKB', None, None, None, 0]]
    stops = [[605701, '01', 6057, 52.288374, 20.932843, "Sokratesa", "Wólczyńska"],
             [605802, '02', 6058, 52.284735, 20.922889, "Nocznickiego", "Metro Młociny"]]

    sv_stop, sv_variant = get_foreign_keys_for_stop_variant(stops, variants)

    assert(len(sv_stop) == 2)
    assert(sv_stop == [605701, 605802])

    assert(len(sv_variant) == 1)
    assert(sv_variant == [('1', 'TD-4TAKB')])

def test_get_raw_data_course(monkeypatch):
    mock_file = io.StringIO("""
*LL 332
   Linia:  1
      *WK 12604
         TD-4TAKB/DP/06.09  606105 DP  0.10
         TD-4TAKB/DP/06.09  146904 DP  6.13
         TD-4TAKB/DP/06.12  112204 DP  6.14
         TD-4TAKB/DP/06.12  152102 DP  6.15
      #WK
   Linia: L10
      *WK
         TZ-TAK4B/DP/18.07  150701 DP 18.00
         TZ-TAK4B/DP/18.07  119505 DP 18.08
         TZ-TAK4B/DP/18.03  127705 DP 18.09
         TZ-TAK4B/DP/18.03  125605 DP 18.11
      #WK
#LL
    """)


    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    courses, _ = get_raw_data_course(mock_file, 0)
    assert(len(courses) == 4)
    assert(courses[0] == ['1', 'TD-4TAKB', 'DP', 369] or courses[0] == ['1', 'TD-4TAKB', 'DP', 372])
    assert(courses[2] == ['L10', 'TZ-TAK4B', 'DP', 1087] or courses[2] == ['L10', 'TZ-TAK4B', 'DP', 1083])

def test_get_dict_for_stop_course():
    raw_course_data = [['1', 'TD-4TAKB', 'DP', 369], ['L10', 'TZ-TAK4B', 'DP', 1087]]
    course_dict = get_dict_for_stop_course(raw_course_data)

    assert(course_dict['1', 'TD-4TAKB/DP/06.09'] == 1)
    assert(course_dict['L10', 'TZ-TAK4B/DP/18.07'] == 2)

def test_time_str_to_int():
    assert(time_str_to_int('10.10') == 610)
    assert(time_str_to_int('02.02') == 122)

def test_time_int_to_str():
    assert(time_int_to_str(610) == '10.10')
    assert(time_int_to_str(130) == '02.10')
    assert(time_int_to_str(122) == '02.02')

def test_change_stop_and_variant_places():
    stop_data = [[605701, '01', 6057, 52.288374, 20.932843, "Sokratesa", "Metro Młociny"],
    [605802, '02', 6058, 52.284735, 20.922889, "Nocznickiego", "Metro Młociny"]]
    variant_data = [['1', 'TP-ANN', 'A', 0, 'Annopol',1],
                    ['1', 'TD-4TAKB', None, None, None, 0]]

    new_stop_data, new_variant_data, places = change_stop_and_variant_places(stop_data, variant_data)
    assert (len( places) == 4)
    raw_places = [place[1] for place in places]
    assert("Nocznickiego" in raw_places)
    assert(None not in raw_places)

    def pseudo_dict(table, place):
        for line in table:
            if line[1] == place:
                return line[0]

    assert(new_stop_data[0][5] == pseudo_dict(places, 'Sokratesa'))
    assert(new_variant_data[0][4] == pseudo_dict(places, 'Annopol'))
    assert(not new_variant_data[1][4])

def test_parse_line_data():
    raw_lines =[
    ['1', 'LINIA TRAMWAJOWA'],
    ['M1', 'LINIA METRA'],
    ['M2', 'LINIA METRA']]

    new_line, new_line_type = parse_line_data(raw_lines)

    expected_new_line = [
    ['1', 1],
    ['M1', 2],
    ['M2', 2]]
    assert(new_line == expected_new_line)
    expected_new_line_type = [
    (1, 'LINIA TRAMWAJOWA'),
    (2, 'LINIA METRA')]
    assert(new_line_type == expected_new_line_type)

def test_create_dict_of_object_index():
    table = ['Ala', 'ma', "kota", 'Ala']
    unordered_dict = create_dict_of_object_index(table, ordered=False)

    assert(len(unordered_dict.keys()) == 3)
    assert(unordered_dict['Ala'])
    assert(unordered_dict['kota'])

    ordered_dict = create_dict_of_object_index(table, ordered=True)
    assert(len(ordered_dict.keys()) == 3)
    assert(ordered_dict['Ala']  == 1)
    assert(ordered_dict['kota'] == 3)

def test_replace_object_in_list_with_index():
    test_table = [['A', 'B'],['C', 'A']]
    test_dict = {'A': 1, 'B': 2, 'C': 3}
    new_table = replace_object_in_list_with_index(test_table, test_dict, [0])
    expected_result = [[1, 'B'],[3, 'A']]
    assert(new_table == expected_result)

def test_dict_of_indexes_to_list():
    dict_to_change = {'A': 1, 'B': 2, 'C': 3}
    table =dict_of_indexes_to_list(dict_to_change)
    expected_result = [(1,'A'),(2,'B'),(3,'C')]
    assert(table == expected_result)

def test_raw_data_town(monkeypatch):
    mock_file = io.StringIO("""
*SM 337
   AL   ALEKSANDRÓW
   AN   ANTONINÓW
   AU   AUGUSTÓWEK
   B2   BOŻA WOLA
   BA   BASZKÓWKA
   BB   BIAŁOBRZEGI
   BC   BANIOCHA
   BD   BORZĘCIN DUŻY
   BE   BRZEZINY
   BG   BOGATKI
   BI   BIELAWA
#SM
""")


    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    towns, _ = get_raw_data_town(mock_file, 0)
    assert(len(towns) == 12)
    assert(towns[0] == ['--', 'WARSZAWA'])
    assert(towns[1] == ['AL', 'ALEKSANDRÓW'])
    assert(towns[11] == ['BI', 'BIELAWA'])

def test_raw_data_day_type(monkeypatch):
    mock_file = io.StringIO("""
*TY  33
   D1   PONIEDZIAŁEK
   D2   WTOREK
   D3   ŚRODA
   D4   CZWARTEK
   D5   PIĄTEK
   D6   SOBOTA
   D7   NIEDZIELA
#TY
    """)


    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    day_type, _ = get_raw_data_day_type(mock_file, 0)
    assert(len(day_type) == 7)
    assert(day_type[0] == ['D1', 'PONIEDZIAŁEK'])
    assert(day_type[6] == ['D7', 'NIEDZIELA'])

def test_get_raw_data_day_line(monkeypatch):
    mock_file = io.StringIO("""
*KD   2
   2023-01-07  5
        1   SB
        2   SB
        3   SB
        4   SB
        6   SB
   2023-01-02  5
        1   NI
        2   SB
        3   NI
        4   NI
        7   NI
#KD
    """)


    mock_file.name = ""
    class mock:
        def __init__(self) -> None:
            self.st_size = 100
            self.name = ""
    def mock_size(a):
        return mock()
    monkeypatch.setattr('os.stat', mock_size)

    lines_list = ['1','2','3','4','5','6','7']
    day_line, _ = get_raw_data_day_line(mock_file, 0, lines_list)
    assert(len(day_line) == 14)
    assert(['2023-01-07', '1', 'SB'] in day_line)
    assert(['2023-01-02', '1', 'NI'] in day_line)
    assert(['2023-01-02', '5', None] in day_line)
    assert(['2023-01-07', '7', None] in day_line)

def test_prepare_line_list():
    raw_line_list = [['1', 'LINIA TRAMWAJOWA'], ['L10', 'LINIA STREFOWA UZUPEŁNIAJĄCA']]
    line_list = prepare_line_list(raw_line_list)
    expected_result = ['1', 'L10']
    assert(line_list == expected_result)

def test_reduce_stop_course_data():
    stop_course_data = [[1, 606105, 10], [2, 150701, 1080], [3, 123401, 400]]
    course_data = [['1', 'TP-TPTP', 'DP', 1000], ['1', 'TP-TPTP', 'DP', 200], ['1', 'TP-TPTP', 'DS', 10]]
    course_dict = {('1', 'TP-TPTP/DP/16.40_'):1, ('1', 'TP-TPTP/DP/03.20_'):2,('1','TP-TPTP/SB/00.10_'): 3}
    lines_list = ['1']
    new_stop_course_data = reduce_stop_course_data(stop_course_data, course_data, course_dict, lines_list)
    expected_result = [[1, 606105, 10], [2, 150701, 1080]]
    assert(new_stop_course_data == expected_result)

def test_if_var_is_integer():
    assert(not check_if_var_is_integer('0'))
    with pytest.raises(NumericTypeExpectedError):
        check_if_var_is_integer('Ala')
    with pytest.raises(NumericTypeExpectedError):
        check_if_var_is_integer('1.234')
