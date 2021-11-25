import clip
import torch
from PIL import Image
from tqdm import tqdm
import pickle
import psycopg2 as psy

class SimpleFileDataset(torch.utils.data.Dataset):
    def __init__(self, file_list, *, transform=None):
        self.file_list = file_list
        self.transform = transform
        if self.transform is None:
            self.transform = torch.nn.Identity()

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        return torch.tensor([idx]), self.transform(Image.open(self.file_list[idx]).convert('RGB'))


def index(image_dir, batch_size=128, device='cuda'):
    clip_model, preprocess = clip.load('ViT-B/16', device=device, jit=False)
    clip_model.eval()
    image_file_list = list(image_dir.glob('**/*.jpg'))
    image_list = list(image_file_list)
    dataset = SimpleFileDataset(image_list, transform=preprocess)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    connection = psy.connect(dbname='photo_gallery', user='postgres', password='mysecretpassword', host='localhost')
    connection.set_session(autocommit=True)
    cursor = connection.cursor()

    for filepath_idx, images in tqdm(dataloader):
        image_features = clip_model.encode_image(images.to(device)).detach().cpu().numpy()
        for i, features in enumerate(image_features):
            filepath = image_file_list[filepath_idx[i].item()]
            cursor.execute("INSERT INTO image_features(path, features) VALUES (%s, %s)",
                           (str(filepath.relative_to(image_dir)), pickle.dumps(features)))



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', type=str, required=True)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()
    index(args.image_dir, args.batch_size, args.device)