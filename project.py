import sys
import mysql.connector
import csv
import os


# helper functions

def get_conn():
    return mysql.connector.connect(
        user='test',
        password='password',
        database='cs122a'
    )

def execute_txn(fn):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        result = fn(cur)

        conn.commit()
        conn.close()
        return result

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False

def print_table(rows):
    for r in rows:
        print(",".join(str(x) if x is not None else "NULL" for x in r))


def out_bool(val):
    print("Success" if val else "Fail")


# main setup (implement your case(s))

def main():
    func = sys.argv[1]
    args = sys.argv[2:]

    match func:

        case "import":
            out_bool(import_data(args[0]))

        case "insertAdmin":
            uid = int(args[0])
            email = args[1]
            username = args[2]
            joined = args[3]
            firstname = args[4]
            lastname = args[5]
            out_bool(insertAdmin(uid, email, username, joined, firstname, lastname))

        case "addVenue":
            eid = int(args[0])
            vid = int(args[1])
            is_primary = args[2].lower() == "true"
            out_bool(addVenue(eid, vid, is_primary))
        
        case "reserveSlot":
            eid = int(args[0])
            snum = int(args[1])
            uid = int(args[2])
            out_bool(reserveSlot(eid, snum, uid))
        
        case "cancelReservation":
            eid = int(args[0])
            snum = int(args[1])
            uid = int(args[2])
            out_bool(cancelReservation(eid, snum, uid))
        
        case "updateEvent":
            eid = int(args[0])
            title = args[1]
            datetime = args[2]
            out_bool(updateEvent(eid, title, datetime))
        
        case "deleteOrganizer":
            raise NotImplementedError()
        
        case "availableEvents":
            raise NotImplementedError()
        
        case "popularEventTypes":
            raise NotImplementedError()
        
        case "participantSchedule":
            raise NotImplementedError()
        
        case "organizerStats":
            raise NotImplementedError()
        
        case "venueEvents":
            raise NotImplementedError()
        
        case _:
            print("Unknown function")


# command functions

def import_data(folder):
    def op(cur):
        drops = [
            "Hosting", "Approval", "Slot", "Event",
            "OnCampus", "OffCampus", "Venue",
            "Administrator", "Participant",
            "Organizer", "User"
        ]

        for t in drops:
            cur.execute(f"DROP TABLE IF EXISTS {t}")

        cur.execute("""
        CREATE TABLE User (
            uid INT,
            email TEXT NOT NULL,
            username TEXT NOT NULL,
            joined DATE NOT NULL,
            PRIMARY KEY (uid)
        )
        """)

        cur.execute("""
        CREATE TABLE Organizer (
            uid INT,
            department TEXT NOT NULL,
            experience INT NOT NULL,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Participant (
            uid INT,
            type TEXT,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Administrator (
            uid INT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Event (
            eid INT,
            creator_uid INT NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            datetime DATETIME NOT NULL,
            PRIMARY KEY (eid),
            FOREIGN KEY (creator_uid) REFERENCES Organizer(uid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Slot (
            eid INT,
            snum INT NOT NULL,
            is_reserved BOOLEAN NOT NULL,
            uid INT,
            PRIMARY KEY (eid, snum),
            FOREIGN KEY (eid) REFERENCES Event(eid) ON DELETE CASCADE,
            FOREIGN KEY (uid) REFERENCES Participant(uid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Venue (
            vid INT,
            street TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            PRIMARY KEY (vid)
        )
        """)

        cur.execute("""
        CREATE TABLE OnCampus (
            vid INT,
            code TEXT NOT NULL,
            PRIMARY KEY (vid),
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE OffCampus (
            vid INT,
            distance INT NOT NULL,
            PRIMARY KEY (vid),
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Hosting (
            eid INT NOT NULL,
            vid INT NOT NULL,
            is_primary BOOLEAN NOT NULL,
            PRIMARY KEY (eid, vid),
            FOREIGN KEY (eid) REFERENCES Event(eid) ON DELETE CASCADE,
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE Approval (
            uid INT NOT NULL,
            vid INT NOT NULL,
            valid_from DATE NOT NULL,
            valid_until DATE NOT NULL,
            PRIMARY KEY (uid, vid),
            FOREIGN KEY (uid) REFERENCES Administrator(uid) ON DELETE CASCADE,
            FOREIGN KEY (vid) REFERENCES OffCampus(vid) ON DELETE CASCADE
        )
        """)

        def load(file, query, convert=None):
            path = os.path.join(folder, file)
            with open(path, newline='') as f:
                reader = csv.reader(f)
                rows = []
                for row in reader:
                    row = [None if x == "NULL" else x for x in row]
                    if convert:
                        row = convert(row)
                    rows.append(row)
                cur.executemany(query, rows)

        def standardize_bool(row, idx):
            if row[idx].lower() == "true":
                row[idx] = 1
            elif row[idx].lower() == "false":
                row[idx] = 0
            return row

        load("User.csv", "INSERT INTO User VALUES (%s,%s,%s,%s)")
        load("Organizer.csv", "INSERT INTO Organizer VALUES (%s,%s,%s)")
        load("Participant.csv", "INSERT INTO Participant VALUES (%s,%s)")
        load("Administrator.csv", "INSERT INTO Administrator VALUES (%s,%s,%s)")
        load("Event.csv", "INSERT INTO Event VALUES (%s,%s,%s,%s,%s)")
        load("Slot.csv", "INSERT INTO Slot VALUES (%s,%s,%s,%s)",
             convert=lambda r: standardize_bool(r, 2))
        load("Venue.csv", "INSERT INTO Venue VALUES (%s,%s,%s,%s,%s)")
        load("OnCampus.csv", "INSERT INTO OnCampus VALUES (%s,%s)")
        load("OffCampus.csv", "INSERT INTO OffCampus VALUES (%s,%s)")
        load("Hosting.csv", "INSERT INTO Hosting VALUES (%s,%s,%s)",
             convert=lambda r: standardize_bool(r, 2))
        load("Approval.csv", "INSERT INTO Approval VALUES (%s,%s,%s,%s)")
        
        return True
    return execute_txn(op)
    
def insertAdmin(uid, email, username, joined, firstname, lastname):
    def op(cur):
        cur.execute("""
            INSERT INTO User (uid, email, username, joined)
            VALUES (%s, %s, %s, %s)
        """, (uid, email, username, joined))

        cur.execute("""
            INSERT INTO Administrator (uid, firstname, lastname)
            VALUES (%s, %s, %s)
        """, (uid, firstname, lastname))

        return True
    return execute_txn(op)

def addVenue(eid, vid, is_primary):
    def op(cur):
        if is_primary:
            cur.execute("""
                SELECT COUNT(*)
                FROM Hosting
                WHERE eid = %s AND is_primary = TRUE
            """, (eid,))

            primary_count = cur.fetchone()[0]
            if primary_count > 0:
                raise Exception("Primary already exists")

        cur.execute("""
            INSERT INTO Hosting (eid, vid, is_primary)
            VALUES (%s, %s, %s)
        """, (eid, vid, is_primary))

        return True
    return execute_txn(op)

def reserveSlot(eid, snum, uid):
    def op(cur):
        cur.execute("""
            SELECT is_reserved
            FROM Slot
            WHERE eid = %s AND snum = %s
        """, (eid, snum))

        is_slot_reserved = cur.fetchone()[0]
        if is_slot_reserved == 1:
            raise Exception('Slot is already reserved')

        cur.execute("""
            UPDATE Slot
            SET is_reserved = TRUE, uid = %s
            WHERE eid = %s AND snum = %s
        """, (uid, eid, snum))

        return True
    return execute_txn(op)

def cancelReservation(eid, snum, uid):
    def op(cur):
        cur.execute("""
            SELECT is_reserved, uid
            FROM Slot
            WHERE eid = %s AND snum = %s
        """, (eid, snum))

        is_slot_reserved, reserved_uid = cur.fetchone()
        if is_slot_reserved == 0:
            raise Exception('Slot is not reserved')
        if is_slot_reserved == 1 and reserved_uid != uid:
            raise Exception('Slot is reserved to a different user')

        cur.execute("""
            UPDATE Slot
            SET is_reserved = FALSE, uid = NULL
            WHERE eid = %s AND snum = %s
        """, (eid, snum))

        return True
    return execute_txn(op)

def updateEvent(eid, title, datetime):
    def op(cur):
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM Event
                WHERE eid = %s
            )
        """, (eid, ))

        is_id_valid = cur.fetchone()[0]
        if is_id_valid == 0:
            raise Exception('Event ID does not exist')

        cur.execute("""
            UPDATE Event
            SET title = %s, datetime = %s
            WHERE eid = %s
        """, (title, datetime, eid))

        return True
    return execute_txn(op)

def deleteOrganizer(uid):
    raise NotImplementedError()

def availableEvents(date):
    raise NotImplementedError()

def popularEventTypes(N):
    raise NotImplementedError()

def participantSchedule(uid):
    raise NotImplementedError()

def organizerStats(N):
    raise NotImplementedError()

def venueEvents(vid):
    raise NotImplementedError()

if __name__ == "__main__":
    main()