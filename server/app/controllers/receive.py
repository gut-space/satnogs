import abc
from abc import abstractmethod
import datetime
import os.path
import shutil
import sys
from typing import Dict, List, Optional, Tuple
import uuid

from flask import request, abort
from webargs import fields, validate
from webargs.flaskparser import use_args
from werkzeug.utils import secure_filename

from app import app
from app import tle_diagrams
from app.authorize_station import authorize_station
from app.utils import make_thumbnail, first, save_binary_stream_to_file
from app.repository import Observation, ObservationFile, ObservationFileId, ObservationId, Repository, SatelliteId, Station, StationId

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

class WebFileLike(abc.ABC):
    '''Class for type-checking the file-like object from request'''
    @property
    @abstractmethod
    def filename(self) -> str:
        pass
    @property
    @abstractmethod
    def mimetype(self) -> str:
        pass
    @abstractmethod
    def save(self, path: str) -> None:
        pass

class RequestArguments(TypedDict):
    aos: datetime.datetime
    tca: datetime.datetime
    los: datetime.datetime
    sat: str
    notes: Optional[str]
    tle: Optional[List[str]]

ALLOWED_FILE_TYPES = {
    "image/png": ".png"
}

get_extension = lambda p: os.path.splitext(p)[1]
is_allowed_file = lambda f: f.mimetype in ALLOWED_FILE_TYPES and \
                            ALLOWED_FILE_TYPES[f.mimetype] == get_extension(f.filename)

@app.route('/receive', methods=["POST",])
@authorize_station
@use_args({
    'aos': fields.DateTime(required=True),
    'tca': fields.DateTime(required=True),
    'los': fields.DateTime(required=True),
    'sat': fields.Str(required=True),
    'notes': fields.Str(required=False),
    'tle': fields.List(fields.Str, required=False,
        validate=[
            # TLE must contains exact two lines
            validate.Length(equal=2, error="Require 2 line TLE. Actual: {input}"),
            # TLE lines may be ended with trailling character
            lambda tle: validate.Length(min=69, max=70,
                error="First TLE line length expected {min}-{max}. Actual: {input}")
                (tle[0]),
            lambda tle: validate.Length(min=69, max=70,
                error="Second TLE line length expected {min}-{max}. Actual: {input}")
                (tle[1]),
        ])
})
def receive(station_id: str, args: RequestArguments):
    '''
    Receive observation from station.

    Station must be authenticated.

    Request must have attached at least one imagery file. We accept only files
    with MIME-type and extension listed in @ALLOWED_FILE_TYPES dictionary.

    From first imagery file we create a thumbnail. Files are sorted using HTTP
    request keys.

    Request data are stored in DB. Binary files are saved in filesystem with
    unique, conflict-safe filename.

    Satellite assigned to observation must exists in database.
    '''
    files: Dict[str, WebFileLike] = request.files

    if len(files) == 0:
        abort(400, description="Missing file")

    # Filter files and create safe filenames
    uid = str(uuid.uuid4())
    items = enumerate(sorted(files.items(), key=lambda e: e[0]))
    file_entries: List[Tuple[str, WebFileLike]] = []
    for idx, (_, file_) in items:
        if not is_allowed_file(file_):
            continue
        org_filename = secure_filename(file_.filename)
        filename = "%s-%d-%s" % (uid, idx, org_filename)
        file_entries.append((filename, file_))

    # Select thumbnail source file
    thumbnail_source_entry = first(lambda f: f[1].mimetype.startswith("image/"), file_entries)
    if thumbnail_source_entry is None:
        abort(400, description="Missing imagery file")
        return

    thumb_source_filename, _ = thumbnail_source_entry
    thumb_filename = "thumb-%s-%s" % (str(uuid.uuid4()), thumb_source_filename)

    # Save data in DB
    repository = Repository()
    with repository.transaction() as transaction:
        satellite = repository.read_satellite(args["sat"])
        if satellite is None:
            abort(400, description="Unknown satellite")

        sat_id = SatelliteId(satellite["sat_id"])

        tle = args.get('tle')
        if tle:
            # Remove trailing character
            tle = [line.strip() for line in tle]

        observation: Observation = {
            'obs_id': ObservationId(0),
            'aos': args['aos'],
            'tca': args['tca'],
            'los': args['los'],
            'sat_id': sat_id,
            'thumbnail': thumb_filename,
            'notes': args.get('notes'),
            'station_id': StationId(station_id),
            'tle': tle
        }

        obs_id = repository.insert_observation(observation)
        observation["obs_id"] = obs_id

        for filename, file_ in file_entries:
            observation_file: ObservationFile = {
                "obs_file_id": ObservationFileId(0),
                "filename": filename,
                "media_type": file_.mimetype,
                "obs_id": obs_id
            }
            repository.insert_observation_file(observation_file)

        transaction.commit()

    # Save files in filesystem
    root = app.config["storage"]['image_root']

    for filename, file_ in file_entries:
        path = os.path.join(root, filename)
        try:
            file_.save(path)
            app.logger.info("File %s written to %s" % (filename, root))
        except OSError as e:
            app.logger.error("Failed to write %s (image_root=%s): %s" % (path, root, e))
            return abort(503, "Unable to write file %s. Disk operation error." % filename)

    # Make thumbnail
    thumb_source_path = os.path.join(root, thumb_source_filename)
    thumb_path = os.path.join(root, "thumbs", thumb_filename)
    make_thumbnail(thumb_source_path, thumb_path)

    # Make charts
    station = repository.read_station(observation["station_id"])
    make_charts(observation, station, root)
    return '', 204

def make_charts(observation: Observation, station: Station,
        root:str=None):
    if root is None:
        root = app.config["storage"]['image_root']

    location = tle_diagrams.Location(station["lat"], station["lon"], 0)
    
    chart_dir = os.path.join(root, "charts")
    get_chart_path = lambda type_, obs_id: os.path.join(
        chart_dir,
        "%s-%d.png" % (type_, obs_id)
    )
    
    for type_, gen in [("by_time", tle_diagrams.generate_by_time_plot_png),
                    ("polar", tle_diagrams.generate_polar_plot_png)]:
        stream = gen(location, observation["tle"], observation["aos"],
                        observation["los"])
        path = get_chart_path(type_, observation["obs_id"])
        save_binary_stream_to_file(path, stream)
