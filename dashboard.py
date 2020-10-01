import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from api_calls import wind_input,solar_input,read_file,predict_power,check_maintenance,combined_power,sms_client
import pandas as pd
import pickle

def get_dash(server):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, 
                    server=server,
                    routes_pathname_prefix='/dashapp/',
                    external_stylesheets=external_stylesheets
                    )

    df = get_data()
    
    df_index=pd.to_datetime(df.index)
    styles = get_styles()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_index, y=df["solar_power"],
                    mode='lines+markers',
                    name='Solar Power'))
    fig.add_trace(go.Scatter(x=df_index, y=df["wind_power"],
                    mode='lines+markers',
                    name='Wind Power'))
    fig.add_trace(go.Scatter(x=df_index, y=df["output_power"],
                    mode='lines+markers', 
                    name='Total Power'))
    fig.update_layout(title={'text': "7-DAYS POWER FORECAST",
                                   'y':0.9,
                                   'x':0.5,
                                   'xanchor': 'center',
                                   'yanchor': 'top'},
                      xaxis_title="DATE",
                      yaxis_title="POWER(MW)",
                      font=dict(family="Courier New, monospace",
                                size=18,
                                color="RebeccaPurple",
                                ),
                       legend=dict(orientation="h",
                                   yanchor="bottom",
                                   y=1.02,
                                   xanchor="right",
                                   x=1)
                       )
    
    app.layout = html.Div([
        # html.H6("Change the value in the text box to see callbacks in action!"),
        html.A("HOME", href="/", style=styles["button_styles"]),
        html.A("SEND SMS", href="/", style=styles["button_styles"]),
        html.Div("AppDev Power Plant Dashboard", id='my-output',
                 style=styles["text_styles"]),
        html.Div(children=[
        html.Div(
            dcc.Graph(
                id='Today',
                figure=go.Figure(go.Indicator(
                                                mode = "gauge+number",
                                                value = df.loc[df.index[0]]['output_power'],
                                                domain = {'x': [0, 1], 'y': [0, 1]},
                                                title = {'text': str(df_index[0])[0:10],'font': {'size': 24}},
                                                gauge = {'axis': {'range': [None, 60]},
                                                         'steps' : [
                                                        {'range': [0, 4], 'color': "red"},
                                                        {'range': [4, 60], 'color': "gray"}],
                                                        'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 490}})           
                                                )),
            style=styles["fig_style"]
        ),
        html.Div(
            dcc.Graph(
                id='Tommorrow',
                figure=go.Figure(go.Indicator(
                                                mode = "gauge+number",
                                                value = df.loc[df.index[1]]['output_power'],
                                                domain = {'x': [0, 1], 'y': [0, 1]},
                                                title = {'text': str(df_index[1])[0:10],'font': {'size': 24}},
                                                                                                gauge = {'axis': {'range': [None, 60]},
                                                         'steps' : [
                                                        {'range': [0, 4], 'color': "red"},
                                                        {'range': [4, 60], 'color': "gray"}],
                                                        'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 490}})
                                               )),
            style=styles["fig_style"]
        ),
        html.Div(
            dcc.Graph(
                id='nextommorrow',
                figure=go.Figure(go.Indicator(
                                                mode = "gauge+number",
                                                value = df.loc[df.index[2]]['output_power'],
                                                domain = {'x': [0, 1], 'y': [0, 1]},
                                                title = {'text':str(df_index[2])[0:10],'font': {'size': 24}},
                                                gauge = {'axis': {'range': [None, 60]},
                                                         'steps' : [
                                                        {'range': [0, 4], 'color': "red"},
                                                        {'range': [4, 60], 'color': "gray"}],
                                                        'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 490}})
                                               )),
            style=styles["fig_style"]
        ),
        html.Div(
            dcc.Graph(
                id='the day after',
                figure=go.Figure(go.Indicator(
                                                mode = "gauge+number",
                                                value = df.loc[df.index[3]]['output_power'],
                                                domain = {'x': [0, 1], 'y': [0, 1]},
                                                title = {'text':str(df_index[3])[0:10],'font': {'size': 24}},
                                                gauge = {'axis': {'range': [None, 60]},
                                                         'steps' : [
                                                        {'range': [0, 4], 'color': "red"},
                                                        {'range': [4, 60], 'color': "gray"}],
                                                        'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 490}})
                                               )),                                       
            style=styles["fig_style"]
        )
    ],style={"display":"flex","width":"98%","height":"50%",'padding':5}),
    html.Div(
            dcc.Graph(
                id='the day',
                figure=fig
            ),
            style={"width":"97%","margin": "auto","border": "1px solid #ddd"}
        )])

    return app


def get_data():
        
        if os.path.exists("maintenance_wind.csv")==False:
            df=pd.DataFrame(columns=['Date of Month;','Capacity Available as %'])
            df.to_csv("maintenance_wind.csv")
            df.to_csv("maintenance_solar.csv")
        else:
            pass
        wind_data=wind_input(0,0)
        wind_schedule=read_file("maintenance_wind.csv",wind_data.index[0]) 
        wind_power=predict_power('wind',wind_data)
        final_wind=check_maintenance(wind_schedule,wind_power)



        solar_data=solar_input(0,0)
        solar_schedule=read_file("maintenance_solar.csv",solar_data.index[0])
        solar_power=predict_power('solar',solar_data)
        final_solar=check_maintenance(solar_schedule,solar_power)
        power= combined_power(final_solar,final_wind)
        sms=power[power['output_power']<=2]
        sms_date=list(sms.index.values)
        sms_power=list(sms.output_power.values)
        if len(sms_power) == 0:
            pass
        else:
            sms_client(sms_power,sms_date)
        return power


def get_styles():
    """
    Very good for making the thing beautiful.
    """
    base_styles = {
        "text-align": "center",
        "border": "1px solid #ddd",
        "padding": "7px",
        "border-radius": "2px",
    }
    text_styles = {
        "background-color": "#eee",
        "margin": "auto",
        "width": "50%"
    }
    text_styles.update(base_styles)

    button_styles = {
        "text-decoration": "none",
    }
    button_styles.update(base_styles)

    fig_style = {
        "padding": "2px",
        "width": "24%",
        "margin": "auto",
        "display":"inline-block"
    }
    fig_style.update(base_styles)
    return {
        "text_styles" : text_styles,
        "base_styles" : base_styles,
        "button_styles" : button_styles,
        "fig_style": fig_style,
    }
   
