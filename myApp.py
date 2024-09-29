from flask import Flask,render_template,request,session,url_for,redirect
from flask_pymongo import PyMongo,ObjectId
import smtplib,random,os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()
print(os.getenv("MONGODB_STR"))
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")
app.config["MONGO_URI"] = os.environ.get("MONGODB_STR")
db = PyMongo(app).db
client = db.loginData
data = db.clientData
def mailer(to,subject,msg):
    sender = os.getenv("EMAIL_SENDER")
    mailserver = os.getenv("EMAIL_SERVER")
    with smtplib.SMTP(mailserver, 587) as s:
        s.starttls()
        print("Logging in...")
        s.login(sender, os.getenv("SMTP_PASSW"))
        print("Login successfull.")
        print("Sending email..")
        s.sendmail(sender,to,f"Subject: {subject}\nTo: {to}\nFrom: {sender}\n\n{msg}")
        print("Mail sent successfully")

@app.route("/",methods=["GET","POST"])
def homePage():
    global id,todos
    if request.method=="POST":
        title=request.form["todoTitle"]
        desc=request.form["todoDesc"]
        if title=="":
            todos = [i for i in data.find({"email":session["email"]})]
            todos.reverse()
            return render_template("nullTitleErr.html",title=title,todos=todos,sideTitle=client.find_one({"email":session["email"]})["name"])
        elif desc=="":
            todos = [i for i in data.find({"email":session["email"]})]
            todos.reverse()
            return render_template("nullDescErr.html",title=title,todos=todos,sideTitle=client.find_one({"email":session["email"]})["name"])
        else:
            data.insert_one({"email":session["email"],"title":title,"desc":desc.strip()})
            todos = [i for i in data.find({"email":session["email"]})]
            todos.reverse()
            return render_template("homepage.html",todos=todos,sideTitle=client.find_one({"email":session["email"]})["name"])
    else:   
        session.permanent = True
        if session.get("email"):
            todos = [i for i in data.find({"email":session["email"]})]
            todos.reverse()
            return render_template("homepage.html",todos=todos,sideTitle=client.find_one({"email":session["email"]})["name"])
        else:
            return render_template("welcomePage.html",sideTitle="chroDo")

@app.route('/login',methods=["GET","POST"])
def homeLogin():
    if request.method=="POST":
        loginUserEmail = request.form["loginUserEmail"]
        loginUserPassword = request.form["loginUserPassword"]
        clientSearch = client.find_one({"email":loginUserEmail})
        if clientSearch is None:
            return render_template("loginNotFound.html",file="login.html",errorText="Client not found",loginUserEmail=loginUserEmail,loginUserPassword=loginUserPassword,sideTitle="chroDo")
        elif loginUserPassword!=clientSearch["password"]:
            return render_template("passwordLenError.html",file="login.html",errorText="Password is incorrect, please try again",loginUserEmail=loginUserEmail,loginUserPassword=loginUserPassword,sideTitle="chroDo")
        else:
            session['email']=loginUserEmail
            return redirect(url_for("homePage"))
    else:
        return render_template("login.html",sideTitle="chroDo")
    
@app.route("/signup",methods=["GET","POST"])
def homeSignup():
    global verificationMode,signupPin,userEmail,userName,userPassword
    if request.method=="POST":
        if not verificationMode:
            userEmail = request.form.get("userEmail")
            userPassword = request.form.get("userPassword")
            confirmPassword = request.form.get("confirmPassword")
            userName = request.form.get("userName")
            if client.find_one({"email":userEmail}) is not None:
                return render_template("emailExistErr.html",userEmail=userEmail,userPassword=userPassword,confirmPassword=confirmPassword,userName=userName)
            elif len(userPassword)<8:
                return render_template("passwordLenError.html",file="signup.html",errorText = "Password length must be at least 8",userEmail=userEmail,userPassword=userPassword,confirmPassword=confirmPassword,userName=userName,sideTitle="chroDo")
            elif userPassword!=confirmPassword:
                return render_template("passwordLenError.html",file="signup.html",errorText = "Password does not match with confirmed password",userEmail=userEmail,userPassword=userPassword,confirmPassword=confirmPassword,userName=userName,sideTitle="chroDo")
            else:
                verificationMode=True
                signupPin = random.randrange(100000,999999)
                mailer(userEmail,"chroDo signup verification",f"Your OTP for chroDo web application is {signupPin}")
                return render_template("signupVer.html",userEmail=userEmail)
        else:
            try:
                if not request.form.get("userOtp").isdigit():
                    return render_template("signupVerErr.html",userEmail=userEmail)
                elif not signupPin==int(request.form.get("userOtp")):
                    return render_template("signupVerErr.html",userEmail=userEmail)
                else:
                    client.insert_one({
                        "name":userName,
                        "email":userEmail,
                        "password":userPassword
                    })
                    session["email"]=userEmail
                    return redirect(url_for("homePage"))
            except:
                print(request.form)
                signupPin = random.randrange(100000,999999)
                mailer(userEmail,"chroDo signup verification",f"Your OTP for chroDo web application is {signupPin}")
                return render_template("signupVer.html",userEmail=userEmail)
    else:
        verificationMode= False
        signupPin=0
        return render_template("signup.html",userEmail="",userPassword="",confirmPassword="",userName="",sideTitle="chroDo")
    
@app.route("/edit_todo/<id>",methods=["GET","POST"])
def homeEditTodo(id):
    global todoDesc,todoTitle
    if request.method=="GET":
        objectData = data.find_one({"_id":ObjectId(id)})
        todoTitle,todoDesc=objectData["title"],objectData["desc"]
        return render_template("editTodo.html",title=todoTitle,desc=todoDesc)
    else:
        todoTitle,todoDesc=request.form["todoTitle"],request.form["todoDesc"]
        data.find_one_and_update({"_id":ObjectId(id)},{"$set":{"title":todoTitle,"desc":todoDesc}})
        # Put something inc before update
        return redirect(url_for("homePage"))

@app.route("/delete_todo/<id>")
def homeDeleteTodo(id):
    data.find_one_and_delete({"_id":ObjectId(id)})
    return redirect(url_for("homePage"))
@app.route("/logout")
def homeLogout():
    session["email"]=None
    return redirect(url_for("homePage"))

if __name__ == '__main__':
    app.run(debug=True)