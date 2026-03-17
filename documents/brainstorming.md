# Feature Brainstorming

## 1. Natural Language Restaurant Search
- **Description:** Retrieve and rank restaurants that best match a user’s specific, natural-language request (e.g., “a quiet place with good service for a date”).
- **Further Data Needed:** Natural language review texts, pre-trained sentence embeddings.
- **ML Methods:**
  - **Sentence Embeddings:** To convert unstructured query text and review texts into dense numerical feature vectors.
  - **Dimensionality Reduction (PCA):** To explore and simplify the structure of the high-dimensional embedding data.
  - **Unsupervised Learning (k-means clustering / GMM):** To probabilistically group restaurants into semantically similar clusters without manual labels.
  - **Distance Metrics (Cosine Similarity):** To compute the distance between the user’s embedded query and the reviews/restaurants.

## 2. Interactive Map Overlay Interface
- **Description:** Visualize the recommended restaurants on a geographic map, making the results immediately actionable for the user.
- **Further Data Needed:** Geolocation data (latitude and longitude) for each restaurant.
- **ML Methods:**
  - **Supervised Ranking Model (Logistic Regression):** Combines text similarity scores, geographical relevance, and standard signals (e.g., star ratings) to rank the final recommendations displayed on the map.

## 3. Initial Explicit Preferences Calibration
- **Description:** Allow users to specify exactly which aspects or styles (e.g., atmosphere, service quality, price) they care most about during their initial use to calibrate their first recommendations.
- **Further Data Needed:** User-selected aspects/styles during onboarding.
- **ML Methods:**
  - **Aspect-Level Sentiment Extraction:** To identify sub-topics within review texts (e.g., "service", "food", "ambience").
  - **Feature Weight Adjustment:** Modifying the weights of extracted aspect-level sentiments to prioritize the user's explicit preferences before computing final similarity scores.

## 4. Finding Similar Restaurants
- **Description:** Allow users to find venues similar to a specific, known restaurant that they already like.
- **Further Data Needed:** Aggregated restaurant profiles.
- **ML Methods:**
  - **Distance Metrics (Cosine Similarity):** Compute pairwise distances between the aggregated embeddings of different restaurants to identify the most mathematically similar ones.

## 5. Automated Recommendations via Search History
- **Description:** Proactively recommend places based on the user's prior search queries and interactions.
- **Further Data Needed:** User search history and logs of positive queries.
- **ML Methods:**
  - **Content-Based Filtering:** Maintaining a "moving-average user embedding" built dynamically from their previous positive queries to anticipate their future preferences.

## 6. Continuous Post-Visit Feedback Loop
- **Description:** Dynamically update and refine future recommendations based on the user's explicit ratings and feedback after visiting a recommended restaurant.
- **Further Data Needed:** Post-visit ratings, textual feedback from the user.
- **ML Methods:**
  - **Online Learning:** Dynamically updating the custom "user embedding" profile using the explicit visit ratings to continuously improve prediction accuracy over time.

# Method Brainstorming

## 1. Sentence Embeddings
- **Natural Language Restaurant Search:** Converts unstructured query text and review texts into dense numerical feature vectors.

## 2. Dimensionality Reduction (PCA)
- **Natural Language Restaurant Search:** Explores and simplifies the structure of the high-dimensional embedding data.

## 3. Unsupervised Learning (k-means clustering / GMM)
- **Natural Language Restaurant Search:** Probabilistically groups restaurants into semantically similar clusters without manual labels.

## 4. Distance Metrics (Cosine Similarity)
- **Natural Language Restaurant Search:** Computes the distance between the user’s embedded query and the reviews/restaurants.
- **Finding Similar Restaurants:** Computes pairwise distances between aggregated embeddings of different restaurants.

## 5. Supervised Ranking Model (Logistic Regression)
- **Interactive Map Overlay Interface:** Combines text similarity scores, geographical relevance, and standard signals to rank the final recommendations displayed on the map.

## 6. Aspect-Level Sentiment Extraction & Feature Weighting
- **Initial Explicit Preferences Calibration:** Identifies sub-topics within review texts and adjusts their weights to prioritize the user's explicit preferences.

## 7. Content-Based Filtering
- **Automated Recommendations via Search History:** Maintains a "moving-average user embedding" dynamically built from previous positive queries to anticipate future preferences.

## 8. Online Learning
- **Continuous Post-Visit Feedback Loop:** Dynamically updates the custom "user embedding" profile using explicit visit ratings to continuously improve prediction accuracy.
