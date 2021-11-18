from pathlib import Path

from flask import Flask
import clip
from PIL import Image
import torch
import psycopg2 as psy
import pickle

app = Flask(__name__)


device = 'cuda:0'
image_dir = Path('/home/lleonard/dev/perso/clip_generators/clip_generators/bots/res/')
batch_size = 32


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

    for batch in chunk(image_list, batch_size):
        print(f'doing {batch}')
        images = [Image.open(img) for img in batch]
        images = torch.stack([preprocess(img) for img in images]).to(device)
        image_features = clip_model.encode_image(images)
        for i, path in enumerate(batch):
            cursor.execute("INSERT INTO image_features(path, features) VALUES (%s, %s)",
                           (str(path), pickle.dumps(image_features[i].detach().cpu().numpy())))


def find(text):
    clip_model, preprocess = clip.load('ViT-B/16', device=device, jit=False)
    clip_model.eval()
    text = clip.tokenize([text]).to(device)
    text_features = clip_model.encode_text(text)

    connection = psy.connect(dbname='photo_gallery', user='postgres', password='mysecretpassword', host='localhost')
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    cursor.execute("SELECT path, features FROM image_features")
    data = cursor.fetchall()
    images_features = []
    images_path = []

    for path, features in data:
        images_path.append(path)
        images_features.append(torch.tensor(pickle.loads(features)))
    image_features = torch.stack(images_features).to(device)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarity = (100.0 * image_features @ text_features.T)
    max_similarities = similarity.squeeze(-1).topk(10).indices
    for similarity in max_similarities:
        print(f'{images_path[similarity]}')



if __name__ == "__main__":
    find('A black and white photography')