# Dependencies
import numpy as np
from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
import os


# relative path to databse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "Resources", "hawaii.sqlite")

# set up sqlite connection objects
engine = create_engine(f"sqlite:///{db_path}")
base = automap_base()
base.prepare(engine,reflect=True)
measurement = base.classes.measurement
station = base.classes.station


# set up flask
app = Flask(__name__)

# get query terms for later
initial_session = Session(engine)
last_date = initial_session.query(func.max(measurement.date)).scalar()
first_date = dt.datetime.strptime(last_date, '%Y-%m-%d').date()
first_date = first_date.replace(year=first_date.year - 1)
first_date = first_date.strftime('%Y-%m-%d')
most_active = (
    initial_session
    .query(measurement.station, func.count(measurement.id,))
    .group_by(measurement.station)
    .order_by(func.count(measurement.id).desc())
    .all()
)
most_active_id = most_active[0][0]
initial_session.close()



# flask routes
@app.route("/")
def homepage():
    return"""
<h1> Hawaii Weather Station API </h1>
<h2> Available endpoints: </h2>
<ul>
    <li><code><a href = "/api/v1.0/precipitation">/api/v1.0/precipitation</a></code> - returns consolidated precipitation data</li>
    <li><code><a href = "/api/v1.0/stations">/api/v1.0/stations</a></code> - returns a list of weather stations</li>
    <li><code><a href = "/api/v1.0/tobs">/api/v1.0/tobs</a></code> - returns temperature observations from the prior year</li>
    <li><code><a href = "/api/v1.0/2017-08-10">/api/v1.0/$start</a></code> - returns temperature min, mean, and max for all dates after <code>$start</code></li>
    <li><code><a href = "/api/v1.0/2017-08-10/2017-08-20">/api/v1.0/$start/$end</a></code> - returns temperature min, mean, and max for all dates between <code>$start</code> and <code>$end</code></li>
    <li><i>(please supply dates in ISO 8601 format, i.e. '2017-08-10')</i></li>
</ul>
          """



@app.route("/api/v1.0/precipitation")
def precipitation():

    session = Session(engine)

    response = (
        session
        .query(measurement.date, measurement.prcp)
        .filter(measurement.date >= first_date)
        .all()
    )

    precipitation_dict = [{"date": date, "prcp": prcp} for date, prcp in response]

    session.close()

    return jsonify(precipitation_dict)



@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)

    results = session.query(station).all()

    results_dictionary = []
    for row in results:
        row_subdict = {
            "station": row.station,
            "name": row.name,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "elevation": row.elevation
        }
        results_dictionary.append(row_subdict)

    session.close()

    return jsonify(results_dictionary)



@app.route("/api/v1.0/tobs")
def tobs():

    session = Session(engine)

    results = (
        session
        .query(measurement.date, measurement.tobs)
        .filter(measurement.date >= first_date)
        .filter(measurement.station == most_active_id)
        .all()
    )

    results_dictionary = []
    for row in results:
        row_subdict = {
            "date": row.date,
            "tobs": row.tobs
        }
        results_dictionary.append(row_subdict)

    session.close()

    return jsonify(results_dictionary)



@app.route("/api/v1.0/<start>")
def get_temp_from(start):

    session = Session(engine)

    results = (
        session
        .query(
            func.min(measurement.tobs),
            func.avg(measurement.tobs),
            func.max(measurement.tobs)
            )
        .filter(measurement.date >= start)
        .all()
    )

    session.close()

    results_list = list(np.ravel(results))

    return jsonify(results_list)



@app.route("/api/v1.0/<start>/<end>")
def get_temp_from_to(start,end):

    session = Session(engine)

    results = (
        session
        .query(
            func.min(measurement.tobs),
            func.avg(measurement.tobs),
            func.max(measurement.tobs)
            )
        .filter(measurement.date >= start)
        .filter(measurement.date <= end)
        .all()
    )

    session.close()

    results_list = list(np.ravel(results))

    return jsonify(results_list)



# run as flask app if executed as primary process
if __name__ == '__main__':
    app.run(debug=True)