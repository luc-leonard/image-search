import json
import logging
import pickle
import urllib
from pathlib import Path

import clip
import psycopg2 as psy
import torch
from flask import Flask, send_file
from flask_cors import CORS
from sklearn.manifold import TSNE

device = 'cpu'
image_dir = Path('/media/lleonard/big_slow_disk/datasets/unslash/content/')
LOGGER = logging.getLogger(__name__)


def init_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format, handlers=[logging.StreamHandler()])
    module_levels = {
        'flask': logging.INFO,
        'werkzeug': logging.WARNING,
    }
    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level)


class MyApp(Flask):
    @torch.no_grad()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_logging()
        LOGGER.info('starting app')
        self.db = psy.connect(dbname='photo_gallery', user='postgres', password='mysecretpassword', host='localhost')
        self.db.set_session(autocommit=True)
        with self.db.cursor() as cursor:
            LOGGER.info('connected to database')
            cursor.execute("SELECT path, features FROM image_features")
            data = cursor.fetchall()
            LOGGER.info('fetched data')
            self.images_path, images_features = list(zip(*data))
        images_features = [pickle.loads(features) for features in images_features]
        self.tsne = TSNE(2, verbose=1)

        self.images_features = torch.tensor(images_features).to(device).type(torch.float32)
        LOGGER.info('loaded features in VRAM')
        self.tsne_proj = self.tsne.fit_transform(self.images_features / self.images_features.norm(dim=-1, keepdim=True))
        LOGGER.info('projected features')

        self.clip_model, _ = clip.load('ViT-B/16', device=device, jit=False)
        self.clip_model.eval()
        LOGGER.info('loaded CLIP model')


app = MyApp(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.get('/embeddings/')
def get_embeddings():
    ret = []
    for i, (path, features) in enumerate(zip(app.images_path, app.tsne_proj)):
        ret.append({'path': str(path), 'x': float(features[0]), 'y': float(features[1]), 'color': 'red'})
    return json.dumps(ret)


# @app.get('/embeddings/<string:term>')
# def get_embeddings_(term):
#     with torch.no_grad():
#         term = urllib.parse.unquote(term).split(';')
#         text_features = app.clip_model.encode_text(clip.tokenize(term).to(device))
#
#         all_features = torch.cat([app.images_features.cpu(), text_features.cpu()])
#         all_features = all_features / all_features.norm(dim=-1, keepdim=True)
#         tsne_proj = app.tsne.fit_transform(all_features)
#         ret = []
#         for i, features in enumerate(tsne_proj):
#             path = app.images_path[i] if i < len(app.images_path) else None
#             if path is None:
#                 path = "text_" + term[i - len(app.images_path)]
#                 print(path, features)
#             ret.append({'path': str(path), 'x': float(features[0]), 'y': float(features[1])})
#         return json.dumps(ret)


@app.get('/embeddings/<string:term>')
def get_embeddings_(term):
    with torch.no_grad():
        term = urllib.parse.unquote(term).split(';')
        text_features = app.clip_model.encode_text(clip.tokenize(term).to(device))
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (100.0 * app.images_features @ text_features.T)
        max_similarities = similarity.squeeze(-1).topk(50).indices
        ret = []
        for i, (path, features) in enumerate(zip(app.images_path, app.tsne_proj)):
            if i in max_similarities:
                ret.append({'path': str(path), 'x': float(features[0]), 'y': float(features[1]), 'color': 'green'})
            else:
                ret.append({'path': str(path), 'x': float(features[0]), 'y': float(features[1]), 'color': 'red'})
        return json.dumps(ret)

@app.get('/search/<string:term>/')
def find(term):
    LOGGER.info('searching for %s', term)
    text = clip.tokenize([term]).to(device)
    text_features = app.clip_model.encode_text(text)
    LOGGER.info('embedded text')
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarity = (100.0 * app.images_features @ text_features.T)
    max_similarities = similarity.squeeze(-1).topk(10).indices
    LOGGER.info('found %d results', len(max_similarities))
    return json.dumps([str(app.images_path[i]) for i in max_similarities])


@app.get('/content/<path:the_path>')
def get_image(the_path):
    path = image_dir / the_path
    return send_file(path, cache_timeout=600)


def open_port():
    import miniupnpc
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 10
    upnp.discover()
    upnp.selectigd()
    port = 5002

    # addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
    upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'photo-gallery', '')


if __name__ == "__main__":
    open_port()
    app.run(host='0.0.0.0', port=5002, debug=True)
