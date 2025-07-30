import torch
import torch.nn as nn
from torchvision import models
import torch.nn.functional as F
import warnings

class ConvBNReLU(nn.Module):
    def __init__(self, in_chan, out_chan, ks=3, stride=1, padding=1, *args, **kwargs):
        super(ConvBNReLU, self).__init__()
        self.conv = nn.Conv2d(in_chan, out_chan, kernel_size=ks,
                             stride=stride, padding=padding, bias=False)
        self.bn = nn.BatchNorm2d(out_chan)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        return x

class BiSeNetOutput(nn.Module):
    def __init__(self, in_chan, mid_chan, n_classes):
        super(BiSeNetOutput, self).__init__()
        self.conv = ConvBNReLU(in_chan, mid_chan, ks=3, stride=1, padding=1)
        self.conv_out = nn.Conv2d(mid_chan, n_classes, kernel_size=1, bias=False)
        
    def forward(self, x):
        x = self.conv(x)
        x = self.conv_out(x)
        return x

class AttentionRefinementModule(nn.Module):
    def __init__(self, in_chan, out_chan):
        super(AttentionRefinementModule, self).__init__()
        self.conv = ConvBNReLU(in_chan, out_chan, ks=3, stride=1, padding=1)
        self.conv_atten = nn.Conv2d(out_chan, out_chan, kernel_size=1, bias=False)
        self.bn_atten = nn.BatchNorm2d(out_chan)
        self.sigmoid_atten = nn.Sigmoid()
        
    def forward(self, x):
        feat = self.conv(x)
        atten = F.avg_pool2d(feat, feat.size()[2:])
        atten = self.conv_atten(atten)
        atten = self.bn_atten(atten)
        atten = self.sigmoid_atten(atten)
        out = torch.mul(feat, atten)
        return out

class FeatureFusionModule(nn.Module):
    def __init__(self, in_chan=256, out_chan=256):  # Changed to match checkpoint
        super(FeatureFusionModule, self).__init__()
        self.convblk = ConvBNReLU(in_chan, out_chan, ks=1, stride=1, padding=0)
        self.conv1 = nn.Conv2d(out_chan, out_chan//4, kernel_size=1, bias=False)
        self.conv2 = nn.Conv2d(out_chan//4, out_chan, kernel_size=1, bias=False)
        self.relu = nn.ReLU(inplace=True)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, fsp, fcp):
        fcat = torch.cat([fsp, fcp], dim=1)
        feat = self.convblk(fcat)
        atten = F.avg_pool2d(feat, feat.size()[2:])
        atten = self.conv1(atten)
        atten = self.relu(atten)
        atten = self.conv2(atten)
        atten = self.sigmoid(atten)
        feat_atten = torch.mul(feat, atten)
        feat_out = feat_atten + feat
        return feat_out

class BiSeNet(nn.Module):
    def __init__(self, n_classes, pretrained=True):
        super(BiSeNet, self).__init__()
        
        # Suppress warning about pretrained parameter
        if pretrained:
            warnings.warn(
                "The parameter 'pretrained' is deprecated, using ResNet18_Weights.IMAGENET1K_V1",
                DeprecationWarning
            )
        
        # Context Path
        resnet = models.resnet18(pretrained=True)
        self.context_path = nn.ModuleDict({
            'conv1': resnet.conv1,
            'bn1': resnet.bn1,
            'relu': resnet.relu,
            'maxpool': resnet.maxpool,
            'layer1': resnet.layer1,
            'layer2': resnet.layer2,
            'layer3': resnet.layer3,
            'layer4': resnet.layer4,
        })
        
        # Attention Refinement Modules
        self.arm16 = AttentionRefinementModule(256, 256)
        self.arm32 = AttentionRefinementModule(512, 512)
        
        # Feature Fusion Module - in_chan matches concat of spatial and context features
        self.ffm = FeatureFusionModule(in_chan=256, out_chan=256)  # Changed to match checkpoint
        
        # Spatial Path
        self.spatial_path = nn.Sequential(
            ConvBNReLU(3, 64, ks=7, stride=2, padding=3),
            ConvBNReLU(64, 128, ks=3, stride=2, padding=1),
            ConvBNReLU(128, 256, ks=3, stride=2, padding=1)
        )
        
        # Final conv
        self.conv_out = BiSeNetOutput(256, 256, n_classes)
        
    def forward(self, x):
        h, w = x.size()[2:]
        
        # Context Path
        feat = self.context_path['conv1'](x)
        feat = self.context_path['bn1'](feat)
        feat = self.context_path['relu'](feat)
        feat = self.context_path['maxpool'](feat)
        feat = self.context_path['layer1'](feat)
        feat = self.context_path['layer2'](feat)
        feat8 = self.context_path['layer3'](feat)  # 1/8
        feat16 = self.context_path['layer4'](feat8)  # 1/16
        
        feat16_arm = self.arm16(feat8)
        feat32_arm = self.arm32(feat16)
        
        # Spatial Path
        feat_sp = self.spatial_path(x)
        
        # Feature Fusion
        feat_fuse = self.ffm(feat_sp, feat16_arm)
        
        # Output
        feat_out = self.conv_out(feat_fuse)
        feat_out = F.interpolate(feat_out, (h, w), mode='bilinear', align_corners=True)
        
        return feat_out
