import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd

baseURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"

def loadData(fileName, columnName): 
    allData = pd.read_csv(baseURL + fileName) \
                .drop(['Lat', 'Long'], axis=1) \
                .melt(id_vars=['Province/State', 'Country/Region'], var_name='date', value_name=columnName) \
                .fillna('<all>')
    allData['date'] = allData['date'].astype('datetime64[ns]')
    return allData

allData = loadData("time_series_19-covid-Confirmed.csv", "Confirmed") \
    .merge(loadData("time_series_19-covid-Deaths.csv", "Deaths")) \
    .merge(loadData("time_series_19-covid-Recovered.csv", "Recovered"))

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1('Case History of the Coronavirus (COVID-19)'),
    html.Div(className="row", children=[
        html.Div(className="four columns", children=[
            html.H5('Country'),
            dcc.Dropdown(
                id='country',
                options=[{'label': state, 'value': state} for state in ['Italy', 'US', 'Australia', 'China']],
                value='Italy'
            ),
        ]),
        html.Div(className="four columns", children=[
            html.H5('State / Province'),
            dcc.Dropdown(
                id='state'
            ),
        ]),
        html.Div(className="four columns", children=[
            html.H5('Selected Metrics'),
            dcc.Checklist(
                id='metrics',
                options = [
                    {'label': 'Confirmed', 'value': 'Confirmed'},
                    {'label': 'Deaths', 'value': 'Deaths'},
                    {'label': 'Recovered', 'value': 'Recovered'},
                ],
                value = ['Confirmed', 'Deaths']            
            )
        ])
    ]),
    dcc.Graph(
        id="plot_new_metrics"
    ),
    dcc.Graph(
        id="plot_cum_metrics"
    )
])

@app.callback(
    [Output('state', 'options'), Output('state', 'value')],
    [Input('country', 'value')]
)
def update_states(country):
    states = list(allData.loc[allData['Country/Region'] == country]['Province/State'].unique())
    states.insert(0, '<all>')
    states.sort()
    state_options = [{'label':s, 'value':s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value

def nonreactive_data(country, state):
    data = allData.loc[allData['Country/Region'] == country]
    if state == '<all>':
        data = data.drop('Province/State', axis=1).groupby("date").sum().reset_index()
    else:
        data = data.loc[data['Province/State'] == state]
    data = data.join(data.select_dtypes(include='int64').diff().add_prefix('New').fillna(0))
    return data

def barchart(data, metrics, metricPrefix=""):
    return go.Figure(data=[
        go.Bar(name=metric, x=data.date, y=data[metricPrefix + metric]) for metric in metrics
    ]).update_layout(barmode='group')

@app.callback(
    Output('plot_new_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_new_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, metricPrefix="New")

@app.callback(
    Output('plot_cum_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_cum_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, metricPrefix="")

if __name__ == '__main__':
    app.run_server(debug=True)

    