import abc
import datetime
import os.path
import uuid
from typing import TypedDict, IO, Union

from flask import request, abort
from webargs import fields
from webargs.flaskparser import use_args

from . import app
from .authorize_station import authorize_station
from .utils import make_thumbnail
from .repository import Observation, ObservationId, Repository, SatelliteId, StationId
from abc import abstractmethod

class WebFileLike(abc.ABC):
    @property
    @abstractmethod
    def filename(self) -> str:
        pass
    @abstractmethod
    def save(self, path: str) -> None:
        pass

class RequestArguments(TypedDict):
    file: WebFileLike
    aos: datetime.datetime
    tca: datetime.datetime
    los: datetime.datetime
    sat: str
    notes: str

cfg = app.config["database"]

@app.route('/receive', methods=["POST",])
@authorize_station
@use_args({
    'file': fields.Field(validate=lambda file: file.mimetype == "image/png", location="files"),
    'aos': fields.DateTime(required=True),
    'tca': fields.DateTime(required=True),
    'los': fields.DateTime(required=True),
    'sat': fields.Str(required=True),
    'notes': fields.Str(required=False)
})
def receive(station_id: str, args: RequestArguments):
    if len(request.files) == 0:
        abort(400, description="Missing file")

    file_ = args['file']
    filename = "%s-%s" % (str(uuid.uuid4()), file_.filename)

    repository = Repository()

    satellite = repository.read_satellite(args["sat"])
    if satellite is None:
        abort(400, description="Unknown satellite")

    sat_id = SatelliteId(satellite["sat_id"])
    observation: Observation = {
        'obs_id': ObservationId(0),
        'aos': args['aos'],
        'tca': args['tca'],
        'los': args['los'],
        'sat_id': sat_id,
        'sat_name': satellite["sat_name"],
        'filename': filename,
        'thumbfile': '',
        'notes': args.get('notes'),
        'station_id': StationId(station_id)
    }

    repository.insert_observation(observation)

    root = app.config["storage"]['image_root']
    path = os.path.join(root, filename)
    file_.save(path)
    thumb_path = os.path.join(root, "thumbs", "thumb-" + filename)
    make_thumbnail(path, thumb_path)
    return '', 204