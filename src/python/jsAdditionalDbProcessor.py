import sqlite3

id_tso = 600000
user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
agent = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
tso_string = "Text selection offset"

INSERT_QUERY = "insert into logger_log values(?,?,?,?,?,?,?,?);"
FIX_OFFSETS_TO_START_FROM_0_QUERY = "UPDATE logger_log SET referrer = referrer - 1 WHERE action like '%offset' AND referrer > 0;"
GET_ALL_EVENTS_QUERY = "SELECT * FROM logger_log ORDER BY timestamp;"
GET_TAB_TSO_EVENTS_QUERY = "SELECT * FROM logger_log WHERE action ='Part activated' or action = 'Text selection offset' ORDER BY timestamp;"
UPDATE_TSO_QUERY = "UPDATE logger_log SET referrer = ? WHERE `index` = ? AND action = ? and timestamp = ?"

class DB_FIELDS:
    INDEX = 0
    USER=1
    TIMESTAMP = 2
    ACTION=3
    TARGET=4
    REFERRER=5
    AGENT=6
    ELAPSED_TIME=7

class JSAdditionalDbProcessor:

    def __init__(self, db):
        self.db = db

    def fixOffsetsToBeginWith0(self, db):
        conn = sqlite3.connect(db)
        conn.execute(FIX_OFFSETS_TO_START_FROM_0_QUERY);
        conn.commit()
        conn.close()

    def __insertTextSelectionOffsetToDb(self, conn, timestamp, doc_path, time_elapsed):
        global id_tso
        c = conn.cursor()
        c.execute(INSERT_QUERY, (0, user, timestamp, tso_string, doc_path, 0, agent, time_elapsed))
        conn.commit()
        id_tso +=1

    def addMissingTextSelectionOffsetEvents(self, db):
        print "Adding manual TSO..."
        conn = sqlite3.connect(db)
        c = conn.cursor()

        result = c.execute(GET_ALL_EVENTS_QUERY).fetchall();

        i = 0
        open_tabs_list = []
        temp_list = []
        full_list = []

        for row in result:
            if row[DB_FIELDS.ACTION] == "Part activated" and \
                            row[DB_FIELDS.TARGET][-2:]== 'js' and '[B]' not in row[DB_FIELDS.REFERRER]:
                open_tabs_list.append(i)
            i+=1

        i=0
        while (i<len(open_tabs_list)):
            for j in range (open_tabs_list[i], len(result)):
                temp_list.append(result[j])
                if result[j][DB_FIELDS.ACTION] == "Part deactivated":
                    break
            full_list.append(temp_list)
            temp_list = []
            i+=1

        for set_of_rows in full_list:
            has_tso = False
            for row in set_of_rows:
                if(row[DB_FIELDS.ACTION] == "Text selection offset"):
                    has_tso = True
                    break
            if(not(has_tso)):
                part_activated_event = set_of_rows[0]
                self.__insertTextSelectionOffsetToDb(conn, part_activated_event[DB_FIELDS.TIMESTAMP], part_activated_event[DB_FIELDS.REFERRER], part_activated_event[DB_FIELDS.ELAPSED_TIME])
            elif(has_tso):
                continue

        conn.close()

    def __updateTSOForEvent(self, conn, event, offset):
        conn.execute(UPDATE_TSO_QUERY, [offset, event[DB_FIELDS.INDEX], tso_string, event[DB_FIELDS.TIMESTAMP]])

    def fixNavPositionsToPreviousLocationOnFile(self, db):
        text_selection_offsets = {}
        update_TSO_to_prev_offset_in_file = False
        opened_file = None

        conn = sqlite3.connect(db)
        c = conn.cursor()

        events = c.execute(GET_TAB_TSO_EVENTS_QUERY).fetchall();
        # timestamp, action target, referrer
        for event in events:
            if '[B]' in str(event[DB_FIELDS.REFERRER]):
                continue

            elif event[DB_FIELDS.ACTION] == 'Part activated':
                opened_file = event[DB_FIELDS.REFERRER]
                if text_selection_offsets.get(opened_file, None) != None:
                    update_TSO_to_prev_offset_in_file = True
                else:
                    update_TSO_to_prev_offset_in_file = False

            elif event[DB_FIELDS.ACTION] == 'Text selection offset':
                logged_offset = event[DB_FIELDS.REFERRER]
                file = event[DB_FIELDS.TARGET]

                if file == opened_file and logged_offset == '0' and update_TSO_to_prev_offset_in_file == True:
                    self.__updateTSOForEvent(conn, event, text_selection_offsets[file])
                    update_TSO_to_prev_offset_in_file = False
                else:
                    text_selection_offsets[file] = logged_offset

        conn.commit()
        conn.close()

    def process(self):
        print "Fixing offsets"
        self.fixOffsetsToBeginWith0(self.db)

        print "Inserting manual TSO"
        self.addMissingTextSelectionOffsetEvents(self.db)

        print "Fix TSO on closing tabs"
        self.fixNavPositionsToPreviousLocationOnFile(self.db)
