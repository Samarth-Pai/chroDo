from flask import Flask,render_template,request,session,url_for,redirect
from flask_pymongo import PyMongo,ObjectId
import smtplib,random
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "samarth@GM"
app.config["MONGO_URI"] = "mongodb+srv://vercel-admin-user-645c358d41b20904e04a539c:B8EKw7G6Drh9GRuG@cluster0.abe4k8u.mongodb.net/chroDo?retryWrites=true&w=majority"
db = PyMongo(app).db
client = db.loginData
data = db.clientData
def mailer(to,subject,msg):
    s = smtplib.SMTP("smtp.office365.com",587)
    s.starttls()
    print("Logging in...")
    s.login("samarthpai9870@hotmail.com","samarth@GM")
    print("Login successfull.")
    print("Sending email..")
    s.sendmail("samarthpai9870@hotmail.com",to,f"Subject: {subject}\n\n{msg}")
    print("Mail sent successfully")
    s.quit()

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