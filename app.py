from datetime import datetime
from string import ascii_uppercase
import requests as rq
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from bs4 import BeautifulSoup as bs, element

app = Flask(__name__)
app.secret_key = '<BAD_SECRET_KEY>'
app.config['SESSION_COOKIE_NAME'] = 'AP_Dashboard_Webinput'
### Your secret key as string here. needed for https

BASE_URL = "<YOURBASE URL>" ### YOUR Base ULR/URI without "http(s)://"
GRAFANA_TOKEN = "<YOUR ACCESS TOKEN>" ### generated in your admin settings under "/org/serviceaccounts"
def dashboard_template():
  return {
  "annotations": {
      "list": [
          {
              "builtIn": 1,
              "datasource": {
                  "type": "grafana",
                  "uid": "-- Grafana --"
              },
              "enable": True,
              "hide": True,
              "iconColor": "rgba(0, 211, 255, 1)",
              "name": "Annotations & Alerts",
              "type": "dashboard"
          }
      ]
  },
  "editable": True,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": None,
  "links": [],
  "panels": [
  ],
  "preload": False,
  "refresh": "1m",
  "schemaVersion": 40,
  "tags": [],
  "templating": {
      "list": []
  },
  "time": {
      "from": "now-3h",
      "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": None,
  "uid": None,
  "version": None,
  "weekStart": ""
  }

def line_panel_template():
    ### this is a just the json template from my panels. it will create simple line-graphs with predefined querys
  return {
    "datasource": {
        "type": "grafana-postgresql-datasource",
        ### change to your desired datasource but since the crawler saves to Postgres DB this is the default
        "uid": "fedh76gb5ds00c" # uid of the datasource
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "palette-classic"
            },
            "custom": {
                "axisBorderShow": False,
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisLabel": "",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "barWidthFactor": 0.6,
                "drawStyle": "line",
                "fillOpacity": 0,
                "gradientMode": "none",
                "hideFrom": {
                    "legend": False,
                    "tooltip": False,
                    "viz": False
                },
                "insertNulls": False,
                "lineInterpolation": "linear",
                "lineWidth": 1,
                "pointSize": 5,
                "scaleDistribution": {
                    "type": "linear"
                },
                "showPoints": "auto",
                "spanNulls": True,
                "stacking": {
                    "group": "A",
                    "mode": "none"
                },
                "thresholdsStyle": {
                    "mode": "off"
                }
            },
            "mappings": [],
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {
                        "color": "green"
                    },
                    {
                        "color": "red",
                        "value": 80
                    }
                ]
          }
        },
        "overrides": []
    },
    "gridPos": {
        "h": 24,
        "w": 24,
        "x": 0,
        "y": 0
    },
    "id": 0,
    "options": {
        "legend": {
            "calcs": [],
            "displayMode": "list",
            "placement": "bottom",
            "showLegend": True
        },
        "tooltip": {
            "hideZeros": False,
            "mode": "single",
            "sort": "none"
        }
    },
    "pluginVersion": "11.5.1",
    "targets": [

    ],
    "title": "placeholder", ### placeholder text, gets replaces later on in the function
    "type": "timeseries"
}


def table_panel_template():
    ### this is a just the json template from my panels. it will create simple line-graphs with predefined querys
  return {
    "datasource": {
        "type": "grafana-postgresql-datasource",
        ### change to your desired datasource but since the crawler saves to Postgres DB this is the default
        "uid": "fedh76gb5ds00c" # uid of the datasource
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "palette-classic"
            },
            "custom": {
                "align": "auto",
                "cellOptions": {
                    "type": "auto"
                },
                "inspect": False
            },
            "mappings": [],
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {
                        "color": "green",
                        "value": 0
                    },
                    {
                        "color": "red",
                        "value": 80
                    }
                ]
          }
        },
        "overrides": []
    },
    "gridPos": {
        "h": 8,
        "w": 24,
        "x": 0,
        "y": 0
    },
    "id": 0,
    "options": {
        "cellHeight": "sm",
        "footer": {
            "countRows": False,
            "fields": "",
            "reducer": [
                "sum"
            ],
            "show": False
        },
        "showHeader": True
      },
    "pluginVersion": "11.5.1",
    "targets": [
    ],
    "title": "Base Stats",
    "type": "table"
}


def build_target(letter_index, query, url_list):
    query = query.replace('\n', '')
    if len(url_list) > 1:
        urls = f"""'{"','".join(url_list)}'"""
    else:
        urls = f"'{url_list[0]}'"
    return {
        "datasource": {
            "type": "grafana-postgresql-datasource",
            "uid": "fedh76gb5ds00c"
        },
        "editorMode": "code",
        "format": "time_series",
        "rawQuery": True,
        "rawSql": f"""{query.format(urls)}""",
        "refId": f"{ascii_uppercase[letter_index]}",
    }


# this si just to have the querys in one place and to just interate over it to create all panels in a row
panel_order = [
    (1,"SELECT\r\n  title as Title,\r\n  MAX(Timestamp)-MIN(timestamp) AS Duration,\r\n  MIN(timestamp) as Startdate,"
       "\r\n  MAX(Timestamp) as Enddate,\r\n  url as URL,\r\n  MAX(base.checks_done) as checks_done,"
       "\r\n  checks_total,\r\n  MAX(base.checks_done)/(Extract( EPOCH from MAX(Timestamp) - MIN(timestamp))/60) as "
       "Checks_per_Minute,\r\n  MAX(base.checks_done)/(Extract( EPOCH from MAX(Timestamp) - MIN(timestamp))/(60*60)) "
       "as Checks_per_Hour,\r\n  MAX(base.checks_done)/(Extract( EPOCH from MAX(Timestamp) - MIN(timestamp))/("
       "60*60*24))  as Checks_per_Day\r\nFROM\r\n  (\r\n    SELECT\r\n      stats_total.*,\r\n      "
       "trackers.title\r\n    FROM\r\n      stats_total,\r\n      trackers\r\n    Where\r\n      trackers.url in ("
       "\r\n        SELECT\r\n          URL\r\n        from\r\n          trackers\r\n        WHERE\r\n          url = {}"
       "\r\n      )\r\n      AND trackers.url = stats_total.url\r\n  ) as base\r\nGROUP BY\r\n  url,\r\n  title,"
       "\r\n  checks_total", "Base Stats"),
    (2, """SELECT name, timestamp as time, checks_done from Stats_Total WHERE name = 'Total' AND url = 
    {} ORDER BY timestamp;""", "AP total checks done"),
    (3, """SELECT games_done, timestamp as time from Stats_total WHERE url = ( SELECT url from Trackers WHERE url LIKE 
    {} ) ORDER BY timestamp;""", "AP total games finished"),
    (4, """SELECT url name, timestamp as time, percentage from Stats_total WHERE name = 'Total' AND url = {} ORDER BY 
    timestamp;""", "AP total percentage"),
    (5, """SELECT name, timestamp as time, checks_done from Stats  WHERE not name = 'Total' AND url IN ( {} ) ORDER BY 
    timestamp;""", "Per Player Stats (actual numbers)"),
    (6, """SELECT name, timestamp as time, percentage from Stats WHERE not name = 'Total' AND url IN ( {} ) ORDER BY 
    timestamp;""", "Per Player Percentage done"),
]


def create_dashboard_template(url_list):
    base_url=f"https://{BASE_URL}/api/"
    ### /api/ is needed to interact with the api endpoints
    header_json = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GRAFANA_TOKEN}',
    }
    data_json = {
        'folderUid': "behe8lwbo4mpsb",
        ### uuid of the folder you want to put your dashboard in. empty if you want it places on root level of grafana
        'message': "created new dashboard",
        'dashboard': {
        },
        'overwrite': False,
    }
    share_json = {
        'share': 'public',
        'isEnabled': True,
        "timeSelectionEnabled": True,
    } ### premark the dashboard as public and generate a public link
    dashboard = dashboard_template()
    # panel["title"] = f"(A)Sync from {datetime.today().strftime('%Y-%m-%d')}"
    for panel_index, SQL_query, name in panel_order:
        ### create panel templates with each query. if multiple links get submitted via the webinput form all links
        ### will be used applied to all dashoboard. so it's a comparison/all in one view
        if panel_index > 1:
            tmp_panel = line_panel_template()
            tmp_panel["gridPos"]["y"] = (panel_index - 1) * 24 + 8
        else:
            tmp_panel = table_panel_template()
            tmp_panel["gridPos"]["y"] = 0
        tmp_panel["id"] = panel_index
        if panel_index < 5:
            for url_index, url in enumerate(url_list):
                tmp_panel["targets"].append(build_target(url_index, SQL_query, [url]))
        else:
            tmp_panel["targets"].append(build_target(panel_index, SQL_query, url_list))
        if panel_index == 1:
            tmp_panel["targets"][0]["format"] = "table"
        tmp_panel["title"] = name
        dashboard["panels"].append(tmp_panel)
    data_json["dashboard"] = dashboard
    data_json["title"] = f"(A)Sync from {datetime.today().strftime('%Y-%m-%d')}"
    data_json["dashboard"]["title"] = f"(A)Sync from {datetime.today().strftime('%Y-%m-%d')}"
    # print(json.dumps(header_json))
    # print(json.dumps(data_json))

    response = rq.post(url=fr'{base_url}dashboards/db', headers=header_json, json=data_json)
    ### generate dashboard itself with all the panels

    # print(response, response.json())
    dashboard_uid = response.json()['uid']
    share_dashboard = rq.post(url=rf'{base_url}dashboards/uid/'
                                  rf'{dashboard_uid}/public-dashboards', headers=header_json, json=share_json) #make
    ### dashboard public and get accesstoken in return to build public link
    shared_dashboard_accesstoken = share_dashboard.json()['accessToken']

    # print(f"accesstoken: + {shared_dashboard_accesstoken}")
    public_url = f"https://{BASE_URL}/public-dashboards/{shared_dashboard_accesstoken}"
    return public_url

def delete_dashboard(url:str):
    base_url=f"https://{BASE_URL}/api/"
    header_json = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GRAFANA_TOKEN}',
    }
    accesstoken = url.split('/')[-1]
    if accesstoken.find('?') > 0:
        accesstoken = accesstoken[:accesstoken.find('?') + 1 ]
    public_dashboards = rq.get(url=fr'{base_url}dashboards/public-dashboards', headers=header_json).json()
    for dashboard in public_dashboards['publicDashboards']:
        if dashboard['accessToken'] == accesstoken:
            response = rq.delete(url=fr'{base_url}dashboards/uid/{dashboard["dashboardUid"]}', headers=header_json)
    return redirect(url_for('index'))


@app.route("/webinput/", methods=['GET', 'POST', 'UPDATE'])
def index():
    cookie_set = request.cookies.get('old_dashboards') or ""
    dashboard_link = ""
    added_list = list()
    invalid_links = list()

    if request.args.get('row_update'):
        increment = int(request.args.get('increment'))
        if session['rows'] + increment > 0:
            session['rows'] = session['rows'] + int(increment)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))

    if not 'rows' in session.keys() or not isinstance(session['rows'], int):
        session['rows'] = 1
    if request.method == 'POST':
        create_dashboard = request.form.get('create_dashboard')
        add_links = request.form.get('add_links')
        user_input = set(request.form.getlist('tracker_urls'))
        delete_dashboard_link = request.form.get('delete_old_dashboard')

        # with open(r'~/Grafana/AP-Crawler/new_trackers.txt', 'a') as new_tracker_file:
        with open(r'H:\AP-crawler/new_trackers.txt', 'a') as new_tracker_file:
            ### the main AP-Crawler script uses this textfile so i also just append it here
            for link in user_input:
                try:
                    if any(word in link for word in ['/tracker/', '/room/']):
                        if "/room/" in link:
                            room_page = rq.get(url=link)

                            room_html = bs(room_page.text, 'html.parser')
                            room_info = room_html.find("span", id="host-room-info").contents
                            link = f"{link.split('/room/')[0]}{room_info[1].get('href')}"
                        new_tracker_file.writelines(link + '\n')
                        session['rows'] = 1
                        added_list.append(link)
                        # return render_template('index.html', rows=range(rows))
                    else:
                        invalid_links.append(link)
                        # pass
                except:
                    pass
        if create_dashboard:
            dashboard_link = create_dashboard_template(added_list)
            if dashboard_link not in cookie_set:
                cookie_set = ";;".join([*cookie_set.split(";;"), dashboard_link])
        if delete_dashboard_link:
            for link in user_input:
                if f'{BASE_URL}/public-dashboards/' in link:
                    cookie_set = cookie_set.replace(f";;{link}'", "")
                    delete_dashboard(link)
    old_dashboards = cookie_set.split(';;')[1:] or list()
    response = make_response(render_template('index.html', rows=range(session['rows']), added_links_list=added_list,
                                             invalid_links_list=invalid_links, dashboard_link=dashboard_link,
                                             old_dashboards=old_dashboards))
    if not cookie_set:
        response.set_cookie('old_dashboards', "")
    else:
        response.set_cookie('old_dashboards', cookie_set)
    return response
    # else:
    #     return render_template('index.html', rows=range(session['rows']))


@app.route("/webinput/clear/", methods=['GET', 'POST'])
def clear():
    session.clear()
    return make_response(redirect(url_for('index')))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False, port=5555)
