from __future__ import absolute_import
import torch
import numpy as np
import cv2
import DetectronPytorch.tools._init_paths
from fast_neural_style import utils as style_utils
from DetectronPytorch.tools.wrapped_model import WrappedDetectron, union_masks, apply_binary_mask, grayscale
from fast_neural_style.forward import forward_pass
from fast_neural_style.transformer_net import TransformerNet


def segment_and_style(style_model, detectron_model, pil_image, mask_threshold=0.9, use_grayscale=False):

    #original image
    numpy_image = np.array(pil_image)

    if grayscale:
        styled = grayscale(numpy_image)
    else:
        #run the style transfer model on the input image
        styled = style_utils.tensor_to_numpy_image(forward_pass(style_model, pil_image))
    
    #get_masks
    scored_masks = detectron_model.segment_people(numpy_image, mask_threshold)

    if len(scored_masks) == 0:
        print("no person found")
        #no people found, style whole image
        output = styled
    else:
        #some people found, merge all masks
        people_mask = union_masks((m for m, s in scored_masks))
        #style network cuts two pixels off due to convolution padding issues
        styled = cv2.resize(styled, (people_mask.shape[1], people_mask.shape[0]))
        output, _, _ = apply_binary_mask(numpy_image, styled, ~people_mask)

    return output[:, :, ::-1]

if __name__ == '__main__':
    #load style models
    style = TransformerNet()
    style.load_state_dict(torch.load('models/starry_more_style/ckpt_epoch_1_batch_id_8000.pth'))
    style.eval()
    style.cuda()

    detectron = WrappedDetectron('./DetectronPytorch')
    for i in range(1, 12):
        in_file = ('sources/catalyst/{:02d}.jpg'.format(i))
        out_file = ('out_{:02d}.png'.format(i))

        input_im = style_utils.load_image(in_file, scale=1)
        output = segment_and_style(style, detectron, input_im, mask_threshold = 0.95, use_grayscale=True)
        cv2.imwrite(out_file, output)
