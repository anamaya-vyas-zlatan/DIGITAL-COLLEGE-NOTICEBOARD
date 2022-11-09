from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,IntegerField, ValidationError, DateField, SubmitField, FileField
from passlib.hash import sha256_crypt
from functools import wraps
import mysql.connector

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'qwerty123'
app.config['MYSQL_DB'] = 'HCI_PROJ'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql =MySQL(app)

@app.route('/')
def index():
    return render_template('Main_Page.html')


#################################################################
# TEACHER INTERFACE
#################################################################
# Teacher Login
@app.route('/login_teacher', methods=['GET', 'POST'])
def login_teacher():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Username = request.form['Username']
        Password = request.form['Password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Teacher WHERE Username = %s", [Username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if Password == password:
                # Passed
                session['logged_in_Teacher'] = True
                session['Username'] = Username

                flash('You are now logged in')
                return redirect(url_for('dashboard_teacher'))
            else:
                error = 'Invalid login'
                return render_template('Teacher_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Teacher_login.html', error=error)

    return render_template('Teacher_login.html')

def is_logged_in_teacher(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in_Teacher' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap

#LogOut Teacher
@app.route('/logoutteacher')
@is_logged_in_teacher
def logout_teacher():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

#Class Creation
class CreateClass(Form):
    Class_Number = StringField('Class Number', [validators.Length(min = 1, max = 80)])
    Course_Name = StringField('Course Name', [validators.Length(min = 1, max = 80)])
    Course_ID = StringField('Course ID', [validators.Length(min=1, max=80)])
    Slot = StringField('Slot', [validators.Length(min = 1, max = 80)])

@app.route('/CreateClass', methods=['GET', 'POST'])
@is_logged_in_teacher
def createclass():
    form = CreateClass(request.form)
    if request.method == 'POST' and form.validate():
        Class_Number = form.Class_Number.data
        Course_Name = form.Course_Name.data
        Course_ID = form.Course_ID.data
        Slot = form.Slot.data
        Teacher_Name = None
        Teacher_ID = session['Username']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM Teacher WHERE Username = %s", [Teacher_ID])
        if result>0:
            data = cur.fetchone()
            Teacher_Name = data['Teacher_Name']
        cur.execute("INSERT INTO Class(Class_Number, Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID) VALUES(%s, %s, %s, %s, %s, %s)",
                    (Class_Number,Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID))

        mysql.connection.commit()

        cur.close()

        return redirect(url_for('index'))
    return render_template('CreateClass.html', form = form)

#Add Students Class
@app.route('/add_student_class', methods=['GET', 'POST'])
@is_logged_in_teacher
def addstudentClass():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Class_Number = request.form['Class_Number']
        Student_ID = request.form['Student_ID']
        Teacher_ID = session['Username']
        # Create cursor
        cur = mysql.connection.cursor()
        flag =0
        # Get user by username
        result = cur.execute("SELECT * FROM Teacher WHERE Username = %s", [session['Username']])
        if result > 0:
            data = cur.fetchone()
            Teacher_Name = data['Teacher_Name']
            Teacher_Email = data['Email']
        student_result = cur.execute("SELECT * FROM Student WHERE Username = %s", [Student_ID])
        if student_result > 0:
            # Get stored hash
            data2 = cur.fetchone()
            Student_Name = data2['Student_Name']
            Email = data2['Email']
        else:
            error = 'Student not found'
            flag =1
            return render_template('Add_Student.html', error=error)
        class_result = cur.execute("SELECT * FROM Class WHERE Class_Number = %s", [Class_Number])
        if class_result > 0:
            # Get stored hash
            data3 = cur.fetchone()
            Course_Name = data3['Course_Name']
            Course_ID = data3['Course_ID']
            Slot = data3['Slot']
        else:
            error = 'Class not found'
            flag=1
            return render_template('Add_Student.html', error=error)

        cur.execute(
            "INSERT INTO Endrolment(Class_Number, Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID, Teacher_Email, Student_Name, Email, Student_ID) VALUES(%s, %s, %s, %s, %s,%s, %s, %s, %s, %s )",
            (Class_Number, Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID, Teacher_Email,Student_Name,Email,Student_ID))
        mysql.connection.commit()
        cur.close()
        if flag == 0:
            flash('Student Registered')
            return redirect(url_for('addstudentClass'))

    return render_template('Add_Student.html')

#Add Message
class CreateMessage(Form):
    Message_Text = TextAreaField('Message Text')
    Class_Number = StringField('Class Number', [validators.Length(min = 1, max = 80)])


@app.route('/add_messaage_class', methods=['GET', 'POST'])
@is_logged_in_teacher
def addmessageClass():
    form = CreateMessage(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        Message_Text = form.Message_Text.data
        Class_Number = form.Class_Number.data
        Teacher_ID = session['Username']
        cur = mysql.connection.cursor()
        flag =0
        result = cur.execute("SELECT * FROM Teacher WHERE Username = %s", [session['Username']])
        if result > 0:
            data = cur.fetchone()
            Teacher_Name = data['Teacher_Name']
        class_result = cur.execute("SELECT * FROM Class WHERE Class_Number = %s", [Class_Number])
        if class_result > 0:
            data3 = cur.fetchone()
            Course_Name = data3['Course_Name']
            Course_ID = data3['Course_ID']
            Slot = data3['Slot']
        else:
            error = 'Class not found'
            flag=1
            return render_template('Add_Message.html', error=error)

        cur.execute(
            "INSERT INTO message(Class_Number, Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID, Message_Text) VALUES(%s, %s, %s, %s, %s,%s, %s)",
            (Class_Number, Course_Name, Course_ID, Slot, Teacher_Name, Teacher_ID, Message_Text))
        mysql.connection.commit()
        cur.close()
        if flag == 0:
            flash('Message Sent')
            return redirect(url_for('addmessageClass'))

    return render_template('Add_Message.html')



#View Class
@app.route('/ViewClass',methods = ['GET', 'POST'])
@is_logged_in_teacher
def viewclass():
    x =0
    if request.method == 'POST':
        Class_Number = request.form['Class_Number']
        cur =mysql.connection.cursor()
        result = cur.execute("SELECT * FROM Endrolment WHERE Class_Number = %s ",[Class_Number])
        details = cur.fetchall()

        if result > 0:
            x=1
            cur.execute("SELECT * FROM Endrolment WHERE Class_Number = %s ",[Class_Number])
            data = cur.fetchone()
            Course_Name = data['Course_Name']
            Course_ID = data['Course_ID']
            Slot = data['Slot']
            return render_template('View_Class.html', details = details, Course_Name = Course_Name, Course_ID = Course_ID, Slot =Slot, Class_Number = Class_Number,x=x)
        else:
           error = 'Class not found'
           return render_template('View_Class.html', error=error, x=x)
        cur.close()
    return render_template('View_Class.html')

@app.route('/delete_student/<string:Student_ID>', methods=['POST'])
@is_logged_in_teacher
def delete_student(Student_ID):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM Endrolment WHERE Student_ID = %s", [Student_ID])
    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Student Deleted', 'success')
    # cat = mysql.connection.cursor()
    # cat.execute("DELETE FROM College_Details WHERE College_Name = %s", [College_Name])
    # mysql.connection.commit()
    # cat.close()

    return redirect(url_for('dashboard_teacher'))


#Teacher Dashboard
@app.route('/dashboardteacher',methods=['GET', 'POST'])
@is_logged_in_teacher
def dashboard_teacher():
    name = session['Username']
    return render_template('Teacher_Dashboard.html', name=name)




#################################################################
# CLUB INTERFACE
#################################################################
#Club Login
@app.route('/login_club', methods=['GET', 'POST'])
def login_club():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Username = request.form['Username']
        Password = request.form['Password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Club WHERE Username = %s", [Username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if Password == password:
                # Passed
                session['logged_in_Club'] = True
                session['Username'] = Username

                flash('You are now logged in')
                return redirect(url_for('dashboard_club'))
            else:
                error = 'Invalid login'
                return render_template('Club_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Club_login.html', error=error)

    return render_template('Club_login.html')

def is_logged_in_club(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in_Club' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap

#LogOut Club
@app.route('/logoutclub')
@is_logged_in_club
def logout_club():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


#Club Dashboard
@app.route('/dashboardclub', methods=['GET', 'POST'])
@is_logged_in_club
def dashboard_club():
    name = session['Username']
    return render_template('Club_Dashboard.html', name=name)

#Club Details
@app.route('/clubdetails')
@is_logged_in_club
def club_details():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Club WHERE Username = %s ", [session['Username']])
    details = cur.fetchone()
    Club_Name = details['Club_Name']
    cur.execute("SELECT * FROM Club_Admin WHERE Club_Name = %s ", [Club_Name])
    data = cur.fetchall()

    Club_Email = details['Club_Email']
    Club_ID = session['Username']
    cur.close()
    return render_template('Club_Details.html', data= data, Club_Name = Club_Name, Club_Email = Club_Email, Club_ID = Club_ID)

#Add Member
@app.route('/add_student_club', methods=['GET', 'POST'])
@is_logged_in_club
def addstudentClub():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Student_ID = request.form['Student_ID']
        # Create cursor
        cur = mysql.connection.cursor()
        flag =0
        # Get user by username
        result = cur.execute("SELECT * FROM Club WHERE Username = %s", [session['Username']])
        if result > 0:
            data = cur.fetchone()
            Club_Name = data['Club_Name']
            Club_Email = data['Club_Email']
            Club_ID = session['Username']
        student_result = cur.execute("SELECT * FROM Student WHERE Username = %s", [Student_ID])
        if student_result > 0:
            # Get stored hash
            data2 = cur.fetchone()
            Student_Name = data2['Student_Name']
            Email = data2['Email']
        else:
            error = 'Student not found'
            flag =1
            return render_template('Add_Member.html', error=error)

        cur.execute(
            "INSERT INTO Endrolment_Club(Club_ID, Club_Name, Club_Email, Student_Name, Student_Email, Student_ID) VALUES(%s, %s, %s, %s, %s,%s)",
            (Club_ID, Club_Name, Club_Email,Student_Name,Email,Student_ID))
        mysql.connection.commit()
        cur.close()
        if flag == 0:
            flash('Member Added')
            return redirect(url_for('addstudentClub'))

    return render_template('Add_Member.html')

#Add Message Club
class CreateMessageClub(Form):
    Message_Text = TextAreaField('Message Text')

@app.route('/add_messaage_club', methods=['GET', 'POST'])
@is_logged_in_club
def addmessageClub():
    form = CreateMessageClub(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        Message_Text = form.Message_Text.data
        cur = mysql.connection.cursor()
        flag =0
        result = cur.execute("SELECT * FROM Club WHERE Username = %s", [session['Username']])
        if result > 0:
            data = cur.fetchone()
            Club_Name = data['Club_Name']
            Username = session['Username']
        cur.execute(
            "INSERT INTO Message_Club(Club_Name, Username, Message_Text) VALUES(%s, %s, %s)",
            (Club_Name, Username, Message_Text))
        mysql.connection.commit()
        cur.close()
        if flag == 0:
            flash('Message Sent')
            return redirect(url_for('addmessageClub'))

    return render_template('Add_Message_Club.html')

#View Club Members
@app.route('/ViewClub',methods = ['GET', 'POST'])
@is_logged_in_club
def viewclub():
    x = 1
    cur =mysql.connection.cursor()
    Club_ID = session['Username']
    result = cur.execute("SELECT * FROM Endrolment_Club WHERE Club_ID = %s ",[session['Username']])
    details = cur.fetchall()
    if result > 0:
        return render_template('View_Club.html', details = details,x=x, Club_ID = Club_ID)
    else:
        x = 0
        error = 'Members not found'
        return render_template('View_Club.html', error=error, x=x, Club_ID = Club_ID)
        cur.close()
    return render_template('View_Club.html', Club_ID = Club_ID)

@app.route('/delete_student_club/<string:Student_ID>', methods=['POST'])
@is_logged_in_club
def delete_student_club(Student_ID):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute("DELETE FROM Endrolment_Club WHERE Student_ID = %s", [Student_ID])
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()
    flash('Student Deleted', 'success')
    return redirect(url_for('dashboard_club'))

#################################################################
# VIT ADMIN INTERFACE
#################################################################
#Admin Login
@app.route('/login_Admin', methods=['GET', 'POST'])
def login_admin():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Username = request.form['Username']
        Password = request.form['Password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM College_Admin WHERE Username = %s", [Username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if Password == password:
                # Passed
                session['logged_in_Admin'] = True
                session['Username'] = Username

                flash('You are now logged in')
                return redirect(url_for('dashboard_admin'))
            else:
                error = 'Invalid login'
                return render_template('Admin_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Admin_login.html', error=error)

    return render_template('Admin_login.html')

def is_logged_in_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in_Admin' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap

#LogOut Admin
@app.route('/logoutadmin')
@is_logged_in_admin
def logout_admin():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


#Club Dashboard
@app.route('/dashboardadmin', methods=['GET', 'POST'])
@is_logged_in_club
def dashboard_admin():
    name = session['Username']
    return render_template('Admin_Dashboard.html', name=name)













#################################################################
# STUDENT INTERFACE
#################################################################

# Student Registration
class RegisterStudent(Form):
    Student_Name = StringField('Student Name', [validators.Length(min = 1, max = 80)])
    Email = StringField('Email', [validators.Length(min=1, max=100)])
    Username = StringField('Username', [validators.Length(min= 1, max = 80)])
    Password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/RegisterStudent', methods=['GET', 'POST'])
def registerstudent():
    form = RegisterStudent(request.form)
    if request.method == 'POST' and form.validate():
        Student_Name = form.Student_Name.data
        Email = form.Email.data
        Username = form.Username.data
        Password = sha256_crypt.encrypt(str(form.Password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO Student(Student_Name, Email,Username, Password) VALUES(%s, %s, %s, %s)",
                    (Student_Name,Email,Username,Password))

        mysql.connection.commit()

        cur.close()

        return redirect(url_for('registerstudent'))
    return render_template('RegisterStudent.html', form = form)

#Student Login
@app.route('/login_student', methods=['GET', 'POST'])
def login_student():
    error = None
    if request.method == 'POST':
        # Get Form Fields
        Username = request.form['Username']
        Password = request.form['Password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Student WHERE Username = %s", [Username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if sha256_crypt.verify(Password, password):
                # Passed
                session['logged_in_Student'] = True
                session['Username'] = Username
                flash('You are now logged in')
                return redirect(url_for('index'))
            else:
                error = 'Invalid login'
                return render_template('student_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('student_login.html', error=error)

    return render_template('student_login.html')


if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
