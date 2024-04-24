import pymongo
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['MyAnimeListDB']
anime_collection = db['anime_data']

# Define the aggregation pipeline to retrieve unique genre names
pipeline = [
    {
        "$project": {
            "_id": 0,
            "genres": 1
        }
    },
    {
        "$unwind": "$genres"
    },
    {
        "$group": {
            "_id": None,
            "genres": {"$addToSet": "$genres.name"}
        }
    }
]

# Execute the aggregation pipeline to get unique genre names
result = list(anime_collection.aggregate(pipeline))
class_names = result[0]["genres"]

# Retrieve all anime documents
anime_data = list(anime_collection.find({}, {"_id": 0}))

# Generate the target variable
target_genre = [1 if genre in [g["name"] for g in anime.get("genres", [])] else 0 for anime in anime_data for genre in class_names]

# Reshape the target variable
target_genre = np.array(target_genre[:len(anime_data)]).reshape(-1)

# Extract features from anime documents
features = []
for anime in anime_data:
    feature = [
        anime.get("mean", 0),
        anime.get("popularity", 0),
        anime.get("num_list_users", 0),
        anime.get("num_scoring_users", 0),
        anime.get("num_episodes", 0),
        anime.get("average_episode_duration", 0)
    ]
    features.append(feature)

# Scale the features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(scaled_features, target_genre, test_size=0.2, random_state=42)

# Fit the SVM model
classifier = SVC(kernel="linear")
classifier.fit(X_train, y_train)

# Evaluate the model
accuracy = classifier.score(X_test, y_test)
print("Accuracy:", accuracy)

import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

# Predict on the test set
y_pred = classifier.predict(X_test)

print("y_test shape:", y_test.shape)
print("y_pred shape:", y_pred.shape)

# Compute confusion matrix
cm = confusion_matrix(y_test, y_pred)

# Plot confusion matrix as a heatmap
plt.figure(figsize=(10, 8))
plt.imshow(cm, cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.xlabel("Predicted Genre")
plt.ylabel("True Genre")
plt.xticks(np.arange(len(class_names)), class_names, rotation=45)
plt.yticks(np.arange(len(class_names)), class_names)
plt.colorbar()
plt.show()

from sklearn.metrics import classification_report

# Generate classification report
report = classification_report(y_test, y_pred, labels=range(76), target_names=class_names)

# Print classification report
print(report)

from sklearn.metrics import roc_auc_score, average_precision_score

# Calculate AUC-ROC
auc_roc = roc_auc_score(y_test, y_pred)

# Calculate average precision score
avg_precision = average_precision_score(y_test, y_pred)

print("AUC-ROC:", auc_roc)
print("Average Precision:", avg_precision)


