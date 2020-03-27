import abc
import datetime
import os.path
import uuid
from typing import IO, Union

from flask import request, abort
from webargs import fields
from webargs.flaskparser import use_args

from . import app
from .authorize_station import authorize_station
from .utils import make_thumbnail
from .repository import Observation, ObservationFile, ObservationFileId, ObservationId, Repository, SatelliteId, StationId
from abc import abstractmethod

import sys
if sys.version_info[0] == 3 and sys.version_info[1] >= 8:
    from typing import TypedDict, Literal
else:
    from typing_extensions import TypedDict, Literal

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
    thumb_filename = "thumb-" + filename

    repository = Repository()
    with repository.transaction() as transaction:
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
            'thumbnail': thumb_filename,
            'notes': args.get('notes'),
            'station_id': StationId(station_id)
        }

        obs_id = repository.insert_observation(observation)
        observation_file: ObservationFile = {
            "obs_file_id": ObservationFileId(0),
            "filename": filename,
            "media_type": "image/png",
            "obs_id": obs_id
        }
        repository.insert_observation_file(observation_file)
        transaction.commit()

    root = app.config["storage"]['image_root']
    path = os.path.join(root, filename)
    file_.save(path)
    thumb_path = os.path.join(root, "thumbs", thumb_filename)
    make_thumbnail(path, thumb_path)
    return '', 204
