import os

import joblib
import numpy as np

from sklearn.ensemble import RandomForestRegressor


# =========================================================
# MODEL PATH
# =========================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "risk_model.joblib"
)


# =========================================================
# TRAIN PROTOTYPE MODEL
# =========================================================

def train_model():

    rng = np.random.default_rng(
        42
    )

    samples = 2500

    rainfall = rng.uniform(
        0,
        100,
        samples
    )

    soil_moisture = rng.uniform(
        0,
        100,
        samples
    )

    ground_movement = rng.uniform(
        0,
        100,
        samples
    )

    terrain = rng.uniform(
        0,
        100,
        samples
    )

    base_risk = rng.uniform(
        0,
        100,
        samples
    )

    humidity = rng.uniform(
        30,
        100,
        samples
    )


    # Prototype target function
    target = (

        rainfall * 0.30

        +

        soil_moisture * 0.18

        +

        ground_movement * 0.22

        +

        terrain * 0.10

        +

        base_risk * 0.12

        +

        humidity * 0.08

    )


    # Small noise
    target += rng.normal(
        0,
        4,
        samples
    )


    target = np.clip(
        target,
        0,
        100
    )


    X = np.column_stack([

        rainfall,

        soil_moisture,

        ground_movement,

        terrain,

        base_risk,

        humidity

    ])


    model = RandomForestRegressor(

        n_estimators=120,

        max_depth=10,

        random_state=42,

        n_jobs=-1

    )


    model.fit(
        X,
        target
    )


    joblib.dump(
        model,
        MODEL_PATH
    )


    return model


# =========================================================
# GET MODEL
# =========================================================

def get_model():

    if os.path.exists(
        MODEL_PATH
    ):

        try:

            return joblib.load(
                MODEL_PATH
            )

        except Exception:

            pass

    return train_model()


# =========================================================
# PREDICT RISK
# =========================================================

def predict_risk(

    rainfall,

    soil_moisture,

    ground_movement,

    terrain,

    base_risk,

    humidity

):

    model = get_model()


    features = np.array([

        [

            float(rainfall),

            float(soil_moisture),

            float(ground_movement),

            float(terrain),

            float(base_risk),

            float(humidity)

        ]

    ])


    prediction = model.predict(
        features
    )[0]


    return round(

        float(
            np.clip(
                prediction,
                0,
                100
            )
        ),

        2

    )


# =========================================================
# RISK LEVEL
# =========================================================

def risk_level(score):

    score = float(score)

    if score >= 80:

        return "CRITICAL"

    if score >= 60:

        return "HIGH"

    if score >= 30:

        return "MODERATE"

    return "LOW"