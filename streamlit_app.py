# Add this function to your code
def load_data_with_uploader():
    """Option to upload CSV files directly"""
    st.sidebar.header("📁 Upload CSV Files")
    
    uploaded_files = {}
    file_names = [
        'DimStudent.csv', 'DimDate.csv', 'DimAssessment.csv', 
        'DimCategory.csv', 'DimCourse.csv', 'DimInstructor.csv',
        'FactEnrollment.csv', 'FactAssessmentPerformance.csv'
    ]
    
    for file_name in file_names:
        uploaded_files[file_name] = st.sidebar.file_uploader(
            f"Upload {file_name}", type="csv", key=file_name
        )
    
    if all(uploaded_files.values()):
        try:
            # Load all files
            dim_student = pd.read_csv(uploaded_files['DimStudent.csv'], parse_dates=['RegistrationDate'], dayfirst=True)
            dim_date = pd.read_csv(uploaded_files['DimDate.csv'], parse_dates=['FullDate'], dayfirst=True)
            dim_assessment = pd.read_csv(uploaded_files['DimAssessment.csv'])
            dim_category = pd.read_csv(uploaded_files['DimCategory.csv'])
            dim_course = pd.read_csv(uploaded_files['DimCourse.csv'], parse_dates=['CreatedDate'], dayfirst=True)
            dim_instructor = pd.read_csv(uploaded_files['DimInstructor.csv'])
            fact_enrollment = pd.read_csv(uploaded_files['FactEnrollment.csv'])
            fact_performance = pd.read_csv(uploaded_files['FactAssessmentPerformance.csv'])
            
            # ... rest of the merging code from load_data_from_csv ...
            
            return enrollment_df, performance_df
        except Exception as e:
            st.error(f"Error processing uploaded files: {e}")
            return load_sample_data()
    else:
        return load_sample_data()
