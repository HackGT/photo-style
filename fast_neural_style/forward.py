import torch
from torchvision import transforms

def forward_pass(model, image, device = 'cuda', pipeline=None):
    if pipeline is None:
        pipeline = transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Lambda(lambda x: x.mul(255))
                    ])

    batch_tensor = pipeline(image).unsqueeze(0).to(device)

    model.to(device)
    model.eval()
    with torch.no_grad():
        output_tensor = model(batch_tensor).data[0]

    output_tensor = output_tensor.cpu()

    return output_tensor
