import random
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.H1(children='Hello World!', id='first'),
    dcc.Interval(id='timer', interval=1000),
    html.Div(id='dummy'),
    dcc.Graph(
            id='example-graph',
            figure={
                'data': [
                    {'x': [1, 2, 3],
                     'y': [4, 1, 2],
                     'type': 'bar', 'name': 'SF'},
                    {'x': [1, 2, 3],
                     'y': [2, 4, 5],
                     'type': 'bar', 'name': 'Montréal'},
                ],
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }
        )
])

@app.callback(output=Output('example-graph', 'figure'),
              inputs=[Input('timer', 'n_intervals')])
def update_graph(n_clicks):
    return {
                'data': [
                    {'x': [1, 2, 3],
                     'y': [random.randint(0, 10) for x in range(3)],
                     'type': 'bar', 'name': 'SF'},
                    {'x': [1, 2, 3],
                     'y': [random.randint(0, 10) for x in range(3)],
                     'type': 'bar', 'name': 'Montréal'},
                ],
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }


if __name__ == '__main__':
    app.run_server(debug=True)