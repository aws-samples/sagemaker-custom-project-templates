from argparse import ArgumentParser, Namespace
import csv
import glob
import json
import logging
import os
import pandas as pd
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from time import gmtime, strftime
import torch
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"

class MulticlassClassifier(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(MulticlassClassifier, self).__init__()
        
        self.fc1 = torch.nn.Linear(input_dim, hidden_dim)
        self.bn1 = torch.nn.BatchNorm1d(hidden_dim)
        self.relu1 = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.bn2 = torch.nn.BatchNorm1d(hidden_dim)
        self.relu2 = torch.nn.ReLU()
        self.dr1 = torch.nn.Dropout(0.2)
        self.fc3 = torch.nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        out = self.fc1(x)
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.fc2(out)
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.dr1(out)
        out = self.fc3(out)
        
        return out

"""
    Read input data
"""
def __read_data(files_path, dataset_percentage=100):
    try:
        logger.info("Reading dataset from source...")

        all_files = glob.glob(os.path.join(files_path, "*.csv"))

        datasets = []

        for filename in all_files:
            data = pd.read_csv(
                filename,
                sep=',',
                quotechar='"',
                quoting=csv.QUOTE_ALL,
                escapechar='\\',
                encoding='utf-8',
                error_bad_lines=False
            )

            datasets.append(data)

        data = pd.concat(datasets, axis=0, ignore_index=True)

        data = data.head(int(len(data) * (int(dataset_percentage) / 100)))

        return data
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error("{}".format(stacktrace))

        raise e

"""
    Read hyperparameters
"""
def __read_params():
    try:
        parser = ArgumentParser()

        parser.add_argument('--epochs', type=int, default=25)
        parser.add_argument('--learning_rate', type=float, default=0.001)
        parser.add_argument('--batch_size', type=int, default=100)
        parser.add_argument('--dataset_percentage', type=str, default=100)
        parser.add_argument('--output-data-dir', type=str, default=os.environ.get('SM_OUTPUT_DATA_DIR'))
        parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
        parser.add_argument('--test', type=str, default=os.environ.get('SM_CHANNEL_TEST'))
        parser.add_argument('--model_dir', type=str, default=os.environ.get('SM_MODEL_DIR'))

        args = parser.parse_args()

        if len(vars(args)) == 0:
            with open(os.path.join("/", "opt", "ml", "input", "config", "hyperparameters.json"), 'r') as f:
                training_params = json.load(f)

            args = Namespace(**training_params)

        return args
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error("{}".format(stacktrace))

        raise e
        
if __name__ == '__main__':

    args = __read_params()

    train = __read_data(args.train, args.dataset_percentage)
    test = __read_data(args.test, args.dataset_percentage)

    X_train, y_train = train['text'], train["labels"].values
    X_test, y_test = test['text'], test["labels"].values

    # Create a bag-of-words vectorizer
    vectorizer = CountVectorizer()
    
    # Fit the vectorizer to your dataset
    vectorizer.fit(X_train)
    
    # Convert the input strings to numerical representations
    X_train = vectorizer.transform(X_train).toarray()
    X_test = vectorizer.transform(X_test).toarray()
    
    X_train, y_train = torch.from_numpy(X_train).type(torch.float32), torch.from_numpy(y_train)
    X_test, y_test = torch.from_numpy(X_test).type(torch.float32), torch.from_numpy(y_test)
    
    model = MulticlassClassifier(X_train.shape[1], 20, 3)
    
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    
    logger.info("Start training: {}".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))

    for epoch in range(args.epochs):
        logger.info("Epoch: {}".format(epoch))
        # Forward pass: compute predicted y by passing x to the model
        y_pred = model(X_train)

        # Compute and print loss
        loss = criterion(y_pred, y_train)
        logger.info(f'Training Loss: {loss:.4f}')

        # Compute the accuracy
        _, predicted = torch.max(y_pred, dim=1)
        correct = (predicted == y_train).sum().item()
        accuracy = correct / len(y_train)
        logger.info(f'Training Accuracy: {accuracy:.4f}')

        # Zero gradients, perform a backward pass, and update the weights
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    logger.info("End training: {}".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))

    with torch.no_grad():
        y_pred = model(X_test)
        # Compute and print loss
        loss = criterion(y_pred, y_test)
        logger.info(f'Evaluation Loss: {loss:.4f}')

        # Compute the accuracy
        _, predicted = torch.max(y_pred, dim=1)
        correct = (predicted == y_test).sum().item()
        accuracy = correct / len(y_test)
        logger.info(f'Evaluation Accuracy: {accuracy:.4f}')

    logger.info("Save model in {}".format(args.model_dir))
    
    torch.save(model.state_dict(), "{}/model.pth".format(args.model_dir))
    
    logger.info("Save vectorizer in {}".format(args.model_dir))
    
    with open("{}/vectorizer.pkl".format(args.model_dir), "wb") as f:
        pickle.dump(vectorizer, f)

        