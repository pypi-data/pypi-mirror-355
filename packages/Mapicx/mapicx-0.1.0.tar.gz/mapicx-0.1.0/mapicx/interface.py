import numpy as np
from .layer import Dense
from .Activation_function import Relu, Softmax
from .Loss_function import CategoricalCrossentropy
from .optimizers import SGD

class NeuralNetwork:
    def __init__(self, layers, loss_activation, optimizer):
        """
        Initialize the neural network model.
        
        Args:
            layers (list): List of network layers in forward pass order
            loss_activation (object): Combined loss and activation function
            optimizer (object): Optimizer for updating parameters
        """
        self.layers = layers
        self.loss_activation = loss_activation
        self.optimizer = optimizer
        
    def forward(self, X):
        """
        Perform forward pass through all layers.
        
        Args:
            X (ndarray): Input data
        Returns:
            ndarray: Output of the final layer
        """
        output = X
        for layer in self.layers:
            layer.forward(output)
            output = layer.output
        return output

    def backward(self, y):
        self.loss_activation.backward(self.loss_activation.output, y)
        dinputs = self.loss_activation.dinputs
        
        for layer in reversed(self.layers):
            layer.backward(dinputs)
            dinputs = layer.dinput

    def update_params(self):
        """Update parameters using the optimizer"""
        self.optimizer.pre_update()
        for layer in self.layers:
            # Only update layers that have trainable parameters
            if hasattr(layer, 'weights'):
                self.optimizer.update_params(layer)
        self.optimizer.post_update_params()

    def train(self, X, y, epochs, print_every=100):
        """
        Train the neural network.
        
        Args:
            X (ndarray): Input data
            y (ndarray): Target values
            epochs (int): Number of training iterations
            print_every (int): Log interval
        """
        # Convert one-hot encoded targets to class indices
        y_labels = np.argmax(y, axis=1) if len(y.shape) == 2 else y
        
        for epoch in range(epochs + 1):
            # Forward pass
            output = self.forward(X)
            loss = self.loss_activation.forward(output, y)
            
            # Calculate accuracy
            predictions = np.argmax(self.loss_activation.output, axis=1)
            accuracy = np.mean(predictions == y_labels)
            
            # Log progress
            if epoch % print_every == 0:
                print(f'epoch: {epoch}, '
                      f'acc: {accuracy:.3f}, '
                      f'loss: {loss:.3f}, '
                      f'lr: {self.optimizer.current_learning_rate}')
            
            # Backward pass and parameter update
            self.backward(y)
            self.update_params()