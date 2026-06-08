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
        return result
    except Exception:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def execute_query(fn):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        result = fn(cur)
        return result
    except Exception:
        return []
    finally:
        if conn:
            conn.close()

def print_table(rows):
    for r in rows:
        print(",".join(str(x) if x is not None else "NULL" for x in r))

def parse_bool(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    v = str(val).lower()
    return v == "true" or v == "1"

def out_bool(val):
    print("Success" if val else "Fail")


# operation functions

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
        CREATE TABLE `User` (
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
                    row = [None if x.upper() == "NULL" else x for x in row]
                    if convert:
                        row = convert(row)
                    rows.append(row)
                for r in rows:
                    try:
                        cur.execute(query, r)
                    except Exception:
                        raise Exception("Import failed")

        load("User.csv", "INSERT INTO `User` VALUES (%s,%s,%s,%s)")
        load("Organizer.csv", "INSERT INTO Organizer VALUES (%s,%s,%s)")
        load("Participant.csv", "INSERT INTO Participant VALUES (%s,%s)")
        load("Administrator.csv", "INSERT INTO Administrator VALUES (%s,%s,%s)")
        load("Event.csv", "INSERT INTO Event VALUES (%s,%s,%s,%s,%s)")
        load("Slot.csv", "INSERT INTO Slot VALUES (%s,%s,%s,%s)",
             convert=lambda r: (r[0], r[1], parse_bool(r[2]), r[3]))
        load("Venue.csv", "INSERT INTO Venue VALUES (%s,%s,%s,%s,%s)")
        load("OnCampus.csv", "INSERT INTO OnCampus VALUES (%s,%s)")
        load("OffCampus.csv", "INSERT INTO OffCampus VALUES (%s,%s)")
        load("Hosting.csv", "INSERT INTO Hosting VALUES (%s,%s,%s)",
             convert=lambda r: (r[0], r[1], parse_bool(r[2])))
        load("Approval.csv", "INSERT INTO Approval VALUES (%s,%s,%s,%s)")
        
        return True
    return execute_txn(op)
    
def insertAdmin(uid, email, username, joined, firstname, lastname):
    def op(cur):
        cur.execute("""
            INSERT INTO `User` (uid, email, username, joined)
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

        cur.execute("""
            SELECT 1 FROM Hosting WHERE eid=%s AND vid=%s
        """, (eid, vid))
        if cur.fetchone():
            raise Exception("Duplicate venue")

        if is_primary:
            cur.execute("""
                SELECT 1 FROM Hosting
                WHERE eid=%s AND is_primary=TRUE
            """, (eid,))
            if cur.fetchone():
                raise Exception("Multiple primary venues")

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

        row = cur.fetchone()
        if row is None:
            raise Exception("Slot not found")

        is_slot_reserved = row[0]
        if is_slot_reserved:
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

        row = cur.fetchone()
        if row is None:
            raise Exception("Slot not found")

        is_slot_reserved, reserved_uid = row
        if not is_slot_reserved:
            raise Exception('Slot is not reserved')
        if is_slot_reserved and reserved_uid != uid:
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
    def op(cur):
        cur.execute("""
                    DELETE FROM Organizer
                    WHERE uid = %s
                """, (uid,))
        
        if cur.rowcount == 0:
            raise Exception("Organizer Not Found")
        
        return True
    return execute_txn(op)

def availableEvents(date):
    def op(cur):
        cur.execute("""
                    SELECT e.eid, e.title, e.type, e.datetime, COUNT(*) AS availableSlots
                    FROM Event e
                    JOIN Slot s on e.eid = s.eid
                    WHERE e.datetime > %s
                        AND s.is_reserved = FALSE
                    GROUP BY e.eid, e.title, e.type, e.datetime
                    ORDER BY e.datetime ASC, e.eid ASC
                """, (date,))
        
        return cur.fetchall()
    return execute_query(op)

def popularEventTypes(N):
    def op(cur):
        cur.execute("""
                    SELECT e.type, COUNT(*) AS reservedCount
                    FROM Event e
                    JOIN Slot s on e.eid = s.eid
                    WHERE s.is_reserved = TRUE
                    GROUP BY e.type
                    HAVING COUNT(*) >= %s
                    ORDER BY reservedCount DESC, e.type ASC
                """, (N,))
        
        return cur.fetchall()
    return execute_query(op)

def participantSchedule(uid):
    def op(cur):
        cur.execute("""
            SELECT e.eid, e.title, e.type, e.datetime, r.snum,
                   v.vid, v.street, v.city, v.state, v.zip
            FROM Slot r
            JOIN Event e ON r.eid = e.eid
            LEFT JOIN (
                SELECT h.eid, ve.vid, ve.street, ve.city, ve.state, ve.zip
                FROM Hosting h
                JOIN Venue ve ON h.vid = ve.vid
                WHERE h.is_primary = TRUE
            ) v ON e.eid = v.eid
            WHERE r.uid = %s
                AND r.is_reserved = TRUE
            ORDER BY e.datetime ASC
        """, (uid,))
        return cur.fetchall()
    return execute_query(op)

def organizerStats(N):
    def op(cur):
        cur.execute("""
            SELECT u.uid, u.username, o.department, COUNT(e.eid) AS eventCount
            FROM Organizer o
            JOIN User u ON o.uid = u.uid
            JOIN Event e ON o.uid = e.creator_uid
            GROUP BY o.uid, u.username, o.department
            HAVING COUNT(e.eid) >= %s
            ORDER BY eventCount DESC, o.uid ASC
        """, (N,))
        return cur.fetchall()
    return execute_query(op)

def venueEvents(vid):
    def op(cur):
        cur.execute("""
            SELECT e.eid, e.title, e.type, e.datetime, h.is_primary
            FROM Hosting h
            JOIN Event e ON h.eid = e.eid
            WHERE h.vid = %s
            ORDER BY e.datetime ASC, e.eid ASC
        """, (vid,))
        return cur.fetchall()
    return execute_query(op)


# main setup

def main():
    func = sys.argv[1]
    args = sys.argv[2:]

    if func == "import":
        out_bool(import_data(args[0]))

    elif func == "insertAdmin":
        uid = int(args[0])
        email = args[1]
        username = args[2]
        joined = args[3]
        firstname = args[4]
        lastname = args[5]
        out_bool(insertAdmin(uid, email, username, joined, firstname, lastname))

    elif func == "addVenue":
        eid = int(args[0])
        vid = int(args[1])
        is_primary = parse_bool(args[2])
        out_bool(addVenue(eid, vid, is_primary))
    
    elif func == "reserveSlot":
        eid = int(args[0])
        snum = int(args[1])
        uid = int(args[2])
        out_bool(reserveSlot(eid, snum, uid))
    
    elif func == "cancelReservation":
        eid = int(args[0])
        snum = int(args[1])
        uid = int(args[2])
        out_bool(cancelReservation(eid, snum, uid))
    
    elif func == "updateEvent":
        eid = int(args[0])
        title = args[1]
        datetime = args[2]
        out_bool(updateEvent(eid, title, datetime))
    
    elif func == "deleteOrganizer":
        uid = int(args[0])
        out_bool(deleteOrganizer(uid))
    
    elif func == "availableEvents":
        date = args[0]
        print_table(availableEvents(date))
    
    elif func == "popularEventTypes":
        N = int(args[0])
        print_table(popularEventTypes(N))
    
    elif func == "participantSchedule":
        print_table(participantSchedule(int(args[0])))
    
    elif func == "organizerStats":
        print_table(organizerStats(int(args[0])))
    
    elif func == "venueEvents":
        print_table(venueEvents(int(args[0])))
    
    else:
        print("Unknown function")

if __name__ == "__main__":
    main()