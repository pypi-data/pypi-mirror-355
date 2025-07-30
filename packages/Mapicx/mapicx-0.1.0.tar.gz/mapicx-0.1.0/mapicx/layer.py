from typing import List
import numpy as np
from .Data import x,y
from .Activation_function import Relu, Softmax
from .Loss_function import Loss,CategoricalCrossentropy

class Layers:
    def __init__(self) -> None:
        self.layer_output = []

    def calc_layer_output(
        self, 
        _input_metrics: List[List[float]],     # 2D: shape = [batch_size, input_features]
        _weight_metrics: List[List[float]],    # 2D: shape = [neurons, input_features]
        biases: List[float]                    # 1D: one bias per neuron
    ) -> List[List[float]]:
        inputs = np.array(_input_metrics)               # shape: [batch, inputs]
        weights = np.array(_weight_metrics).T           # transpose to [inputs, neurons]
        bias_vec = np.array(biases)                     # shape: [neurons]

        self.layer_output = np.dot(inputs, weights) + bias_vec
        return self.layer_output.tolist()


    
class Dense():
    def __init__(self, n_input, n_neurons):
        self.weights = 0.01 * np.random.randn(n_input, n_neurons)
        self.biases = np.zeros((1, n_neurons))

    def forward(self, input):
        self.output = np.dot(input, self.weights) + self.biases
        self.input = input

    def backward(self, dvalue):
        self.dweight = np.dot(self.input.T,dvalue)
        self.dbaises = np.sum(dvalue, axis=0, keepdims=True)
        self.dinput = np.dot(dvalue, self.weights.T)


class Dropout:
    def __init__(self, rate) -> None:
        self.rate = 1 - rate  # Probability of keeping neurons
        self.training = True   # Default to training mode

    def forward(self, inputs):
        if not self.training:
            self.output = inputs
            return

        self.inputs = inputs
        self.binary_mask = np.random.binomial(
            n=1, 
            p=self.rate, 
            size=inputs.shape
        ) / self.rate
        self.output = inputs * self.binary_mask

    def backward(self, dvalues):
        self.dinput = dvalues * self.binary_mask