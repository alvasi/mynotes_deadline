from flask import Flask, jsonify, request
import psycopg2 as psycopg
import os
from datetime import date

app = Flask(__name__)

# SQL
DB_HOST = "db.doc.ic.ac.uk"
DB_USER = "wss119"
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = "5432"

# SQL USER
DB_USER_2 = "sf23"
DB_PASSWORD_2 = os.environ.get("DB_PASSWORD_2")


def get_db_connection():
    server_params = {
        "dbname": DB_USER,
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "client_encoding": "utf-8",
    }
    return psycopg.connect(**server_params)


def get_user_db_connection():
    server_params = {
        "dbname": DB_USER_2,
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER_2,
        "password": DB_PASSWORD_2,
        "client_encoding": "utf-8",
    }
    return psycopg.connect(**server_params)


@app.route("/all_deadlines", methods=["GET"])
def get_all_deadlines():
    username = request.args.get("username")
    user_deadlines = {"entries": []}
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM deadlines WHERE userid = %s", (username,))
            records = cursor.fetchall()
            print(records)
            for record in records:
                record_dict = {
                    "id": record[0],
                    "task": record[2],
                    "date": record[3].strftime("%d/%m/%Y"),
                    "completed": record[4],
                }
                user_deadlines["entries"].append(record_dict)
        except (Exception, psycopg.Error) as error:
            print("Error retrieving deadlines: ", error)
        finally:
            connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500
    return jsonify(user_deadlines)


@app.route("/past_deadlines", methods=["GET"])
def get_past_deadlines():
    today = date.today()
    username = request.args.get("username")
    past_deadlines = {"entries": []}
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Select deadlines before today
            cursor.execute(
                "SELECT * FROM deadlines WHERE userid = %s AND (deadline < %s OR completed = 'true') ORDER BY deadline DESC",
                (
                    username,
                    today,
                ),
            )
            records = cursor.fetchall()
            for record in records:
                record_dict = {
                    "id": record[0],
                    "task": record[2],
                    "date": record[3].strftime("%d/%m/%Y"),
                    "completed": record[4],
                }
                past_deadlines["entries"].append(record_dict)
        except (Exception, psycopg.Error) as error:
            print("Error retrieving past deadlines: ", error)
        finally:
            connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500
    return jsonify(past_deadlines)


@app.route("/current_deadlines", methods=["GET"])
def get_current_deadlines():
    today = date.today()
    username = request.args.get("username")
    current_deadlines = {"entries": []}
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Select deadlines on today's date or in the future
            cursor.execute(
                "SELECT * FROM deadlines WHERE userid = %s AND deadline >= %s AND completed = 'false' ORDER BY deadline ASC",
                (
                    username,
                    today,
                ),
            )
            records = cursor.fetchall()
            for record in records:
                record_dict = {
                    "id": record[0],
                    "task": record[2],
                    "date": record[3].strftime("%d/%m/%Y"),
                    "completed": record[4],
                }
                current_deadlines["entries"].append(record_dict)
        except (Exception, psycopg.Error) as error:
            print("Error retrieving current deadlines: ", error)
        finally:
            connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500
    return jsonify(current_deadlines)


@app.route("/add_deadline", methods=["POST"])
def add_deadline():
    data = request.get_json()
    username = data.get("username")
    task = data.get("task")
    deadline = data.get("deadline")

    if not all([username, task, deadline]):
        return jsonify("Missing data"), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            insert_sql = "INSERT INTO deadlines (userid, task, deadline, completed) VALUES (%s, %s, %s, 'false')"
            cursor.execute(insert_sql, (username, task, deadline))
            connection.commit()
            return jsonify("Deadline added successfully"), 201
        except (Exception, psycopg.Error) as error:
            print("Error while inserting data into PostgreSQL", error)
            return jsonify("Failed to add deadline"), 500
        finally:
            if connection is not None:
                connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500


@app.route("/delete_deadline", methods=["POST"])
def delete_deadline():
    data = request.get_json()
    deadline_id = data.get("id")

    if not deadline_id:
        return jsonify("Missing deadline ID"), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            update_sql = "DELETE FROM deadlines WHERE id = %s"
            cursor.execute(update_sql, (deadline_id,))
            connection.commit()
            return jsonify("Deadline deleted"), 200
        except (Exception, psycopg.Error) as error:
            print("Error while updating deadline in PostgreSQL", error)
            return jsonify("Failed to delete deadline"), 500
        finally:
            if connection is not None:
                connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500


@app.route("/update_deadline", methods=["POST"])
def update_deadline():
    data = request.get_json()
    deadline_id = data.get("id")
    new_task = data.get("task")
    new_date = data.get("date")

    if not deadline_id:
        return jsonify("Missing deadline ID"), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            if new_task:
                update_sql = "UPDATE deadlines SET task = %s WHERE id = %s"
                cursor.execute(
                    update_sql,
                    (
                        new_task,
                        deadline_id,
                    ),
                )
                connection.commit()
            if new_date:
                update_sql = "UPDATE deadlines SET date = %s WHERE id = %s"
                cursor.execute(
                    update_sql,
                    (
                        new_date,
                        deadline_id,
                    ),
                )
                connection.commit()
            return jsonify("Updated deadline"), 200
        except (Exception, psycopg.Error) as error:
            print("Error while updating deadline in PostgreSQL", error)
            return jsonify("Failed to update deadline"), 500
        finally:
            if connection is not None:
                connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500


@app.route("/complete_deadline", methods=["POST"])
def complete_deadline():
    data = request.get_json()
    deadline_id = data.get("id")

    if not deadline_id:
        return jsonify("Missing deadline ID"), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            update_sql = "UPDATE deadlines SET completed = 'true' WHERE id = %s"
            cursor.execute(update_sql, (deadline_id,))
            connection.commit()
            if cursor.rowcount == 0:
                return jsonify("No such deadline found"), 404
            return jsonify("Deadline marked as completed"), 200
        except (Exception, psycopg.Error) as error:
            print("Error while updating deadline in PostgreSQL", error)
            return jsonify("Failed to mark deadline as completed"), 500
        finally:
            if connection is not None:
                connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500


@app.route("/mark_incomplete", methods=["POST"])
def mark_incomplete():
    data = request.get_json()
    deadline_id = data.get("id")

    if not deadline_id:
        return jsonify("Missing deadline ID"), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            update_sql = "UPDATE deadlines SET completed = 'false' WHERE id = %s"
            cursor.execute(update_sql, (deadline_id,))
            connection.commit()
            if cursor.rowcount == 0:
                return jsonify("No such deadline found"), 404
            return jsonify("Deadline marked as incomplete"), 200
        except (Exception, psycopg.Error) as error:
            print("Error while updating deadline in PostgreSQL", error)
            return jsonify("Failed to mark deadline as incomplete"), 500
        finally:
            if connection is not None:
                connection.close()
    else:
        return jsonify("Failed to connect to the database"), 500


@app.route("/clean_database", methods=["POST"])
def clean_database():
    # Connect to the user database to get valid userids
    connection_user = get_user_db_connection()
    valid_userids = []
    if connection_user:
        try:
            cursor_user = connection_user.cursor()
            cursor_user.execute("SELECT DISTINCT userid FROM notes_user_2")
            valid_userids_results = cursor_user.fetchall()
            valid_userids = [userid[0] for userid in valid_userids_results]
        except (Exception, psycopg.Error) as error:
            print("Error fetching userids from user database:", error)
            return jsonify("Failed to fetch userids from user database"), 500
        finally:
            cursor_user.close()
            connection_user.close()

    # If no valid userids are found, there's nothing to clean
    if not valid_userids:
        return jsonify("No userids found. No cleanup needed."), 200

    # Connect to the main database to delete deadlines not associated with valid userids
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            format_strings = ",".join(["%s"] * len(valid_userids))
            # Delete deadlines where userid is not in the list of valid userids
            cursor.execute(
                f"DELETE FROM deadlines WHERE userid NOT IN ({format_strings})",
                tuple(valid_userids),
            )
            connection.commit()
            deleted_rows = cursor.rowcount
            return (
                jsonify(
                    f"Cleaned up {deleted_rows} deadlines not linked to a valid user."
                ),
                200,
            )
        except (Exception, psycopg.Error) as error:
            print("Error while cleaning deadlines from main database:", error)
            return jsonify("Failed to clean deadlines from main database"), 500
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify("Failed to connect to the main database"), 500


if __name__ == "__main__":
    app.run(debug=True)
