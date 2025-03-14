import mysql.connector
import time
import json
import requests
from datetime import date
import html2text


# Connect to database
# You may need to edit the connect function based on your local settings.#I made a password for my database because it is important to do so. Also make sure MySQL server is running or it will not connect
def connect_to_sql():
    conn = mysql.connector.connect(user='root', password='',
                                   host='localhost', database='jobhunter',
                                   autocommit=True
                                   )
    return conn


# Create the table structure
def create_tables(cursor):
    # Creates table
    # Must set Title to CHARSET utf8 unicode Source: http://mysql.rjweb.org/doc.php/charcoll.
    # Python is in latin-1 and error (Incorrect string value: '\xE2\x80\xAFAbi...') will occur if Description is not in unicode format due to the json data
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INT PRIMARY KEY auto_increment, 
        Job_id varchar(50) UNIQUE, 
        company varchar (300), 
        Created_at DATE, 
        url varchar(3000), 
        Title TEXT, 
        Description TEXT
    ); ''')


# Query the database.
# You should not need to edit anything in this function
def query_sql(cursor, query):
    cursor.execute(query)
    return cursor


# Add a new job
def add_new_job(cursor, jobdetails):
    # extract all required columns
    job_id = jobdetails['id']
    company = jobdetails['company_name']
    created_at = jobdetails['publication_date'][0:10]
    url = jobdetails['url']
    title = jobdetails['title']
    description = html2text.html2text(jobdetails['description'])

    # Insert the data into the table
    query = '''
        INSERT INTO jobs (Job_id, company, Created_at, url, Title, Description)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
     # %s is what is needed for Mysqlconnector as SQLite3 uses ? the Mysqlconnector uses %s
    
    try:
        cursor.execute(query, (job_id, company, created_at, url, title, description))  # Execute safely
        print(f"New job added: {title} at {company}")

    except mysql.connector.IntegrityError:
        print(f"Job already exists: {title} at {company}")

    except mysql.connector.Error as err:
        print(f"Error inserting job: {err}")


# Check if new job
def check_if_job_exists(cursor, jobdetails):
    query = "SELECT * FROM jobs WHERE Job_id = %s"

    cursor.execute(query, (jobdetails['id'],))  # Execute safely with parameterized value
    result = cursor.fetchone()  # Fetch the result

    if result:
        print(f"Job exists: {jobdetails['title']} at {jobdetails['company_name']}")
    else:
        print(f"Job does NOT exist: {jobdetails['title']} at {jobdetails['company_name']}")

    return result is not None

# Deletes job
def delete_job(cursor, jobdetails):
    query = "DELETE FROM jobs WHERE Job_id = %s"

    # Execute using query_sql() but also pass the job ID
    cursor = query_sql(cursor, query)
    cursor.execute(query, (jobdetails['id'],))  # Ensure safe parameterized execution
    print(f"Job deleted: {jobdetails['id']}")  
    return query_sql(cursor, query)

# Deletes jobs older than 14 days
def delete_old_jobs(cursor):
    query = "DELETE FROM jobs WHERE Created_at < (CURDATE() - INTERVAL 14 DAY)"
    cursor.execute(query)
    deleted_count = cursor.rowcount  # Get number of affected rows
    print(f"{deleted_count} old jobs deleted")


# Grab new jobs from a website, Parses JSON code and inserts the data into a list of dictionaries do not need to edit
def fetch_new_jobs():
    query = requests.get("https://remotive.io/api/remote-jobs")
    datas = json.loads(query.text)

    return datas


# Main area of the code. Should not need to edit
def jobhunt(cursor):
    # Fetch jobs from website
    jobpage = fetch_new_jobs()  # Gets API website and holds the json data in it as a list
    # use below print statement to view list in json format
    # print(jobpage)
    add_or_delete_job(jobpage, cursor)


def add_or_delete_job(jobpage, cursor):
    # Add your code here to parse the job page
    for jobdetails in jobpage['jobs']:  # EXTRACTS EACH JOB FROM THE JOB LIST. It errored out until I specified jobs. This is because it needs to look at the jobs dictionary from the API. https://careerkarma.com/blog/python-typeerror-int-object-is-not-iterable/
        title = jobdetails['title']
        company = jobdetails['company_name']

        # Add in your code here to check if the job already exists in the DB
        is_job_found = check_if_job_exists(cursor, jobdetails)
        
        if is_job_found:
            print(f"Job already exists: {title} at {company}")
        else:
            add_new_job(cursor, jobdetails)
            print(f"New job added: {title} at {company}")



# Setup portion of the program. Take arguments and set up the script
# You should not need to edit anything here.
def main():
    # Important, rest are supporting functions
    # Connect to SQL and get cursor
    conn = connect_to_sql()
    cursor = conn.cursor()
    create_tables(cursor)

    while (1):  # Infinite Loops. Only way to kill it is to crash or manually crash it. We did this as a background process/passive scraper
        jobhunt(cursor)
        delete_old_jobs(cursor)
        time.sleep(14400)  # Sleep for 4h, this is ran every 4 hours because API or web interfaces have request limits. Your reqest will get blocked.


# Sleep does a rough cycle count, system is not entirely accurate
# If you want to test if script works change time.sleep() to 10 seconds and delete your table in MySQL
if __name__ == '__main__':
    main()

