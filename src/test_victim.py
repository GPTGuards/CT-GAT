import argparse
from transformers import AutoTokenizer
import torch
from utils import packDataset_util
import torch.nn as nn
import pandas as pd
import os
# base_path = os.path.dirname(os.getcwd ())
base_path = os.path.abspath('.')
data_path = base_path +"/data/"

def load_data(data_name,type):
    file_path = data_path+data_name+"/"
    data = pd.read_csv(file_path+type+".csv")
    p_data = []
    for i in range(len(data)):
        p_data.append((data['text'][i], data['label'][i]))
    return p_data

def evaluaion(loader):
    model.eval()
    total_number = 0
    total_correct = 0
    with torch.no_grad():
        for padded_text, attention_masks, labels in loader:
            if torch.cuda.is_available():
                padded_text, attention_masks, labels = padded_text.cuda(), attention_masks.cuda(), labels.cuda()
            output = model(padded_text, attention_masks).logits
            _, flag = torch.max(output, dim=1)
            total_number += labels.size(0)
            correct = (flag == labels).sum().item()
            total_correct += correct
        acc = total_correct / total_number
        return acc

def test():
    dev_acc = evaluaion(test_loader)
    print('test acc: {}'.format(dev_acc))

    test_acc = evaluaion(test_loader)
    print('*' * 89)
    print('finish all, test acc: {}'.format(test_acc))
    model_path = base_path+"/model/"
    torch.save(model, model_path+dataset_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dataset', type=str, default='satnews'
    )
    parser.add_argument(
        '--bert_type', type=str, default='bert-base-uncased'
    )
    parser.add_argument(
        '--labels', type=int, default=2
    )

    args = parser.parse_args()

    dataset_name = args.dataset
    bert_type = args.bert_type
    labels = args.labels

    tokenizer = AutoTokenizer.from_pretrained(bert_type)
    model_path = base_path+"model/"
    model = torch.load(model_path+dataset_name)
    if torch.cuda.is_available():
        model = nn.DataParallel(model.cuda())
    orig_train = load_data(dataset_name,"train")
    orig_test = load_data(dataset_name,"dev")

    pack_util = packDataset_util(bert_type)
    train_loader = pack_util.get_loader(orig_train, shuffle=True, batch_size=32)
    test_loader = pack_util.get_loader(orig_test, shuffle=False, batch_size=32)

    test()