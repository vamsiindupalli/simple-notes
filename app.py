from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file# just for creating general seession   
import mysql.connector   ### for connecting database it is one of the package for connecting database

from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session ##here it will add additional security to session import from flask above 1st cmd
from io import  BytesIO  ## which converts buinary format to bytes
import flask_excel as excel  ## for creating excel data
import re
app=Flask(__name__)  ## these is called object creation
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
app.secret_key='codegnan@2018'  # for using flash we use this secret key
Session(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='snmproject')
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        username=request.form['username']
        uemail=request.form['email']
        password=request.form['password']
        cpassword=request.form['cpassword']
        cursor=mydb.cursor()
        cursor.execute("select count(useremail) from users where user_email=%s",[uemail])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            print(gotp)
            udata={"username":username,'useremail':uemail,"pword":password,'otp':gotp
            }
            subject='otp for simple notes manager'
            body=f'otp for registration of simple notes manager {gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('otp has sent to given mail')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash("email already exist")
            return redirect(url_for('login'))
        else:
            return "something went wrong"
                
    return render_template('create.html')
    

@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dudata=decode(data=enudata)
        except Exception as e:
            print(e)
            print("something went wrong")
        else:
            if dudata['otp']==uotp:
                cursor=mydb.cursor()
                cursor.execute("insert into users(username,useremail,password) values(%s,%s,%s)",[dudata['username'],dudata['useremail'],dudata['pword']])
                mydb.commit()  ## these is tcl command we must use because whene data came  from frameworks we must use commit 
                cursor.close()
                flash("registeration sucessfully done")
                return redirect(url_for('login'))
            else:
                return "otp not valid register again"
    return render_template('otp.html')
   
@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['email'] 
            pword=request.form['password']
            cursor=mydb.cursor(buffered=True) # actiavting mysql cursor and buffered=True meeans it will handle some error
            cursor.execute("select count(user_email) from users where user_email=%s",[uemail])
            bdata=cursor.fetchone()
            
            if bdata[0]==1:
                cursor.execute('select password from users where user_email=%s',[uemail])
                dpassword=cursor.fetchone()
                if pword==dpassword[0].decode('utf-8'):
                    print('before',session)
                    session['user']=uemail
                    print("after",session)
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('login'))
            elif bdata[0]==0:
                flash('email not registered')
                return redirect(url_for('create'))
            else:
                return "something went wrong"
    else:
        return redirect(url_for('dashboard'))

    return render_template('login.html')
@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/addnotes',methods=['GET','POST'])

def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            uid=cursor.fetchone()
            if uid:
                try:

                    cursor.execute('insert into notes(title,ndescription,user_id) values(%s,%s,%s)',[title,description,uid[0]])
                    mydb.commit()
                    cursor.close()
                    # flash('Notes added Successfully')
                    # return redirect(url_for('dashboard'))
                except mysql.connector.errors.IntegrityError:
                
                    flash("Duplicate Title entry")
                    return redirect(url_for('dashboard'))
                except mysql.connector.errors.ProgrammingError:
                    flash('could note add notes')
                    print(mysql.connector.errors.ProgrammingError)
                    return redirect(url_for('dashboard'))
                else:
                    flash('notes added sucessfully')
                    return redirect(url_for('dashboard'))
                    
            else:
                return 'Something Went Wrong'
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select n_id,title,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall()  # iwill return in tuple format of all data   data from backend be like [(1,"python"),(2,"java")]
        except Exception as e:
            print(e)
            flash('data not found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallnotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where nid=%s',[nid])
            ndata=cursor.fetchone() #(1,"python","hellowrold")
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:    
            return render_template('view.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
    
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notes where nid=%s",[nid])
        ndata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,description,nid])
            mydb.commit()
            cursor.close()
            flash("updated notes succesfully")
            return redirect(url_for('viewnotes',nid=nid))
        return render_template('updatenotes.html',ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/deletenotes/<nid>',methods=['GET','POST'])
def deletenotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("delete from notes where nid=%s",[nid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash("something went wrong")
            return redirect(url_for('viewallnotes'))
        else:
            flash("deleted notes sucessfully")
            return redirect(url_for('viewallnotes'))
    else:
        return redirect(url_for('login'))

@app.route('/uploadfiles',methods=['GET','POST'])
def uploadfiles():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']  ##  for accepting file data
        # print(filedata) # it will show what type of file it is 
        # print(filedata.read()) # it will show data in the file
            fname=filedata.filename ## to know the file name
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('could not upload file')
                return redirect(url_for('dashboard'))
            else:
                flash('file uploaded sucessfully')
                return redirect(url_for('dashboard'))


        return render_template('uploadfiles.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[uid[0]])
            filedata=cursor.fetchall()  
        except Exception as e :
            print(e)
            flash('data not found')
            return redirect(url_for('dashboard'))
        else:
            return render_template('viewallfiles.html',filedata=filedata)
    else:
        return redirect(url_for('login'))

@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash('could not upload file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))
    

@app.route('/downloadfiles/<fid>')
def downloadfiles(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash('could not upload file')
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))
@app.route('/deletefile/<fid>')
def deletefile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("delete from filedata where fid=%s",[fid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('something went wrong')
            return redirect(url_for('viewallfiles'))
        
        else:
            flash("succefully deleted")
            return redirect(url_for('viewallfiles'))
    else:
        return redirect(url_for('login'))
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
            uid=cursor.fetchone() #(1,)
            cursor.execute('select nid,title,ndescription,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall()  #[(1,'python',2024)]
        except Exception as e:
            print(e)
            flash('no data found')
            return redirect(url_for('dashboard'))
        else:
            array_data=[list(i) for i in ndata]
            columns=["Notesid","Title","Content","Created_time"]
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename="notesdata")
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE) # ^ here cap meanning it must be starting letter
                if(pattern.match(sdata)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or ndescription like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('no data found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:

            print(e)
            flash('cannot find anything')
            return redirect(url_for('dashboard'))
        


    else:
        return redirect(url_for('login'))
        

app.run(use_reloader=True,debug=True)