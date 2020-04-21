import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
from datetime import datetime
from os.path import isfile

baseURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
fileNamePickle = "allData.pkl"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

tickFont = {'size':12, 'color':"rgb(30,30,30)", 'family':"Courier New, monospace"}

def loadData_GLOB(fileName, columnName): 
    agg_dict = { columnName:sum, 'Lat':np.median, 'Long':np.median }
    data = pd.read_csv(baseURL + fileName) \
             .rename(columns={ 'Country/Region':'Country' }) \
             .melt(id_vars=['Country', 'Province/State', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')
    ## Extract chinese provinces separately.
    data_CHI = data[data.Country == 'China']
    data = data.groupby(['Country', 'date']).agg(agg_dict).reset_index()
    data['Province/State'] = '<all>'
    return pd.concat([data, data_CHI])

def loadData_US(fileName, columnName): 
    id_vars=['Country', 'Province/State', 'Lat', 'Long']
    agg_dict = { columnName:sum, 'Lat':np.median, 'Long':np.median }
    data = data = pd.read_csv(baseURL + fileName).iloc[:, 6:]
    if 'Population' in data.columns:
        data = data.drop('Population', axis=1)
    data = data \
             .drop('Combined_Key', axis=1) \
             .rename(columns={ 'Country_Region':'Country', 'Province_State':'Province/State', 'Long_':'Long' }) \
             .melt(id_vars=id_vars, var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore') \
             .groupby(['Country', 'Province/State', 'date']).agg(agg_dict).reset_index()
    return data

def refreshData():
    data_GLOB = loadData_GLOB("time_series_covid19_confirmed_global.csv", "CumConfirmed") \
        .merge(loadData_GLOB("time_series_covid19_deaths_global.csv", "CumDeaths"))
    data_US = loadData_US("time_series_covid19_confirmed_US.csv", "CumConfirmed") \
        .merge(loadData_US("time_series_covid19_deaths_US.csv", "CumDeaths"))
    data = pd.concat([data_GLOB, data_US])
    data.to_pickle(fileNamePickle)
    return data

def allData():
    if not isfile(fileNamePickle):
        refreshData()
    allData = pd.read_pickle(fileNamePickle)
    return allData

countries = allData()['Country'].unique()
countries.sort()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

## App title, keywords and tracking tag (optional).
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-161733256-2"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'UA-161733256-2');
        </script>
        <meta name="keywords" content="COVID-19,Coronavirus,Dash,Python,Dashboard,Cases,Statistics">
        <title>COVID-19 Case History</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
       </footer>
    </body>
</html>"""

app.layout = html.Div(
    style={ 'font-family':"Courier New, monospace" },
    children=[
        html.H1('Case History of the Coronavirus (COVID-19)'),
        html.Div(className="row", children=[
            html.Div(className="four columns", children=[
                html.H5('Country'),
                dcc.Dropdown(
                    id='country',
                    options=[{'label':c, 'value':c} for c in countries],
                    value='Italy'
                )
            ]),
            html.Div(className="four columns", children=[
                html.H5('State / Province'),
                dcc.Dropdown(
                    id='state'
                )
            ]),
            html.Div(className="four columns", children=[
                html.H5('Selected Metrics'),
                dcc.Checklist(
                    id='metrics',
                    options=[{'label':m, 'value':m} for m in ['Confirmed', 'Deaths', 'Recovered']],
                    value=['Confirmed', 'Deaths']
                )
            ])
        ]),
        dcc.Graph(
            id="plot_new_metrics",
            config={ 'displayModeBar': False }
        ),
        dcc.Graph(
            id="plot_cum_metrics",
            config={ 'displayModeBar': False }
        ),
        dcc.Interval(
            id='interval-component',
            interval=3600*1000, # Refresh data each hour.
            n_intervals=0
        )
    ]
)

@app.callback(
    [Output('state', 'options'), Output('state', 'value')],
    [Input('country', 'value')]
)
def update_states(country):
    d = allData()
    states = list(d.loc[d['Country'] == country]['Province/State'].unique())
    states.insert(0, '<all>')
    states.sort()
    state_options = [{'label':s, 'value':s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value

def filtered_data(country, state):
    d = allData()
    data = d.loc[d['Country'] == country].drop('Country', axis=1)
    if state == '<all>':
        data = data.drop('Province/State', axis=1).groupby("date").sum().reset_index()
    else:
        data = data.loc[data['Province/State'] == state]
    newCases = data.select_dtypes(include='Int64').diff().fillna(0)
    newCases.columns = [column.replace('Cum', 'New') for column in newCases.columns]
    data = data.join(newCases)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data

def barchart(data, metrics, prefix="", yaxisTitle=""):
    figure = go.Figure(data=[
        go.Bar( 
            name=metric, x=data.date, y=data[prefix + metric],
            marker_line_color='rgb(0,0,0)', marker_line_width=1,
            marker_color={ 'Deaths':'rgb(200,30,30)', 'Recovered':'rgb(30,200,30)', 'Confirmed':'rgb(100,140,240)'}[metric]
        ) for metric in metrics
    ])
    figure.update_layout( 
              barmode='group', legend=dict(x=.05, y=0.95, font={'size':15}, bgcolor='rgba(240,240,240,0.5)'), 
              plot_bgcolor='#FFFFFF', font=tickFont) \
          .update_xaxes( 
              title="", tickangle=-90, type='category', showgrid=True, gridcolor='#DDDDDD', 
              tickfont=tickFont, ticktext=data.dateStr, tickvals=data.date) \
          .update_yaxes(
              title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD')
    return figure

@app.callback(
    [Output('plot_new_metrics', 'figure'), Output('plot_cum_metrics', 'figure')], 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value'), Input('interval-component', 'n_intervals')]
)
def update_plots(country, state, metrics, n):
    refreshData()
    data = filtered_data(country, state)
    barchart_new = barchart(data, metrics, prefix="New", yaxisTitle="New Cases per Day")
    barchart_cum = barchart(data, metrics, prefix="Cum", yaxisTitle="Cumulated Cases")
    return barchart_new, barchart_cum

server = app.server

if __name__ == '__main__':
    app.run_server(host="0.0.0.0")
