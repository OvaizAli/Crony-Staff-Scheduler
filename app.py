import streamlit as st
import pandas as pd

# Function to calculate employees required based on sales target, grouped by day, shift, and department
def calculate_employees_for_shift_day_department(day, shift, department, target_sales, grouped_data):
    """
    Calculate how many employees are needed based on the target sales and historical data for a specific day, shift, and department.
    """
    # Get historical mean sales and employee count for the given day, shift, and department
    day_shift_department_data = grouped_data[(grouped_data['Day'] == day) & 
                                             (grouped_data['Employee Shift'] == shift) &
                                             (grouped_data['Department'] == department)]
    
    if not day_shift_department_data.empty:
        historical_sales = day_shift_department_data['Average Sales ($)'].values[0]
        historical_employees = day_shift_department_data['Average Employees Needed'].values[0]
        
        # Calculate ratio: target_sales / historical_sales = required_employees / historical_employees
        required_employees = (target_sales / historical_sales) * historical_employees
        
        # Ensure at least 1 employee is scheduled if target_sales > 0
        return max(int(round(required_employees)), 1)
    
    return 0  # If no data is available for the shift, day, and department, return 0 employees

# Streamlit UI
st.title("Department-wise Employee Schedule Generator")

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
    expected_columns = ['EmployeeName', 'Date', 'Day', 'Employee Shift', 'Department', 'Total Sales ($)']
    
    if all(col in previous_data.columns for col in expected_columns):
        # Fix inconsistent day values by ensuring the 'Date' and 'Day' columns align correctly
        previous_data['Date'] = pd.to_datetime(previous_data['Date'])
        previous_data['Corrected Day'] = previous_data['Date'].dt.day_name()
        
        # Drop the incorrect 'Day' column and rename the corrected one
        previous_data = previous_data.drop(columns=['Day'])
        previous_data = previous_data.rename(columns={'Corrected Day': 'Day'})
        
        # Group the data by Day, Shift, and Department to calculate the average sales and unique employee count
        grouped_by_shift_day_department = previous_data.groupby(['Day', 'Employee Shift', 'Department']).agg({
            'Total Sales ($)': 'mean',  # Average sales
            'EmployeeName': pd.Series.nunique  # Count of unique employees
        }).reset_index()
        
        grouped_by_shift_day_department = grouped_by_shift_day_department.rename(columns={
            'Total Sales ($)': 'Average Sales ($)',
            'EmployeeName': 'Average Employees Needed'
        })
        
        # Display the grouped DataFrame with average sales and employees by department
        st.success("Historical Average Sales and Employees by Shift and Department")
        st.dataframe(grouped_by_shift_day_department)
        
        # Generate schedules based on previous data, department, and target sales
        st.success("Generated Employee Schedule for the Upcoming Week")
        
        # Placeholder for generated schedule
        schedule = []
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        shifts = ['Morning', 'Night']
        departments = previous_data['Department'].unique()  # Get all unique departments
        
        for day in days_of_week:
            assigned_employees = set()  # Track employees assigned to shifts for the day
            for shift in shifts:
                for department in departments:
                    # Calculate the number of employees needed for the shift, day, and department
                    employees_needed = calculate_employees_for_shift_day_department(day, shift, department, sales_target, grouped_by_shift_day_department)
                    
                    # Get available employees for the day, shift, and department excluding already assigned ones
                    available_employees = previous_data[
                        (previous_data['Day'] == day) & 
                        (previous_data['Employee Shift'] == shift) & 
                        (previous_data['Department'] == department) & 
                        (~previous_data['EmployeeName'].isin(assigned_employees))
                    ]['EmployeeName'].unique()
                    
                    # Assign employees based on availability
                    employees_assigned = available_employees[:employees_needed] if len(available_employees) >= employees_needed else list(available_employees) + ['Not Available'] * (employees_needed - len(available_employees))
                    
                    # Update the set of assigned employees
                    assigned_employees.update(employees_assigned)
                    
                    schedule.append({
                        'Day': day,
                        'Shift': shift,
                        'Department': department,
                        'Sales Target ($)': sales_target,
                        'Employees Needed': employees_needed,
                        'Assigned Employees': ', '.join(employees_assigned)
                    })
        
        # Convert to DataFrame for display
        schedule_df = pd.DataFrame(schedule)

        # Display the DataFrame using st.table() to ensure all values are fully visible
        st.table(schedule_df)

        # Download button for generated schedule
        csv = schedule_df.to_csv(index=False)
        st.download_button(label="Download Schedule as CSV", data=csv, file_name='generated_schedule.csv', mime='text/csv')

    else:
        st.error("The uploaded file does not match the expected format. Please check the column names.")
