from .Mapicx import Mapicx
from .optimizers import SGD
from .Data import x, y

# Create model
model = Mapicx()

# Add layers
model.add(2, 512, layer='Dense', activation='Relu')
model.add(0, 0, layer='Dropout', rate=0.1) 
model.add(512, 512, layer='Dense', activation='Relu')
model.add(0, 0, layer='Dropout', rate=0.2)
model.add(512, 3, layer='Dense', activation='Softmax')

# Compile model
optimizer = SGD(_learning_rate=1, _decay=1e-3, momentum=0.9)
model.compile(optimizer=optimizer)

# Train model
model.fit(x, y, epochs=10001, print_every=100)

# Make predictions
predictions = model.predict(x)
print("Predictions shape:", predictions.shape)
print(predictions)