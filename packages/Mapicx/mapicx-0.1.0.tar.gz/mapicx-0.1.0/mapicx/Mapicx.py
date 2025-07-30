from .layer import Dense, Dropout
from .Activation_function import Relu, Softmax
from .Loss_function import Activation_Softmax_Loss_CategoricalCrossentropy
from .optimizers import SGD
from .interface import NeuralNetwork
from typing import Optional, List
import numpy as np

class Mapicx:
    def __init__(self) -> None:
        self.layers_list = []
        self.loss = None
        self.optimizer = None
        self.model = None
        self.softmax = Softmax()  # For prediction

    def add(self, n_features: int, n_neurons: int, 
            layer: str = 'Dense', 
            activation: Optional[str] = 'Relu', 
            rate: float = 0.0):
        """
        Add layers to the neural network
        
        Args:
            n_features: Input size for Dense layer
            n_neurons: Output size for Dense layer
            layer: Layer type ('Dense' or 'Dropout')
            activation: Activation function ('Relu', 'Softmax', or None)
            rate: Dropout rate (for Dropout layer)
        """
        if layer == 'Dense':
            self.layers_list.append(Dense(n_features, n_neurons))
            if activation == 'Relu':
                self.layers_list.append(Relu())
            elif activation == 'Softmax':
                self.layers_list.append(Softmax())
        elif layer == 'Dropout':
            if not self.layers_list:
                raise ValueError("Cannot add Dropout layer at the beginning")
            self.layers_list.append(Dropout(rate))

    def compile(self, optimizer: SGD, loss: str = 'categorical_crossentropy'):
        """
        Configure the model for training
        
        Args:
            optimizer: Optimizer instance (e.g., SGD)
            loss: Loss function (only 'categorical_crossentropy' supported)
        """
        if loss != 'categorical_crossentropy':
            raise ValueError("Only 'categorical_crossentropy' is supported")
        
        if not isinstance(self.layers_list[-1], Softmax):
            raise ValueError("Last layer must be Softmax for classification")
        
        # Remove final Softmax (handled by combined loss)
        self.layers_list.pop()
        self.loss = Activation_Softmax_Loss_CategoricalCrossentropy()
        self.optimizer = optimizer

    def fit(self, X: np.ndarray, y: np.ndarray, 
            epochs: int, print_every: int = 100):
        """
        Train the model
        
        Args:
            X: Input data
            y: Target labels
            epochs: Number of training iterations
            print_every: Logging interval
        """
        epochs += 1
        # Set Dropout layers to training mode
        for layer in self.layers_list:
            if isinstance(layer, Dropout):
                layer.training = True
        
        self.model = NeuralNetwork(
            layers=self.layers_list,
            loss_activation=self.loss,
            optimizer=self.optimizer
        )
        self.model.train(X, y, epochs, print_every)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model
        
        Args:
            X: Input data
        Returns:
            Predicted probabilities
        """
        if not self.model:
            raise RuntimeError("Model must be trained before prediction")
        
        # Set Dropout layers to inference mode
        for layer in self.model.layers:
            if isinstance(layer, Dropout):
                layer.training = False
        
        # Forward pass to get logits
        logits = self.model.forward(X)
        
        # Apply Softmax to get probabilities
        self.softmax.forward(logits)
        return self.softmax.output