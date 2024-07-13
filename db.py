from bs4 import BeautifulSoup
import requests
import mysql.connector
from mysql.connector import Error

# Database functions


def create_connection():
    """Create a database connection to the MySQL database."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Replace with your MySQL host
            user='root',  # Replace with your MySQL username
            password='Anu@1234',  # Replace with your MySQL password
            database='attendance_db'  # Replace with your database name
        )
        if connection.is_connected():
            print("Connected to MySQL database")
    except Error as e:
        print(f"Error: '{e}'")

    return connection


def insert_or_update_subject_attendance(connection, roll_no, subject_name, taken_sessions, points_over_sessions, percentage_over_sessions, sessions_rem, average_attendance):
    """Insert a new record or update an existing record in the subject_attendance table."""
    cursor = connection.cursor()
    query = """
    INSERT INTO subject_attendance (roll_no, subject_name, taken_sessions, points_over_sessions, percentage_over_sessions, sessions_rem, average_attendance)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        taken_sessions = VALUES(taken_sessions),
        points_over_sessions = VALUES(points_over_sessions),
        percentage_over_sessions = VALUES(percentage_over_sessions),
        sessions_rem = VALUES(sessions_rem),
        average_attendance = VALUES(average_attendance);
    """
    cursor.execute(query, (roll_no, subject_name, taken_sessions,
                           points_over_sessions, percentage_over_sessions, sessions_rem, average_attendance))
    connection.commit()
    cursor.close()


# Web scraping code
dashboard_url = 'http://moodle.glwec.in/moodle/my/'

# Credentials
credentials = {
    'username': '21733142',
    'password': 'Anu@1234'
}

# Start a session
session = requests.Session()

# Send a POST request to login directly
login_url = 'http://moodle.glwec.in/moodle/login/index.php'
login_page_response = session.get(login_url)
login_page_soup = BeautifulSoup(login_page_response.content, 'html.parser')

# Find the CSRF token
csrf_token = login_page_soup.find('input', {'name': 'logintoken'}).get('value')

# Include the CSRF token in the credentials
credentials['logintoken'] = csrf_token

# Send a POST request to login
response = session.post(login_url, data=credentials)

# Check if login was successful
if response.status_code == 200:
    print("Login successful!")

    # Get the dashboard page
    response = session.get(dashboard_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the dashboard page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all course links
        course_links = soup.find_all('a', class_='list-group-item')

        for course_link in course_links:
            course_url = course_link.get('href')
            course_name = course_link.text.strip()

            # Navigate to the course page
            response = session.get(course_url)
            if response.status_code == 200:
                course_soup = BeautifulSoup(
                    response.content, 'html.parser')

                # Find the link to Attendance
                attendance_link = course_soup.find(
                    'span', class_='instancename', string='Attendance')
                if attendance_link:
                    attendance_link = attendance_link.find_parent('a')
                if attendance_link:
                    attendance_url = attendance_link.get('href')
                    print(f"Attendance URL found: {attendance_url}")

                    # Navigate to the attendance page
                    response = session.get(attendance_url)
                    if response.status_code == 200:
                        attendance_soup = BeautifulSoup(
                            response.content, 'html.parser')

                        # Find the link to "All sessions"
                        all_sessions_link = attendance_soup.find(
                            'a', string='All courses')
                        if all_sessions_link:
                            all_sessions_url = all_sessions_link.get(
                                'href')
                            print(
                                f"All Sessions URL found: {all_sessions_url}")

                            # Navigate to the "All sessions" page
                            response = session.get(all_sessions_url)
                            if response.status_code == 200:
                                all_sessions_soup = BeautifulSoup(
                                    response.content, 'html.parser')

                                # Find the row containing the average attendance
                                last_row = all_sessions_soup.find(
                                    'tr', class_='lastrow')
                                average_attendance = 0
                                if last_row:
                                    average_attendance_cell = last_row.find(
                                        'td', class_='colatt')
                                    if average_attendance_cell:
                                        average_attendance_text = average_attendance_cell.text.strip()
                                        print(
                                            f"Extracted average attendance text: {average_attendance_text}")
                                        try:
                                            average_attendance = float(
                                                average_attendance_text.rstrip('%'))
                                        except ValueError as ve:
                                            print(
                                                f"Error converting average attendance to float: {ve}")

                                print(
                                    f"Average attendance: {average_attendance}")

                                # Find all rows containing subject-wise attendance data
                                rows = all_sessions_soup.find_all(
                                    'tr', class_='')

                                roll_no_with_prefix = '2456' + \
                                    credentials['username']

                                for row in rows:
                                    try:
                                        # Extract data from each row
                                        course_cell = row.find(
                                            'td', class_='colcourse')
                                        if course_cell:
                                            subject_name = course_cell.text.strip()
                                            taken_sessions = int(
                                                row.find('td', class_='colsessionscompleted').text.strip())
                                            points_over_sessions = row.find(
                                                'td', class_='colpointssessionscompleted').text.strip()
                                            percentage_over_sessions = row.find(
                                                'td', class_='colpercentagesessionscompleted').text.strip()

                                            # Parse points_over_sessions to get the points taken and total sessions
                                            points_taken, total_sessions = map(
                                                int, points_over_sessions.split('/'))

                                            # Calculate percentage_over_sessions
                                            percentage_over_sessions = float(
                                                percentage_over_sessions.rstrip('%'))

                                            # Calculate sessions_rem needed to achieve 75% attendance
                                            current_attendance = float(
                                                percentage_over_sessions)
                                            required_attendance = 75.0
                                            sessions_attended = taken_sessions
                                            total_sessions = total_sessions

                                            sessions_needed = (
                                                (required_attendance * total_sessions) - (current_attendance * total_sessions)) // 100
                                            sessions_rem = int(
                                                sessions_needed)

                                            # Store subject-wise attendance in the database
                                            conn = create_connection()
                                            if conn:
                                                insert_or_update_subject_attendance(
                                                    conn, roll_no_with_prefix, subject_name, taken_sessions, points_taken, percentage_over_sessions, sessions_rem, average_attendance)
                                                conn.close()

                                    except Exception as e:
                                        print(
                                            f"Error processing row: {e}")

                            else:
                                print(
                                    f"Failed to retrieve All Sessions page. Status code: {response.status_code}")
                        else:
                            print(
                                "All Sessions link not found. Check the HTML structure.")

                    else:
                        print(
                            f"Failed to retrieve attendance page. Status code: {response.status_code}")
                else:
                    print(
                        "Attendance link not found. Check the HTML structure.")

            else:
                print(
                    f"Failed to retrieve course page. Status code: {response.status_code}")

    else:
        print(
            f"Failed to retrieve dashboard page. Status code: {response.status_code}")

else:
    print("Login failed. Please check your credentials.")
