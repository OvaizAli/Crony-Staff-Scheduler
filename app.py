import streamlit as st
import pandas as pd

# Function to calculate employees required based on sales target and historical data grouped by shift and day
def calculate_employees_for_shift_day(day, shift, target_sales, grouped_data):
    """
    Calculate how many employees are needed based on the target sales and historical data for a specific shift and day.
    """
    # Get historical mean sales and employee count for the given day and shift
    day_shift_data = grouped_data[(grouped_data['Day'] == day) & (grouped_data['Employee Shift'] == shift)]
    
    if not day_shift_data.empty:
        historical_sales = day_shift_data['Average Sales ($)'].values[0]
        historical_employees = day_shift_data['Average Employees Needed'].values[0]
        
        # Calculate ratio: target_sales / historical_sales = required_employees / historical_employees
        required_employees = (target_sales / historical_sales) * historical_employees
        
        # Ensure at least 1 employee is scheduled if target_sales > 0
        return max(int(round(required_employees)), 1)
    
    return 0  # If no data is available for the shift and day, return 0 employees

# Streamlit UI
st.title("Employee Schedule Generator")

# Input Sales Target
sales_target = st.number_input("Enter Sales Target for Each Day ($)", min_value=500, max_value=10000, step=1000)

# File upload for previous schedule data
uploaded_file = st.file_uploader("Upload CSV with Previous Schedules", type=["csv"])

if uploaded_file is not None:
    # Reading the CSV file
    previous_data = pd.read_csv(uploaded_file)
    st.error("Preview of uploaded file:")
    st.dataframe(previous_data)
    
    # Ensure the CSV has the expected columns
    expected_columns = ['EmployeeName', 'Date', 'Day', 'Employee Shift', 'Total Sales ($)']
    
    if all(col in previous_data.columns for col in expected_columns):
        # Fix inconsistent day values by ensuring the 'Date' and 'Day' columns align correctly
        previous_data['Date'] = pd.to_datetime(previous_data['Date'])
        previous_data['Corrected Day'] = previous_data['Date'].dt.day_name()
        
        # Drop the incorrect 'Day' column and rename the corrected one
        previous_data = previous_data.drop(columns=['Day'])
        previous_data = previous_data.rename(columns={'Corrected Day': 'Day'})
        
        # Group the data by Day and Shift to calculate the average sales and unique employee count
        grouped_by_shift_day = previous_data.groupby(['Day', 'Employee Shift']).agg({
            'Total Sales ($)': 'mean',  # Average sales
            'EmployeeName': pd.Series.nunique  # Count of unique employees
        }).reset_index()
        
        grouped_by_shift_day = grouped_by_shift_day.rename(columns={
            'Total Sales ($)': 'Average Sales ($)',
            'EmployeeName': 'Average Employees Needed'
        })
        
        # Display the grouped DataFrame with average sales and employees
        st.success("Historical Average Sales and Employees by Shift")
        st.dataframe(grouped_by_shift_day)
        
        # Generate schedules based on previous data and target sales
        st.success("Generated Employee Schedule for the Upcoming Week")
        
        # Placeholder for generated schedule
        schedule = []
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        shifts = ['Morning', 'Night']
        
        for day in days_of_week:
            for shift in shifts:
                # Calculate the number of employees needed for the shift and day
                employees_needed = calculate_employees_for_shift_day(day, shift, sales_target, grouped_by_shift_day)
                
                # Get available employees for the day and shift
                available_employees = previous_data[
                    (previous_data['Day'] == day) & 
                    (previous_data['Employee Shift'] == shift)
                ]['EmployeeName'].unique()
                
                # Assign employees based on availability
                employees_assigned = available_employees[:employees_needed] if len(available_employees) >= employees_needed else list(available_employees) + ['Not Available'] * (employees_needed - len(available_employees))
                
                schedule.append({
                    'Day': day,
                    'Shift': shift,
                    'Sales Target ($)': sales_target,
                    'Employees Needed': employees_needed,
                    'Assigned Employees': ', '.join(employees_assigned)
                })
        
        # Convert to DataFrame for display
        schedule_df = pd.DataFrame(schedule)
        
        # Display the DataFrame using st.write() to avoid truncation
        st.write("Generated Schedule:")
        st.write(schedule_df)
        
        # Download button for generated schedule
        csv = schedule_df.to_csv(index=False)
        st.download_button(label="Download Schedule as CSV", data=csv, file_name='generated_schedule.csv', mime='text/csv')
    
    else:
        st.error("The uploaded file does not match the expected format. Please check the column names.")
