# -*- coding: utf-8 -*-
# ================================================================
#
#   @File        : noisylabeln.py
#   @Author      : Xinhao Cai
#   @Created date: 2023/5/18
#   @Description :
#
# ================================================================
import os
from torchvision.datasets import VisionDataset
from PIL import Image
from tqdm import tqdm


def pil_loader(path):
    with open(path, 'rb') as f:
        img = Image.open(f)
        return img.convert('RGB')


def is_image_file(filename, extensions):
    return filename.lower().endswith(extensions)


def find_classes(root):
    root = os.path.expanduser(root)
    category_file = os.path.join(root, 'classes.txt')
    classes = []
    with open(category_file, 'r') as f:
        lines = f.readlines()
    for line in lines:
        classes.append(line.strip())
    assert len(classes) == 200, f'number of classes is expected to be 200, got {len(classes)}!'
    class_to_idx = {classes[i]: i for i in range(len(classes))}
    return classes, class_to_idx



def make_dataset(root, extensions, split='train'):
    root = os.path.expanduser(root)
    instances = []     # item: image_path
    true_labels = []   # item: human-annotated label
    labels = []  # item: unreliable label
    
    if split in ['train']:
        annotation_file_clean = os.path.join(root, 'training_labels_noise_80.txt')
        with open(annotation_file_clean, 'r') as f:
            lines = f.readlines()
        for line in lines:
            img_index, label_index = line.strip().split(' ')
            path = os.path.join(root, 'train', str(img_index).zfill(4)+'.jpg')
            instances.append(path)
            labels.append(int(label_index) - 1)
        return instances, labels

    elif split in ['val', 'test']:
        annotation_file_clean = os.path.join(root, 'test_labels.txt')
        with open(annotation_file_clean, 'r') as f:
            lines = f.readlines()
        for line in lines:
            img_index, label_index = line.strip().split(' ')
            path = os.path.join(root, 'test', str(img_index).zfill(4)+'.jpg')
            instances.append(path)
            labels.append(int(label_index) - 1)
        return instances, labels



class NoisylabelN(VisionDataset):
    # samples with correct labels:   72409
    # samples with noisy labels  : 1037497
    def __init__(self, root, split='train', use_cache=False, transform=None, target_transform=None, loader=pil_loader, extensions=None):
        super().__init__(root, transform=transform, target_transform=target_transform)
        assert split in ['train', 'test'], 'split can only be train / val / test'
        self.image_extensions = ('.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif', '.tiff', '.webp') if extensions is None else extensions
        self.split = split  # train / val / test
        self.loader = loader
        self.use_cache = use_cache
        classes, class_to_idx = find_classes(root)

        samples, targets = make_dataset(root, self.image_extensions, self.split)

        if len(samples) == 0:
            raise (RuntimeError("Found 0 files in subfolders of: " + self.root + "\n"
                                "Supported extensions are: " + ",".join(extensions)))

        self.n_samples = len(samples)
        self.samples = samples
        self.targets = targets
        self.classes = classes
        self.class_to_idx = class_to_idx
        self.loaded_samples = self._cache_dataset() if self.use_cache else None

    def get_targets(self):
        if self.split == 'train':
            targets = [-1] * self.n_samples
            for idx in range(self.n_samples):
                # verification samples also use noisy labels as targets
                if (self.noisy_labels[idx] is not None) and (self.clean_labels[idx] is not None):
                    targets[idx] = self.noisy_labels[idx]
                elif self.noisy_labels[idx] is None:
                    targets[idx] = self.clean_labels[idx]
                else:
                    targets[idx] = self.noisy_labels[idx]
        else:
            assert None not in self.clean_labels, 'clean labels are missing'
            targets = [y for y in self.clean_labels]
        return targets

    def _cache_dataset(self):
        cached_samples = []
        print('caching samples ... ')
        for idx, path in enumerate(tqdm(self.samples, ncols=100, ascii=' >')):
            image = self.loader(path)
            cached_samples.append(image)
        assert len(cached_samples) == self.n_samples
        return cached_samples

    def __getitem__(self, index):
        if self.use_cache:
            assert len(self.loaded_samples) == self.n_samples
            sample, target = self.loaded_samples[index], self.targets[index]
        else:
            sample, target = self.loader(self.samples[index]), self.targets[index]
        if self.transform is not None:
            sample = self.transform(sample)
        if self.target_transform is not None:
            target = self.target_transform(target)

        return {'index': index, 'data': sample, 'label': target}

    def __len__(self):
        return len(self.samples)

    def get_verification_samples(self):
        # verification samples: samples which have both clean and noisy labels
        verification_samples = []
        for idx in range(self.n_samples):
            if self.clean_labels[idx] is not None and self.noisy_labels[idx] is not None:
                verification_samples.append(idx)
        return verification_samples

    def get_clean_samples(self):
        # clean samples: samples which have clean labels
        clean_samples = []
        for idx in range(self.n_samples):
            if self.clean_labels[idx] is not None:
                clean_samples.append(idx)
        return clean_samples

    def get_noisy_samples(self):
        # noisy samples: samples which have noisy labels
        noisy_samples = []
        for idx in range(self.n_samples):
            if self.noisy_labels[idx] is not None:
                noisy_samples.append(idx)
        return noisy_samples


if __name__ == '__main__':
    train_data = NoisylabelN('../Datasets/release', 'train')
    print('Train ---> ', train_data.n_samples)        # 1047570
    # val_data = Clothing1M('../Datasets/clothing1m', 'val')
    # print('Val   ---> ', val_data.n_samples)          #   14313
    # test_data = Clothing1M('../Datasets/clothing1m', 'test')
    # print('Test  ---> ', test_data.n_samples)         #   10526

    # v_samples = set(train_data.get_verification_samples())
    # c_samples = set(train_data.get_clean_samples())
    # n_samples = set(train_data.get_noisy_samples())
    # print(len(v_samples), len(c_samples), len(n_samples))
    print(train_data.targets[0])
