import re
import argparse

import torch
import transformer_net


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Utility to convert PyTorch 0.3.x style transfer models to 0.4.1+")
    parser.add_argument("--model", type=str, required=True, help="model file to convert")
    parser.add_argument("--output", type=str, required=True, help="location for new model")
    args = parser.parse_args()

    style_model = transformer_net.TransformerNet()
    state_dict = torch.load(args.model)

    # remove saved deprecated running_* keys in InstanceNorm from the checkpoint
    for k in list(state_dict.keys()):
        if re.search(r'in\d+\.running_(mean|var)$', k):
            del state_dict[k]

    style_model.load_state_dict(state_dict)
    print(style_model)

    style_model.eval()
    style_model.cpu()

    torch.save(style_model.state_dict(), args.output)

