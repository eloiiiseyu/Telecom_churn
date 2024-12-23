import shap
import pandas as pd
import numpy as np
import streamlit as st
from matplotlib import pyplot as plt
from pyarrow import parquet as pq
from catboost import CatBoostClassifier, Pool
import joblib
from pathlib import Path

# Path of the trained model and data
MODEL_PATH = "model/catboost_model.cbm" 
DATA_PATH = "data/catboost_data.csv"
SCALER_PATH = "model/scaler.pkl"


st.set_page_config(page_title="Churn Project")

@st.cache_resource
def load_data():
    data = pd.read_csv(DATA_PATH)
    return data

def load_x_y(file_path):
    data = joblib.load(file_path)
    data.reset_index(drop=True, inplace=True)
    return data

def load_model():
    model = CatBoostClassifier()
    model.load_model(MODEL_PATH)
    return model

def yes_no_to_binary(value):
    return 1 if value == "Yes" else 0

def load_scaler():
    scaler = joblib.load(SCALER_PATH)
    return scaler

@st.cache_resource
def calculate_shap(_model, X_train, X_test):
    # Calculate SHAP values
    explainer = shap.TreeExplainer(_model)
    shap_train = explainer.shap_values(X_train)
    shap_test = explainer.shap_values(X_test)
    return explainer, shap_train, shap_test

def plot_shap_values(model, explainer, shap_train, shap_test, customer_id, X_test, X_train):
    # Visualize SHAP values for a specific customer
    customer_index = X_test[X_test['CustomerID'] == customer_id].index[0]
    fig, ax_2 = plt.subplots(figsize=(6,6), dpi=200)
    shap.decision_plot(explainer.expected_value, shap_test[customer_index], X_test[X_test['CustomerID'] == customer_id], link="logit")
    st.pyplot(fig)
    plt.close()

def display_shap_summary(shap_train, X_train):
    # Create the plot summarizing the SHAP values
    shap.summary_plot(shap_train, X_train, plot_type="bar", plot_size=(12,12))
    summary_fig, _ = plt.gcf(), plt.gca()
    st.pyplot(summary_fig)
    plt.close()

def display_shap_waterfall_plot(explainer, expected_value, shap_values, feature_names, max_display=20):
    # Create SHAP waterfall drawing
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    shap.plots._waterfall.waterfall_legacy(expected_value, shap_values, feature_names=feature_names, max_display=max_display, show=False)
    st.pyplot(fig)
    plt.close()

def plot_shap(model, data, customer_id, X_train, X_test, explainer, shap_train, shap_test):

    # Visualize SHAP values
    plot_shap_values(model, explainer, shap_train, shap_test, customer_id, X_test, X_train)

    # Waterfall
    customer_index = X_test[X_test['CustomerID'] == customer_id].index[0]
    display_shap_waterfall_plot(explainer, explainer.expected_value, shap_test[customer_index], feature_names=X_test.columns, max_display=20)

st.title("Telco Customer Churn Project")

def main():
    model = load_model()
    data = load_data()

    X_train = load_x_y("data/X_train_cat.pkl")
    X_test = load_x_y("data/X_test_cat.pkl")
    y_train = load_x_y("data/y_train.pkl")
    y_test = load_x_y("data/y_test.pkl")

    max_tenure = data['Tenure Months'].max()
    max_monthly_charges = data['Monthly Charges'].max()
    max_total_charges = data['Total Charges'].max()

    explainer, shap_train, shap_test = calculate_shap(_model = model, X_train = X_train, X_test = X_test)

    # Radio buttons for options
    election = st.radio("Make Your Choice:", ("Feature Importance", "Current customer & user-based SHAP", "Future customer prediction"))
    available_customer_ids = X_test['CustomerID'].tolist()
    
    # If User-based SHAP option is selected
    if election == "Current customer & user-based SHAP":
        # Customer ID text input
        customer_id = st.selectbox("Choose the Customer", available_customer_ids)
        customer_index = X_test[X_test['CustomerID'] == customer_id].index[0]
        st.write(f'Customer {customer_id}:')
        st.write(f'Actual value for the Customer Churn : {y_test.iloc[customer_index]}')
        y_pred = model.predict(X_test)
        y_pred_prob = model.predict_proba(X_test)[:, 1]
        st.write(f"Prediction for the Customer Churn Probability : {y_pred_prob[customer_index] * 100:.2f}%")
        st.write(f"Prediction for the Customer Churn : {y_pred[customer_index]}")
        plot_shap(model, data, customer_id, X_train=X_train, X_test=X_test, explainer = explainer, shap_train = shap_train, shap_test = shap_test)
    
    # If Feature Importance is selected
    elif election == "Feature Importance":
        display_shap_summary(shap_train= shap_train, X_train=X_train)

    # If Calculate CHURN Probability option is selected
    elif election == "Future customer prediction":
        # Retrieving data from the user
        customerID = "6464-UIAEA"
        gender = st.selectbox("Gender:", ("Female", "Male"))
        senior_citizen = st.selectbox("SeniorCitizen", ("No","Yes"))
        partner = st.selectbox("Partner:", ("No", "Yes"))
        dependents = st.selectbox("Dependents:", ("No", "Yes"))
        tenure = st.number_input("TenureMonths:", min_value=0, max_value=max_tenure, step=1)
        phone_service = st.selectbox("PhoneService:", ("No", "Yes"))
        multiple_lines = st.selectbox("MultipleLines:", ("No", "Yes"))
        internet_service = st.selectbox("InternetService:", ("No", "DSL", "Fiber optic"))
        online_security = st.selectbox("OnlineSecurity:", ("No", "Yes"))
        online_backup = st.selectbox("OnlineBackup:", ("No", "Yes"))
        device_protection = st.selectbox("DeviceProtection:", ("No", "Yes"))
        tech_support = st.selectbox("TechSupport:", ("No", "Yes"))
        streaming_tv = st.selectbox("StreamingTV:", ("No", "Yes"))
        streaming_movies = st.selectbox("StreamingMovies:", ("No", "Yes"))
        contract = st.selectbox("Contract:", ("Month-to-month", "One year", "Two year"))
        paperless_billing = st.selectbox("PaperlessBilling", ("No", "Yes"))
        payment_method = st.selectbox("PaymentMethod:", ("Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"))
        monthly_charges = st.number_input("Monthly Charges", min_value=0.0, max_value=max_monthly_charges, step=0.01)
        total_charges = st.number_input("Total Charges", min_value=0.0, max_value=max_total_charges, step=0.01)
        
        # Confirmation button
        confirmation_button = st.button("Confirm")

        # When the confirmation button is clicked
        if confirmation_button:
            # Convert user-entered data into a data frame
            new_customer_data = pd.DataFrame({
                "customerID": [customerID],
                "Gender": [gender],
                "Senior Citizen": [yes_no_to_binary(senior_citizen)],
                "Partner": [yes_no_to_binary(partner)],
                "Dependents": [yes_no_to_binary(dependents)],
                "Tenure Months": [tenure],
                "Phone Service": [yes_no_to_binary(phone_service)],
                "Multiple Lines": [yes_no_to_binary(multiple_lines)],
                "Internet Service": [internet_service],
                "Online Security": [yes_no_to_binary(online_security)],
                "Online Backup": [yes_no_to_binary(online_backup)],
                "Device Protection": [yes_no_to_binary(device_protection)],
                "Tech Support": [yes_no_to_binary(tech_support)],
                "Streaming TV": [yes_no_to_binary(streaming_tv)],
                "Streaming Movies": [yes_no_to_binary(streaming_movies)],
                "Contract": [contract],
                "Paperless Billing": [yes_no_to_binary(paperless_billing)],
                "Payment Method": [payment_method],
                "Monthly Charges": [monthly_charges],
                "Total Charges": [total_charges]
            })
            
            # Transform numeric features using the scaler
            numeric_features = ["Tenure Months", "Monthly Charges", "Total Charges"]
            scaler = load_scaler()
            new_customer_data[numeric_features] = scaler.transform(new_customer_data[numeric_features])
            
            # Predict churn probability using the model
            churn_probability = model.predict_proba(new_customer_data)[:, 1]

            # Format churn probability
            formatted_churn_probability = "{:.2%}".format(churn_probability.item())

            big_text = f"<h1>Churn Probability: {formatted_churn_probability}</h1>"
            st.markdown(big_text, unsafe_allow_html=True)
            st.write(new_customer_data.to_dict())

if __name__ == "__main__":
    main()