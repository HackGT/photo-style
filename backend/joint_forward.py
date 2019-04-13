import torch
import numpy as np
import cv2
import DetectronPytorch.tools._init_paths
import random


from scipy.signal import convolve2d
from fast_neural_style import utils as style_utils
from DetectronPytorch.tools.wrapped_model import WrappedDetectron, union_masks, apply_binary_mask, grayscale
from fast_neural_style.forward import forward_pass
from fast_neural_style.transformer_net import TransformerNet


dilation_kernel = np.ones((9, 9)).astype(np.int8)
sobel_x = np.array([[1, 0, -1], [2, 0, -2], [1, 0, -1]]).astype(np.int8)
sobel_y = sobel_x.copy().T

# mask is boolean, binary
def outline(mask, value, use_base=True):
    x = abs(convolve2d(mask, sobel_x, mode = 'same', boundary='fill', fillvalue='0'))
    y = abs(convolve2d(mask, sobel_y, mode = 'same', boundary='fill', fillvalue='0'))
    x += y
    x = convolve2d(x, dilation_kernel, mode = 'same', boundary='fill', fillvalue='0')
    x[x != 0] = 100 + value
    if use_base:
        x[mask != 0] = 0
        mask = mask * value
        return mask + x
    return x

# def make_background_outline(mask_arr):
#     # TODO: why can't we use sobel
#     outline = np.zeros_like(mask_arr).astype(int)
#     mask_arr = np.pad(mask_arr, ((1, 1), (1, 1)), 'constant', constant_values=-1) # Key for edge

#     for i in range(1, mask_arr.shape[0] - 1):
#         for j in range(1, mask_arr.shape[1] - 1):
#             if mask_arr[i,j]: # if background point
#                 if not (mask_arr[i-1,j] == 1 and mask_arr[i+1,j] == 1 and mask_arr[i, j-1] == 1 and mask_arr[i, j+1] == 1):
#                     outline[i-1, j-1] = 1 # offset for padding
#     outline += 100
#     return outline

def segment_and_style(style_models, detectron, pil_image, mask_threshold = 0.9):
    numpy_image = np.array(pil_image)
    with torch.no_grad():
        scored_masks = [m for m, _ in detectron.segment_people(numpy_image, mask_threshold)]

    # background is by default, everything
    background_mask = np.ones(numpy_image.shape[:2], dtype=np.uint16)

    mask = np.zeros(numpy_image.shape[:2], dtype=np.int16)
    if len(scored_masks) > 0:
        background_bool_mask = ~union_masks(scored_masks)
        background_mask = background_bool_mask.astype(int)
        background_outline = outline(background_mask, 100, False) # Expect outline back as 200
        background_outline /= 2
        mask[background_outline != 0] = 0
        mask += background_outline
        for i, single_mask in enumerate(scored_masks):
            single_mask = outline(single_mask, i + 1)
            mask[single_mask != 0] = 0
            mask += single_mask
    else:
        background_outline = outline(background_mask, 0, False) # Short circuit, preferably
        mask[background_outline != 0] = 0


    scored_masks = [background_mask] + scored_masks
    # scored_masks is a list of boolean masks
    # mask is a unified mask with values

    # temp = mask.copy()
    # temp[temp != 0] = 1
    # temp = (1 - temp)
    # temp = np.pad(temp, ((1, 1)), mode='constant', constant_values=1)
    # out = outline(temp, 100)[1:-1, 1:-1]

    # mask[out != 0] = 0
    # mask += out

    # if len(scored_masks) > 0:
        # # pixel map where 0 is the background, 1 is the first person, etc
        # for i, single_mask in enumerate(scored_masks):
            # mask[single_mask != 0] = 0
            # mask += (i + 1) * single_mask

    styled_images = []
    for model in style_models:
        styled = style_utils.tensor_to_numpy_image(forward_pass(model, pil_image))
        styled_images.append(cv2.resize(styled, (numpy_image.shape[1], numpy_image.shape[0])))

    styled_images.append(grayscale(numpy_image))

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

    starry2 = TransformerNet()
    starry2.load_state_dict(torch.load('models/starry_night/starry02.model'))
    starry2.eval()
    starry2.cuda()
    models.append(starry2)

    neon = TransformerNet()
    neon.load_state_dict(torch.load('models/neon/neon01.model'))
    neon.eval()
    neon.cuda()
    models.append(neon)

    detectron = WrappedDetectron('./DetectronPytorch')

    print("Loaded all models")

    import json
    for i in range(11, 12):
        in_file = ('sources/catalyst/{:02d}.jpg'.format(i))
        print(in_file)

        input_im = style_utils.load_image(in_file, scale=1)
        numpy_image = np.array(input_im)
        mask, scored_masks, styled_images = segment_and_style(models, detectron, input_im)
        out_mask_name = 'mock_data/out_mask_{:02d}.jpg'.format(i)
        # cv2.imwrite(out_mask_name, 16 * mask)
        # mas

        for j, mask in enumerate(scored_masks):
            out_name = 'mock_data/out_mask_{:02d}_{:02d}.json'.format(j, i)
            json.dump(mask.tolist(), open(out_name, 'w'))
            # cv2.imwrite(out_name, im[:, :, ::-1])

        for j, im in enumerate(styled_images):
            out_name = 'mock_data/out_style_{:02d}_{:02d}.jpg'.format(j, i)
            cv2.imwrite(out_name, im[:, :, ::-1])


        # if len(scored_masks) > 0:
            # mask = ~union_masks(scored_masks)
            # numpy_image, _, _ = apply_binary_mask(numpy_image, random.choice(styled_images), mask)
        # else:
            # numpy_image = random.choice(styled_images)
            # numpy_image, _, _ = apply_binary_mask(numpy_image, random.choice(styled_images), mask)

        # numpy_image = numpy_image[:, :, ::-1]
        # cv2.imwrite(out_file, numpy_image)
