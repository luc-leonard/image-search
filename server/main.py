import json
from pathlib import Path
from flask_cors import CORS
from flask import Flask, send_file
import clip
from PIL import Image
import torch
import psycopg2 as psy
import pickle

from tqdm import tqdm

app = Flask(__name__)


device = 'cuda:0'
image_dir = Path('/home/lleonard/dev/perso/clip_generators/clip_generators/bots/res/')
batch_size = 64

cors = CORS(app, resources={r"/*": {"origins": "*"}})


def chunk(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def index():
    clip_model, preprocess = clip.load('ViT-B/16', device=device, jit=False)
    clip_model.eval()

    image_list = list(image_dir.glob('**/*.png'))

    connection = psy.connect(dbname='photo_gallery', user='postgres', password='mysecretpassword', host='localhost')
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    for batch in tqdm(chunk(image_list, batch_size)):
        images = [Image.open(img) for img in batch]
        images = torch.stack([preprocess(img) for img in images]).to(device)
        image_features = clip_model.encode_image(images).detach().cpu().numpy()
        for i, path in enumerate(batch):
            cursor.execute("INSERT INTO image_features(path, features) VALUES (%s, %s)",
                           (str(path.relative_to(image_dir)), pickle.dumps(image_features[i])))


@app.get('/search/<string:term>')
def find(term):
    clip_model, preprocess = clip.load('ViT-B/16', device=device, jit=False)
    clip_model.eval()
    text = clip.tokenize([term]).to(device)
    text_features = clip_model.encode_text(text)

    connection = psy.connect(dbname='photo_gallery', user='postgres', password='mysecretpassword', host='localhost')
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    cursor.execute("SELECT path, features FROM image_features")
    data = cursor.fetchall()
    images_path, images_features = list(zip(*data))

    images_features = [pickle.loads(features) for features in images_features]
    images_features = torch.tensor(images_features).to(device)

    images_features /= images_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarity = (100.0 * images_features @ text_features.T)
    max_similarities = similarity.squeeze(-1).topk(10).indices
    return json.dumps([str(images_path[i]) for i in max_similarities])

@app.get('/content/<path:the_path>')
def get_image(the_path):
    path = image_dir / the_path
    return send_file(path)


if __name__ == "__main__":
    # index()
    # print(find('A black and white photography'))
    app.run()