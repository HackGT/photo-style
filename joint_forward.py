import torch
import numpy as np
import cv2
import DetectronPytorch.tools._init_paths
import random
from fast_neural_style import utils as style_utils
from DetectronPytorch.tools.wrapped_model import WrappedDetectron, union_masks, apply_binary_mask, grayscale
from fast_neural_style.forward import forward_pass
from fast_neural_style.transformer_net import TransformerNet


def segment_and_style(style_models, detectron, pil_image, mask_threshold = 0.9):
    numpy_image = np.array(pil_image)
    with torch.no_grad():
        scored_masks = [m for m, _ in detectron.segment_people(numpy_image, mask_threshold)]

    #merge masks
    mask = np.zeros(numpy_image.shape[:2])
    if len(scored_masks) > 0:
        # pixel map where 0 is the background, 1 is the first person, etc
        for i, single_mask in enumerate(scored_masks):
            mask += (i + 1) * single_mask

    styled_images = []
    for model in style_models:
        styled = style_utils.tensor_to_numpy_image(forward_pass(model, pil_image))
        styled_images.append(cv2.resize(styled, (numpy_image.shape[1], numpy_image.shape[0])))

    return mask, scored_masks, styled_images

if __name__ == '__main__':
    #load style models
    models = []

    mosaic = TransformerNet()
    mosaic.load_state_dict(torch.load('models/mosaic/mosaic_0.4.1.model'))
    mosaic.eval()
    mosaic.cuda()
    models.append(mosaic)

    starry = TransformerNet()
    starry.load_state_dict(torch.load('models/starry_night/starry01.model'))
    starry.eval()
    starry.cuda()
    models.append(starry)

    neon = TransformerNet()
    neon.load_state_dict(torch.load('models/neon/neon01.model'))
    neon.eval()
    neon.cuda()
    models.append(neon)

    detectron = WrappedDetectron('./DetectronPytorch')

    print("Loaded all models")


    for i in range(1, 13):
        in_file = ('sources/catalyst/{:02d}.jpg'.format(i))
        print(in_file)
        out_file = ('out_{:02d}.png'.format(i))

        input_im = style_utils.load_image(in_file, scale=1)
        numpy_image = np.array(input_im)
        _, scored_masks, styled_images = segment_and_style(models, detectron, input_im)
        if len(scored_masks) > 0:
            mask = ~union_masks(scored_masks)
            numpy_image, _, _ = apply_binary_mask(numpy_image, random.choice(styled_images), mask)

        numpy_image = numpy_image[:, :, ::-1]
        cv2.imwrite(out_file, numpy_image)
