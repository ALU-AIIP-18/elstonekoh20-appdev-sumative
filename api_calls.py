import pandas as pd
from twilio.rest import Client
import requests
import pickle
import csv

# Calls API to get windfarm meterological data
def wind_input(wind_lat,wind_lon):
    
    latitude =  8.598084
    longitude = 53.556563
    url = ("http://www.7timer.info/bin/meteo.php?lon=" + str(longitude) + "&lat=" + str(latitude)+"&ac=0&unit=metric&output=json&tzshift=0")

    response = requests.get(url)
    data = response.json()
    data_size = len(data["dataseries"])
    wind_speed=[]
    wind_direction=[]
    
    # Converts class of wind speed in 7timer to values sutiable for model. Averge value of class is used
    wind_value={"1":0.3,'2':1.85,'3':5.7,'4':9.4,'5':14,'6':20.85,'7':28.55,'8':34.65,'9':39.05,'10':43.8,'11':48.55,'12':53.4,'13':55.9}
    for j in range(8):
        dates=get_dates(data["init"])
    for i in range(data_size):
        speed=data["dataseries"][i][ "wind10m"]['speed']
        wind_speed.append(float(wind_value[str(speed)]))
        wind_direction.append(float(data["dataseries"][i][ "wind10m"]['direction']))
    wind_data = {'dates':dates,
                 'wind_speed': [sum(wind_speed[0:8])/4,sum(wind_speed[8:16])/4,sum(wind_speed[16:24])/4,sum(wind_speed[24:32])/4,
                                sum(wind_speed[32:40])/4,sum(wind_speed[40:48])/4,sum(wind_speed[48:56])/4,sum(wind_speed[56:64])/4],
                 'wind_direction':[sum(wind_direction[0:8])/4,sum(wind_direction[8:16])/4,sum(wind_direction[16:24])/4,sum(wind_direction[24:32])/4,
                                   sum(wind_direction[32:40])/4,sum(wind_direction[40:48])/4,sum(wind_direction[48:56])/4,sum(wind_direction[56:64])/4]
                 }
    wind_data=pd.DataFrame.from_dict(wind_data)
    wind_data.set_index("dates", inplace = True)
    return wind_data

# Calls API to get solar farm meterological data   
def solar_input(solar_lat,solar_lon):
    latitude  =   -19.461907
    longitude =    142.110216

    url = ("http://www.7timer.info/bin/meteo.php?lon=" + str(longitude) + "&lat=" + str(latitude)+"&ac=0&unit=metric&output=json&tzshift=0")

    response = requests.get(url)

    data = response.json()
    
    data_size = len(data["dataseries"])
    solar_temp=[]
    cover=[]
    precip=[]
    
    for j in range(8):
        #dates.append(int(data["init"][0:8])+j)
        dates=get_dates(data["init"])
        
    for i in range(data_size):
        solar_temp.append((float(data["dataseries"][i][ "temp2m"])* 9/5) + 32 )
        cover.append(float(data["dataseries"][i][ "cloudcover"]))
        precip.append(float(data["dataseries"][i][ "prec_amount"]))
    solar_data = {'dates':dates,
                 'temp_hi': [max(solar_temp[0:8]),max(solar_temp[8:16]),max(solar_temp[16:24]),max(solar_temp[24:32]),
                             max(solar_temp[32:40]),max(solar_temp[40:48]),max(solar_temp[48:56]),max(solar_temp[56:64])], 
                 'temp_lo': [min(solar_temp[0:8]),min(solar_temp[8:16]),min(solar_temp[16:24]),min(solar_temp[24:32]),
                             min(solar_temp[32:40]),min(solar_temp[40:48]),min(solar_temp[48:56]),min(solar_temp[56:64])],
                 'cover':   [max(cover[0:8]),max(cover[8:16]),max(cover[16:24]),max(cover[24:32]),
                             max(cover[32:40]),max(cover[40:48]),max(cover[48:56]),max(cover[56:64])],
                 'precip':  [min(precip[0:8]),min(precip[8:16]),min(precip[16:24]),min(precip[24:32]),
                             min(precip[32:40]),min(precip[40:48]),min(precip[48:56]),min(precip[56:64])]
                 }
    solar_data=pd.DataFrame.from_dict(solar_data)
    solar_data.set_index("dates", inplace = True)
    return solar_data

# Reads csvfile
def read_file(filename,dates):
    with open(filename) as wfile:
        reader = csv.reader(wfile)
        data={}
        data1={}
        dates=str(dates)[0:6]
        for line in reader:
            if type(line[1])==str and len(line[1])>0:
                if len(line[1])>4:
                    pass
                else:
                    if len(line[0])==1:
                        data[dates+"0"+line[0]]=float(line[1])
                    else:
                        data[dates+line[0]]=float(line[1])
        

        for key in data:
            if len(str(int(key[4:6])+1))==1:
                data1[key[0:4]+"0"+str(int(key[4:6])+1)+key[6:8]]=data[key]
            else:
                if int(key[4:6])+1==12:
                    data1[key[0:4]+"01"+key[6:8]]=data[key]
                else:
                    data1[key[0:4]+str(int(key[4:6])+1)+key[6:8]]=data[key]
        data.update(data1)
    return data
    

# Loads saved machine learning model
def predict_power(model,data):
    model = pickle.load(open('ml_model/'+str(model)+'_model.sav', 'rb'))
    power={}
    ml_result=model.predict(data.values)
    date= data.index.values   
    for i in list(range(len(date))):
        power[str(date[i])]=float(ml_result[i])
    return power

# Checks if power are scheduled for maintenance and adjust power
def check_maintenance(schedule,power): 
    for key in schedule:
        if key in power:
            power[key]=power.get(key)*(1-schedule.get(key)/100)
        else:
            pass
    return power  
 
# Combines power output from wind and solar farm 
def combined_power(final_solar,final_wind):
    total={}
    output_power={}
    solar_power=final_solar
    wind_power=final_wind
    for key in solar_power:
        total[key]=solar_power[key]+wind_power[key]
        output_power[key]=[solar_power[key],wind_power[key],total[key]]
    return pd.DataFrame.from_dict(output_power, orient='index',columns=['solar_power', 'wind_power', 'output_power'])

# Module to send sms with Twilio 
def sms_client(sms_power,sms_date):
    account = "ACd5f2964264997275a58388ea0cacb8d0"
    token = "45477273b7f46189e888cf8cc88e5c36"
    client = Client(account, token)
    power=""
    date=""
    for i in range(len(sms_power)):
        if power=="":
            power=power+str(sms_power[i])
            date=date+str(sms_date[i]) 
        else:
            power=power+"\n"+str(sms_power[i])
            date=date+"\n"+str(sms_date[i])
            
    message = client.messages.create(to="+2347030361587", from_="+12025590186",
                                 body="Hello,\n" + "Predicted power for these/this date(s)is lesser than agreed SLA.\n" + date + "\nThank You")
    return

# Manipulate Dates
def get_dates(date_value):
    dates=[]
    for j in range(8):   
        if j==0:
            dates.append(int(date_value[0:8])+j)
        
        # Date Manipulation of Leap Years
        if j !=0:
            if int(str(dates[-1])[0:4])%4==0:
                
                #Manipulations for the months of Apr, Jun, Sept and Nov
                if int(str(dates[-1])[4:6]) in [4,6,9,11]:
                    if int(str(dates[-1])[6:8])>29:
                        month=str(int(str(dates[-1])[4:6])+1)
                        
                        # Specific to single digit month(Apr,Jun,Sept)
                        if len(month)==1:
                            month="0"+month
                        dates.append(int(str(dates[-1])[0:4]+month+"01"))
                    else:
                        dates.append(dates[-1]+1)
                
                #Manipulations for the months of Jan, Mar, May,Jul,August,Oct,Dec
                elif int(str(dates[-1])[4:6]) in [1,3,5,7,8,10,12]:
                    if int(str(dates[-1])[6:8])>30:
                        month=str(int(str(dates[-1])[4:6])+1)
                        
                        # Specific to single digit month(Jan,Mar,May,Jul,Aug)
                        if len(month)==1:
                            month="0"+month
                            
                        # Specific to Dec
                        if month=="13":
                            dates.append(int(str(int(str(dates[-1])[0:4])+1)+"01"+"01"))
                        else:
                            dates.append(int(str(dates[-1])[0:4]+month+"01"))
                    else:
                        dates.append(dates[-1]+1)
                        
                # Manipulations for Feb
                else:
                    if int(str(dates[-1])[6:8])>28:
                        dates.append(int(str(dates[-1])[0:4]+str(int(str(dates[-1])[4:6])+1)+"01"))
                    else:
                        dates.append(dates[-1]+1)
                        
            # Date Manipulation of Non Leap Years
            if int(str(dates[-1])[0:4])%4!=0:
                
                #Manipulations for the months of Apr, Jun, Sept and Nov
                if int(str(dates[-1])[4:6]) in [4,6,9,11]:
                    if int(str(dates[-1])[6:8])>29:
                        month=str(int(str(dates[-1])[4:6])+1)
                        
                        # Specific to single digit month(Apr,Jun,Sept)
                        if len(month)==1:
                            month="0"+month
                        dates.append(int(str(dates[-1])[0:4]+month+"01"))
                    else:
                        dates.append(dates[-1]+1)
                
                #Manipulations for the months of Jan, Mar, May,Jul,August,Oct,Dec
                elif int(str(dates[-1])[4:6]) in [1,3,5,7,8,10,12]:
                    if int(str(dates[-1])[6:8])>30:
                        month=str(int(str(dates[-1])[4:6])+1)
                        
                        # Specific to single digit month(Jan,Mar,May,Jul,Aug)
                        if len(month)==1:
                            month="0"+month
                        
                        # Specific to Dec
                        if month=="13":
                            dates.append(int(str(int(str(dates[-1])[0:4])+1)+"01"+"01"))
                        else:
                            dates.append(int(str(dates[-1])[0:4]+month+"01"))
                    else:
                        dates.append(dates[-1]+1)
                
                # Manipulations for Feb
                else:
                    if int(str(dates[-1])[6:8])>27:
                        dates.append(int(str(dates[-1])[0:4]+str(int(str(dates[-1])[4:6])+1)+"01"))
                    else:
                        dates.append(dates[-1]+1)
    return dates