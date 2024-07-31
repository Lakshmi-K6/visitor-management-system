from flask import Flask, redirect, url_for, request, render_template, flash, session
import mysql.connector
from flask_session import Session
from key import secret_key, salt, salt2
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'
mydb = mysql.connector.connect(host="localhost", user="root", password="200423A", db="visitors")

@app.route('/')
def admin():
    return render_template('title.html')

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if session.get('user'):
        return redirect(url_for('admin'))
    if request.method == 'POST':
        print(request.form)
        name = request.form['name']
        password = request.form['password']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from admin where username=%s and password=%s', [name, password])
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            session['admin'] = name
            return redirect(url_for('adminhome'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/adminhome')
def adminhome():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('adduser'))

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from admin where username=%s', [username])
        count = cursor.fetchone()[0]
        cursor.execute('select count(*) from admin where email=%s', [email])
        count1 = cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            flash('Username already in use')
            return render_template('registration.html')
        elif count1 == 1:
            flash('Email already in use')
            return render_template('registration.html')
        data = {'username': username, 'password': password, 'email': email}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nFollow this link for further steps - {url_for('confirm', token=token(data, salt), _external=True)}"
        sendmail(to=email, subject=subject, body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('adminlogin'))
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer = URLSafeTimedSerializer(secret_key)
        data = serializer.loads(token, salt=salt, max_age=180)
    except Exception as e:
        return 'Link Expired register again'
    else:
        cursor = mydb.cursor(buffered=True)
        username = data['username']
        cursor.execute('select count(*) from admin where username=%s', [username])
        count = cursor.fetchone()[0]
        if count == 1:
            cursor.close()
            flash('You are already registered!')
            return redirect(url_for('adminlogin'))
        else:
            cursor.execute('insert into admin (username, password, email) values(%s, %s, %s)', [data['username'], data['password'], data['email']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('adminlogin'))

@app.route('/forget', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select count(*) from admin where email=%s', [email])
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('SELECT email from admin where email=%s', [email])
            status = cursor.fetchone()[0]
            cursor.close()
            subject = 'Forget Password'
            confirm_link = url_for('reset', token=token(email, salt=salt2), _external=True)
            body = f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email, body=body, subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('adminlogin'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    try:
        serializer = URLSafeTimedSerializer(secret_key)
        email = serializer.loads(token, salt=salt2, max_age=180)
    except:
        abort(404, 'Link Expired')
    else:
        if request.method == 'POST':
            newpassword = request.form['npassword']
            confirmpassword = request.form['cpassword']
            if newpassword == confirmpassword:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('update admin set password=%s where email=%s', [newpassword, email])
                mydb.commit()
                flash('Reset Successful')
                return redirect(url_for('adminlogin'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('adminlogin'))

@app.route('/adduser', methods=['GET', 'POST'])
def adduser():
    if request.method == 'POST':
        print(request.form)
        id1 = request.form['id1']
        fullname = request.form['name']
        mobile = request.form['mobile']
        room = request.form['room']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('insert into users values(%s, %s, %s, %s)', [id1, fullname, room, mobile])
        mydb.commit()
        cursor.close()
        return redirect(url_for('visitor'))
    return render_template('Add-Users.html')

@app.route('/visitor', methods=['GET', 'POST'])
def visitor():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT * from users')
    data = cursor.fetchall()
    cursor.execute('Select * from visitors')
    details = cursor.fetchall()
    cursor.close()
    if request.method == "POST":
        id1 = request.form['id']
        name = request.form['name']
        mobile = request.form['mobile']
        cursor = mydb.cursor(buffered=True)
        cursor.execute('INSERT INTO visitors (vid, vname, phno) values(%s, %s, %s)', [id1, name, mobile])
        cursor.execute('Select * from visitors')
        details = cursor.fetchall()
        mydb.commit()
    return render_template('VisitorRecord.html', data=data, details=details)

@app.route('/checkinvisitor/<id1>')
def checkinvisitor(id1):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('update visitors set checkin=current_timestamp() where vid=%s', [id1])
    mydb.commit()
    return redirect(url_for('visitor'))

@app.route('/checkoutvisitor/<id1>')
def checkoutvisitor(id1):
    cursor = mydb.cursor(buffered=True)
    cursor.execute('update visitors set checkout=current_timestamp() where vid=%s', [id1])
    mydb.commit()
    return redirect(url_for('visitor'))

app.run(debug=True, use_reloader=True)
