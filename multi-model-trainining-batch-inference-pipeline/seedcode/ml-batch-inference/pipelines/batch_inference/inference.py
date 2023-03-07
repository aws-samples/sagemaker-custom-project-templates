import json
import logging
import numpy as np
import pickle
import torch
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hidden_dim = 20
output_dim = 3

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

def input_fn(request_body, content_type):
    logger.info("Request Body: {}".format(request_body))
    logger.info("Content Type: {}".format(content_type))

    if content_type == "application/json":
        input_data = json.loads(request_body)

        logger.info("Input data: {}".format(input_data))

        return input_data["inputs"]
    elif content_type == "text/csv":

        input_data = request_body.split("\n")

        logger.info("Input data: {}".format(input_data))

        return input_data
    else:
        logger.error("Requested unsupported ContentType in Accept: " + content_type)

        raise Exception("Requested unsupported ContentType in Accept: " + content_type)

def model_fn(model_dir):
    try:

        logger.info("Loading model: {}".format(model_dir))

        with open("{}/vectorizer.pkl".format(model_dir), "rb") as f:
            vectorizer = pickle.load(f)
            
        model = MulticlassClassifier(len(vectorizer.vocabulary_), hidden_dim, output_dim)
        
        model.load_state_dict(torch.load("{}/model.pth".format(model_dir)))

        return vectorizer, model
    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)

        raise e

def output_fn(prediction_output, response_type):
    logger.info("Predictions: {}".format(prediction_output))

    if response_type == "application/json":
        return json.dumps(prediction_output), "application/json"
    if response_type == "text/csv":
        return prediction_output, "text/csv"

    raise Exception("Requested unsupported ContentType in Accept: " + response_type)

def predict_fn(input_data, model_pack):
    try:
        logger.info("Input data: {}".format(input_data))

        vectorizer, model = model_pack

        sentences_bag = vectorizer.transform(input_data).toarray()
        sentences_tensor = torch.from_numpy(sentences_bag).type(torch.float32)

        with torch.no_grad():
            output = model(sentences_tensor)

        predictions = []

        for el in output:
            prediction = np.argmax(el, axis=-1)

            predictions.append("{},{}".format(prediction.tolist(), max(el.softmax(dim=-1).tolist())))

        return predictions

    except Exception as e:
        stacktrace = traceback.format_exc()
        logger.error(stacktrace)

        raise e