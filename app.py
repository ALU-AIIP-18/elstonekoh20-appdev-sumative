from flask import Flask,render_template,request,redirect,url_for,jsonify
from api_calls import wind_input,solar_input,read_file,sms_client,predict_power,check_maintenance,combined_power
import csv,os,dashboard
import pandas as pd


server = Flask(__name__)
app = dashboard.get_dash(server)

@app.server.route("/",methods=['GET','POST'])
def index():
    # go back to home page
    return render_template("index.html")


# Form to submit operator and powerplant details
@app.server.route("/admin")
def admin():
    # check if maintenance file has been uploaded
    if os.path.exists("maintenance.csv")==False:
        return render_template("preview.html")
    # go to admin page
    return render_template("admin.html")

# Endpoint to Dashboard
@app.server.route("/dashapp1/")
def dashapp1():
    # check if maintenance file has been uploaded
    if os.path.exists("maintenance.csv")==False:
        return render_template("preview.html")
    else:
        return redirect("/dashapp/")
   
 
#Endpoint resets application     
@app.server.route("/reset")
def reset():
    os.remove("maintenance.csv")
    os.remove("summary.csv")
    # go back to home page
    return redirect("/")
    
 #Endpoint to upload maintenace file        
@app.server.route("/store_file",methods=['POST'])
def store_file():
    file=request.files["maintenance"]
    file.save("maintenance.csv")
    
    # Obtain Meterological Data
    wind_data=wind_input(0,0)
    solar_data=solar_input(0,0)
        
    # Read Maintenance Schedule File
    wind_schedule=read_file("maintenance.csv",wind_data.index[0]) 
    solar_schedule=read_file("maintenance.csv",solar_data.index[0]) 
        
    # Power Prediction for ML model
    wind_power=predict_power('wind',wind_data)
    solar_power=predict_power('solar',solar_data)
        
    # Check maintenance file 
    final_wind=check_maintenance(wind_schedule,wind_power)
    final_solar=check_maintenance(solar_schedule,solar_power)
        
    # Combine wind and solar power
    power= combined_power(final_solar,final_wind)
    power['DateTime']=power.index
    power['DateTime'] = power['DateTime'].apply(lambda x: pd.to_datetime(str(x), format='%Y%m%d'))
    power.set_index('DateTime', inplace = True)
    power_csv=power.to_csv("summary.csv")
    # go back to home page
    return redirect("/")
    
# call back for sms summary
@app.server.route("/sms",methods=['GET','POST'])
def sms():
    # go to summary sms page
    return render_template("sms.html")

# callable to send SMS summary
@app.server.route("/send_summary",methods=['GET','POST'])
def send_summary():
    
    phone = request.args.get('phone')
    power_csv=pd.read_csv("summary.csv")
    sms_power=power_csv['output_power'].round(2)
    sms_date=power_csv['DateTime']
    status=1
    sms_client(sms_power,sms_date,status,phone)
    
    # go back to dashboard
    return redirect("/dashapp/")

# call back to save admin
@app.server.route("/send_slasms",methods=['GET','POST'])
def send_slasms():
    phone = request.args.get('phone')
    SLA = request.args.get('SLA')
    power_csv=pd.read_csv("summary.csv")
    sms=power_csv[power_csv['output_power']<=float(SLA)].round(2)
    sms_date=power_csv['DateTime']
    status=0
    sms_power=list(sms.output_power.values)
    if len(sms_power) == 0:
    # If SLA is meet don't send SMS
        pass
    else:
        # Send SMS when SLA is met
        sms_client(sms_power,sms_date,status,phone)
      
    # go back to homepage
    return redirect("/")    
    
if __name__ == '__main__':
    app.run_server(port=5001, debug=True)
