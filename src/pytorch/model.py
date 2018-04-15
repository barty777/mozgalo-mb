import pretrainedmodels
import torch.nn.functional as F
from torch import nn
import pdb
from lsoftmax import LSoftmaxLinear

class LModel(nn.Module):
    def __init__(self, margin, num_classes, fine_tune=True):
        """

        :param margin:
        :param num_classes: Number classes
        :param fine_tune: If true then all layers are trained. Otherwise only the top
        layers are trained and the main network layers are locked
        """
        super().__init__()
        self.margin = margin

        self.model = pretrainedmodels.__dict__['xception'](num_classes=1000,
                                                      pretrained='imagenet')
        self.net = nn.Sequential(*list(self.model.children())[:-1])

        if not fine_tune:
            print("Locking base model layers")
            for param in self.net.parameters():
                param.requires_grad = False

        #self.lsoftmax_linear = LSoftmaxLinear(input_dim=2048, output_dim=num_classes, margin=margin)
        self.logits = nn.Linear(2048, num_classes)
        self.reset_parameters()

    def reset_parameters(self):
        #self.lsoftmax_linear.reset_parameters()
        pass

    def forward(self, input, target=None):
        conv_output = self.net(input)

        avg_kernel_size = conv_output[-1].shape[-2]
        global_pooling = F.avg_pool2d(conv_output, avg_kernel_size)

        batch_size = conv_output.size(0)
        #logit = self.lsoftmax_linear(input=global_pooling.view(batch_size, -1), target=target)
        logit = self.logits(global_pooling.view(batch_size, -1))
        return logit
