# -*- coding: utf-8 -*-
"""Environmental_Change_Prediction_V2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1q3Hxkom6JJcN6v8E95WxHqjLZPEznpsz
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt

# Step 1: Load the datasets
simulated_data = pd.read_csv('Enhanced_UAV_TrainingData.csv')
historical_train = pd.read_csv('Training_Data.csv')
historical_test = pd.read_csv('Testing_Data.csv')

# Step 2: Select relevant columns from historical data
relevant_columns = ['temperature', 'wind', 'rhum', 'precipitation', 'Visibility (km)']
historical_train = historical_train[relevant_columns]
historical_test = historical_test[relevant_columns]

# Rename columns to match simulated data
historical_train.columns = ['Temperature', 'WindSpeed', 'Humidity', 'Precipitation', 'Visibility']
historical_test.columns = ['Temperature', 'WindSpeed', 'Humidity', 'Precipitation', 'Visibility']

# Step 3: Combine historical training data with simulated data
combined_data = pd.concat([historical_train, simulated_data], ignore_index=True)

# Check distribution of Precipitation values
print("Precipitation Value Counts (Training Data):")
print(combined_data['Precipitation'].value_counts())

# Balance training data if needed
balanced_train_data = combined_data[combined_data['Precipitation'] <= 5.0]  # Example threshold
combined_data = balanced_train_data  # Replace the original dataset

# Step 4: Normalize the data
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

# Features (X) and target (y)
X_combined = combined_data[['Temperature', 'WindSpeed', 'Humidity', 'Visibility']]
y_combined = combined_data['Precipitation']

# Normalize
X_combined_scaled = scaler_X.fit_transform(X_combined)
y_combined_scaled = scaler_y.fit_transform(y_combined.values.reshape(-1, 1))

# Reshape X for LSTM input
X_combined_reshaped = np.reshape(X_combined_scaled, (X_combined_scaled.shape[0], 1, X_combined_scaled.shape[1]))

# Step 5: Handle Rare Classes in the Target (y_combined_scaled)

# Count occurrences of each unique value in y_combined_scaled
import numpy as np
import pandas as pd

unique_counts = pd.Series(y_combined_scaled.flatten()).value_counts()

# Filter rows where the target value occurs at least twice
valid_values = unique_counts[unique_counts >= 2].index  # Keep only values with >= 2 occurrences
valid_indices = [i for i in range(len(y_combined_scaled)) if y_combined_scaled[i][0] in valid_values]

# Apply filtering to X_combined_reshaped and y_combined_scaled
X_combined_reshaped = X_combined_reshaped[valid_indices]
y_combined_scaled = y_combined_scaled[valid_indices]

print(f"Filtered dataset size: {len(X_combined_reshaped)} samples")

# Step 6: Stratified Train/Test Split

from sklearn.model_selection import train_test_split

try:
    # Stratified split based on filtered data
    X_train, X_val, y_train, y_val = train_test_split(
        X_combined_reshaped, y_combined_scaled, test_size=0.2, random_state=42, stratify=y_combined_scaled
    )

    print(f"Training set size: {len(X_train)} samples")
    print(f"Validation set size: {len(X_val)} samples")

except ValueError as e:
    print("Error in stratified split:", e)
    print("Falling back to a random split...")

    # Fallback to random split if stratified split fails
    X_train, X_val, y_train, y_val = train_test_split(
        X_combined_reshaped, y_combined_scaled, test_size=0.2, random_state=42
    )

    print(f"Training set size: {len(X_train)} samples")
    print(f"Validation set size: {len(X_val)} samples")

# Step 6: Define the LSTM Model
model = tf.keras.Sequential([
    tf.keras.layers.LSTM(256, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),
    tf.keras.layers.Dropout(0.3),  # dropout for regularization
    tf.keras.layers.LSTM(128, return_sequences=True),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(1)  # Single output for regression
])

# Compile the model
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Step 7: Train the Model
# Early stopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train the updated model
history = model.fit(X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=100,
                    batch_size=64,
                    callbacks=[early_stopping])

# Step 8: Evaluate the Model
X_test = scaler_X.transform(historical_test[['Temperature', 'WindSpeed', 'Humidity', 'Visibility']])
y_test = scaler_y.transform(historical_test['Precipitation'].values.reshape(-1, 1))
X_test_reshaped = np.reshape(X_test, (X_test.shape[0], 1, X_test.shape[1]))

# Evaluate
test_loss, test_mae = model.evaluate(X_test_reshaped, y_test)
print(f"Test Loss: {test_loss}, Test MAE: {test_mae}")

# Debugging actual and predicted values
print("First 10 Actual Values:", scaler_y.inverse_transform(y_test[:10]))
print("First 10 Predicted Values:", scaler_y.inverse_transform(y_pred_scaled[:10]))

# Step 9: Visualize Training Progress
plt.figure(figsize=(10, 6))
plt.plot(history.history['loss'], label='Training Loss', color='blue')
plt.plot(history.history['val_loss'], label='Validation Loss', color='orange')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.title('Training and Validation Loss')
plt.grid(True)
plt.show()

# Step 10: Visualize Predictions
y_pred_scaled = model.predict(X_test_reshaped)
y_pred = scaler_y.inverse_transform(y_pred_scaled)
y_actual = scaler_y.inverse_transform(y_test)

# Plot actual vs predicted values for more samples
plt.figure(figsize=(12, 8))
plt.plot(y_actual[:300], label='Actual', color='blue', alpha=0.7, linewidth=2)
plt.plot(y_pred[:300], label='Predicted', color='orange', alpha=0.7, linewidth=2)
plt.xlabel('Sample Index')
plt.ylabel('Precipitation (mm)')
plt.title('Actual vs Predicted Precipitation')
plt.legend()
plt.grid(True)
plt.show()