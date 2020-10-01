from flask import Flask,render_template,request,redirect,url_for,jsonify
from api_calls import wind_input,solar_input,read_file
import pandas as pd
import csv
import dashboard


server = Flask(__name__)
app = dashboard.get_dash(server)

@app.server.route("/",methods=['GET','POST'])
def index():
    # go back to home pageS
    return render_template("index.html")


@app.server.route("/admin")
def admin():
    print("call back used.")

    # go back to home page
    return render_template("admin.html")
    
@app.server.route("/submit_data",methods=['POST'])
def submit_data():
    print("call back used.")

    # go back to home page
    return redirect("/")
    
@app.server.route("/reset")
def call_back_1():
    print("call back used.")

    # go back to home page
    return redirect("/")
    
    
@app.server.route("/store_file",methods=['POST'])
def store_file():
    file_solar=request.files["solar"]
    file_solar.save("maintenance_solar.csv")
    
    file_wind=request.files["wind"]
    file_wind.save("maintenance_wind.csv")
    # go back to home page
    return redirect("/")

@app.server.route("/preview")
def preview():
    solar_schedule=read_file("maintenance_solar.csv")
    wind_schedule=read_file("maintenance_wind.csv")  
    return render_template("preview.html",solar_schedule=solar_schedule,wind_schedule=wind_schedule)

if __name__ == '__main__':
    app.run_server(port=5001, debug=True)
