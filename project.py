import sys
import mysql.connector
import csv
import os


# utility helper functions

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
    except mysql.connector.Error:
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def print_table(rows):
    for r in rows:
        print(",".join(str(x) if x is not None else "NULL" for x in r))

def parse_bool(val):
    return  {"true": True, "false": False}[val.lower()]

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

        load("User.csv", "INSERT INTO User VALUES (%s,%s,%s,%s)")
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
                return False

        cur.execute("""
            INSERT INTO Hosting (eid, vid, is_primary)
            VALUES (%s, %s, %s)
        """, (eid, vid, is_primary))

        return True
    return execute_txn(op)

def reserveSlot(eid, snum, uid):
    raise NotImplementedError()

def cancelReservation(eid, snum, uid):
    raise NotImplementedError()

def updateEvent(eid, title, datetime):
    raise NotImplementedError()

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
        raise NotImplementedError()
    
    elif func == "cancelReservation":
        raise NotImplementedError()
    
    elif func == "updateEvent":
        raise NotImplementedError()
    
    elif func == "deleteOrganizer":
        raise NotImplementedError()
    
    elif func == "availableEvents":
        raise NotImplementedError()
    
    elif func == "popularEventTypes":
        raise NotImplementedError()
    
    elif func == "participantSchedule":
        raise NotImplementedError()
    
    elif func == "organizerStats":
        raise NotImplementedError()
    
    elif func == "venueEvents":
        raise NotImplementedError()
    
    else:
        print("Unknown function")

if __name__ == "__main__":
    main()