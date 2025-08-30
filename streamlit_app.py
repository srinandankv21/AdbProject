import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="EduSkillUp Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .data-table {
        font-size: 0.8rem;
    }
    .kpi-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for data
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'raw_data_loaded' not in st.session_state:
    st.session_state.raw_data_loaded = False

@st.cache_data
def load_raw_data_from_csv():
    """Load raw CSV files without any processing"""
    try:
        raw_data = {}
        csv_files = {
            'DimStudent': 'DimStudent.csv',
            'DimDate': 'DimDate.csv',
            'DimAssessment': 'DimAssessment.csv',
            'DimCategory': 'DimCategory.csv',
            'DimCourse': 'DimCourse.csv',
            'DimInstructor': 'DimInstructor.csv',
            'FactEnrollment': 'FactEnrollment.csv',
            'FactAssessmentPerformance': 'FactAssessmentPerformance.csv'
        }
        
        for name, file in csv_files.items():
            try:
                if name in ['DimStudent', 'DimDate', 'DimCourse']:
                    raw_data[name] = pd.read_csv(file, parse_dates=True, dayfirst=True, infer_datetime_format=True)
                else:
                    raw_data[name] = pd.read_csv(file)
                st.sidebar.success(f"✅ {name} loaded")
            except Exception as e:
                st.sidebar.error(f"❌ Error loading {name}: {str(e)}")
                return None
        
        return raw_data
        
    except Exception as e:
        st.error(f"Critical error loading raw data: {str(e)}")
        return None

@st.cache_data
def process_data_for_analysis(raw_data):
    """Process raw data into analysis-ready format"""
    if not raw_data:
        return None, None
    
    try:
        # Process enrollment data
        enrollment_df = raw_data['FactEnrollment'].merge(
            raw_data['DimStudent'][['StudentKey', 'StudentName', 'MembershipType']], 
            on='StudentKey', how='left'
        ).merge(
            raw_data['DimCourse'][['CourseKey', 'CourseTitle', 'Level']], 
            on='CourseKey', how='left'
        ).merge(
            raw_data['DimInstructor'][['InstructorKey', 'InstructorName']], 
            on='InstructorKey', how='left'
        ).merge(
            raw_data['DimCategory'][['CategoryKey', 'CategoryName']], 
            on='CategoryKey', how='left'
        )
        
        # Process performance data
        performance_df = raw_data['FactAssessmentPerformance'].merge(
            raw_data['DimStudent'][['StudentKey', 'StudentName']], 
            on='StudentKey', how='left'
        ).merge(
            raw_data['DimCourse'][['CourseKey', 'CourseTitle']], 
            on='CourseKey', how='left'
        ).merge(
            raw_data['DimAssessment'][['AssessmentKey', 'AssessmentTitle', 'AssessmentType', 'DifficultyLevel', 'MaxScore']], 
            on='AssessmentKey', how='left'
        )
        
        # Convert date keys to actual dates
        date_map = raw_data['DimDate'].set_index('DateKey')['FullDate']
        
        enrollment_df['EnrollmentDate'] = enrollment_df['EnrollmentDateKey'].map(date_map)
        enrollment_df['CompletionDate'] = enrollment_df['CompletionDateKey'].map(date_map)
        performance_df['SubmissionDate'] = performance_df['SubmissionDateKey'].map(date_map)
        
        # Calculate derived fields
        performance_df['ScorePercentage'] = (performance_df['ScoreEarned'] / performance_df['MaxPossibleScore']) * 100
        enrollment_df['CourseLevel'] = enrollment_df['Level']
        
        # Select final columns
        enrollment_df = enrollment_df[[
            'EnrollmentKey', 'StudentName', 'CourseTitle', 'CategoryName', 'InstructorName',
            'MembershipType', 'EnrollmentDate', 'CompletionDate', 'CoursePrice', 
            'ProgressPercentage', 'DaysToComplete', 'CompletionStatus', 'PaymentStatus', 'CourseLevel'
        ]]
        
        performance_df = performance_df[[
            'PerformanceKey', 'StudentName', 'CourseTitle', 'AssessmentTitle', 
            'AssessmentType', 'DifficultyLevel', 'ScoreEarned', 'MaxPossibleScore',
            'ScorePercentage', 'TimeSpentMinutes', 'AttemptsCount', 'SubmissionDate', 'IsCompleted'
        ]].rename(columns={'MaxPossibleScore': 'MaxScore'})
        
        return enrollment_df, performance_df
        
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None, None

@st.cache_data
def create_sample_data():
    """Create comprehensive sample data"""
    np.random.seed(42)
    
    # Sample data that matches your schema exactly
    enrollment_data = {
        'EnrollmentKey': range(1, 101),
        'StudentKey': np.random.randint(1, 51, 100),
        'CourseKey': np.random.randint(1, 16, 100),
        'InstructorKey': np.random.randint(1, 11, 100),
        'CategoryKey': np.random.randint(1, 11, 100),
        'EnrollmentDateKey': [20250829] * 100,
        'CompletionDateKey': np.random.choice([20250829, 20250915, 20251001, None], 100, p=[0.4, 0.3, 0.2, 0.1]),
        'EnrollmentCount': [1] * 100,
        'CoursePrice': np.random.uniform(100, 900, 100).round(2),
        'ProgressPercentage': np.random.uniform(0, 100, 100).round(2),
        'DaysToComplete': np.random.choice([None, 30, 60, 90], 100, p=[0.3, 0.3, 0.2, 0.2]),
        'CompletionStatus': np.random.choice(['Completed', 'In Progress', 'Dropped'], 100, p=[0.6, 0.3, 0.1]),
        'PaymentStatus': np.random.choice(['Paid', 'Pending', 'Failed'], 100, p=[0.7, 0.2, 0.1])
    }
    
    performance_data = {
        'PerformanceKey': range(1, 151),
        'StudentKey': np.random.randint(1, 51, 150),
        'CourseKey': np.random.randint(1, 16, 150),
        'AssessmentKey': np.random.randint(1, 31, 150),
        'SubmissionDateKey': [20250829] * 150,
        'SubmissionCount': np.random.randint(1, 4, 150),
        'ScoreEarned': np.random.uniform(50, 200, 150).round(2),
        'MaxPossibleScore': np.random.choice([100, 150, 200], 150),
        'TimeSpentMinutes': np.random.randint(10, 4000, 150),
        'AttemptsCount': np.random.randint(1, 5, 150),
        'IsCompleted': np.random.choice([True, False], 150, p=[0.8, 0.2])
    }
    
    # Create dimension data
    students = [f'Student_{i:02d}' for i in range(1, 51)]
    courses = [f'Course_{i:02d}' for i in range(1, 16)]
    categories = [f'Category_{i:02d}' for i in range(1, 11)]
    instructors = [f'Instructor_{i:02d}' for i in range(1, 11)]
    assessments = [f'Assessment_{i:02d}' for i in range(1, 31)]
    
    enrollment_df = pd.DataFrame(enrollment_data)
    performance_df = pd.DataFrame(performance_data)
    
    # Add dimension information
    enrollment_df['StudentName'] = enrollment_df['StudentKey'].apply(lambda x: students[x-1] if x <= len(students) else f'Student_{x}')
    enrollment_df['CourseTitle'] = enrollment_df['CourseKey'].apply(lambda x: courses[x-1] if x <= len(courses) else f'Course_{x}')
    enrollment_df['CategoryName'] = enrollment_df['CategoryKey'].apply(lambda x: categories[x-1] if x <= len(categories) else f'Category_{x}')
    enrollment_df['InstructorName'] = enrollment_df['InstructorKey'].apply(lambda x: instructors[x-1] if x <= len(instructors) else f'Instructor_{x}')
    enrollment_df['MembershipType'] = np.random.choice(['Premium', 'Standard', 'Basic'], 100)
    enrollment_df['CourseLevel'] = np.random.choice(['Beginner', 'Intermediate', 'Advanced'], 100)
    
    performance_df['StudentName'] = performance_df['StudentKey'].apply(lambda x: students[x-1] if x <= len(students) else f'Student_{x}')
    performance_df['CourseTitle'] = performance_df['CourseKey'].apply(lambda x: courses[x-1] if x <= len(courses) else f'Course_{x}')
    performance_df['AssessmentTitle'] = performance_df['AssessmentKey'].apply(lambda x: assessments[x-1] if x <= len(assessments) else f'Assessment_{x}')
    performance_df['AssessmentType'] = np.random.choice(['Quiz', 'Assignment', 'Exam', 'Project'], 150)
    performance_df['DifficultyLevel'] = np.random.choice(['Easy', 'Medium', 'Hard'], 150)
    
    # Convert dates
    enrollment_df['EnrollmentDate'] = pd.to_datetime('2024-08-29')
    enrollment_df['CompletionDate'] = pd.to_datetime(enrollment_df['CompletionDateKey'], format='%Y%m%d', errors='coerce')
    performance_df['SubmissionDate'] = pd.to_datetime('2024-08-29')
    
    # Calculate score percentage
    performance_df['ScorePercentage'] = (performance_df['ScoreEarned'] / performance_df['MaxPossibleScore']) * 100
    
    return enrollment_df, performance_df

def create_sidebar_filters(enrollment_df, performance_df):
    """Create sidebar filters"""
    st.sidebar.header("📊 Dashboard Filters")
    
    # Handle date range safely
    try:
        # Filter out NaT values and get valid dates
        valid_dates = enrollment_df['EnrollmentDate'].dropna()
        if len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
        else:
            # Fallback dates if no valid dates found
            min_date = pd.to_datetime('2024-08-29')
            max_date = pd.to_datetime('2024-08-29')
    except:
        # Fallback if any error occurs
        min_date = pd.to_datetime('2024-08-29')
        max_date = pd.to_datetime('2024-08-29')
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 1:
        date_range = (date_range[0], date_range[0])
    
    # Other filters with safe defaults
    try:
        categories_options = enrollment_df['CategoryName'].unique()
    except:
        categories_options = []
    
    try:
        membership_options = enrollment_df['MembershipType'].unique()
    except:
        membership_options = []
    
    categories = st.sidebar.multiselect(
        "Select Categories",
        options=categories_options,
        default=categories_options if len(categories_options) > 0 else []
    )
    
    membership_types = st.sidebar.multiselect(
        "Select Membership Types",
        options=membership_options,
        default=membership_options if len(membership_options) > 0 else []
    )
    
    return date_range, categories, membership_types

def filter_data(df, date_col, date_range, categories=None, membership_types=None):
    """Apply filters to dataframe - simplified version"""
    filtered_df = df.copy()
    
    # TEMPORARY: Skip date filtering to see if that's the issue
    # Category filter
    if categories and 'CategoryName' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CategoryName'].isin(categories)]
    
    # Membership filter
    if membership_types and 'MembershipType' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['MembershipType'].isin(membership_types)]
    
    return filtered_df

def show_data_explorer_tab(raw_data, enrollment_df, performance_df):
    """Tab 1: Data Explorer - Show raw and processed data"""
    st.header("🔍 Data Explorer - Fact Constellation Verification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Dimension Tables")
        dim_option = st.selectbox("Select Dimension Table", 
                                list(raw_data.keys()) if raw_data else [])
        if raw_data and dim_option:
            st.dataframe(raw_data[dim_option], use_container_width=True)
            st.info(f"Shape: {raw_data[dim_option].shape}")
    
    with col2:
        st.subheader("📈 Fact Tables")
        fact_option = st.selectbox("Select Fact Table", 
                                 ['FactEnrollment', 'FactAssessmentPerformance'])
        if raw_data and fact_option in raw_data:
            st.dataframe(raw_data[fact_option], use_container_width=True)
            st.info(f"Shape: {raw_data[fact_option].shape}")
    
    st.subheader("🔄 Processed Data for Analysis")
    
    tab1, tab2 = st.tabs(["Enrollment Data", "Performance Data"])
    
    with tab1:
        st.dataframe(enrollment_df, use_container_width=True)
        st.info(f"Processed Enrollment Data: {enrollment_df.shape}")
        
    with tab2:
        st.dataframe(performance_df, use_container_width=True)
        st.info(f"Processed Performance Data: {performance_df.shape}")
    
    # Schema information
    st.subheader("🏗️ Schema Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Enrollment Fact Schema:**")
        for col in enrollment_df.columns:
            st.write(f"- {col}: {enrollment_df[col].dtype}")
    
    with col2:
        st.write("**Performance Fact Schema:**")
        for col in performance_df.columns:
            st.write(f"- {col}: {performance_df[col].dtype}")

def show_enrollment_dashboard(enrollment_df):
    """Tab 2: Enrollment Dashboard"""
    st.header("📈 Enrollment Dashboard")
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Enrollments", len(enrollment_df))
    with col2: st.metric("Total Revenue", f"${enrollment_df['CoursePrice'].sum():,.2f}")
    with col3: st.metric("Avg Progress", f"{enrollment_df['ProgressPercentage'].mean():.1f}%")
    with col4: st.metric("Completion Rate", f"{(enrollment_df['CompletionStatus'] == 'Completed').mean()*100:.1f}%")
    
    # Visualizations
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(enrollment_df, names='CategoryName', title='Enrollments by Category')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(enrollment_df.groupby('MembershipType')['CoursePrice'].sum().reset_index(), 
                    x='MembershipType', y='CoursePrice', title='Revenue by Membership Type')
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(enrollment_df, x='ProgressPercentage', title='Progress Distribution')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(enrollment_df['CompletionStatus'].value_counts().reset_index(), 
                    x='CompletionStatus', y='count', title='Completion Status')
        st.plotly_chart(fig, use_container_width=True)

def show_performance_dashboard(performance_df):
    """Tab 3: Performance Dashboard"""
    st.header("🎓 Performance Dashboard")
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Avg Score", f"{performance_df['ScorePercentage'].mean():.1f}%")
    with col2: st.metric("Total Submissions", len(performance_df))
    with col3: st.metric("Avg Time Spent", f"{performance_df['TimeSpentMinutes'].mean():.0f} mins")
    with col4: st.metric("Success Rate", f"{(performance_df['ScorePercentage'] >= 70).mean()*100:.1f}%")
    
    # Visualizations
    col1, col2 = st.columns(2)
    with col1:
        fig = px.box(performance_df, x='AssessmentType', y='ScorePercentage', title='Scores by Assessment Type')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(performance_df, x='TimeSpentMinutes', y='ScorePercentage', 
                        color='DifficultyLevel', title='Time vs Score')
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(performance_df, x='ScorePercentage', title='Score Distribution')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(performance_df.groupby('DifficultyLevel')['AttemptsCount'].mean().reset_index(), 
                    x='DifficultyLevel', y='AttemptsCount', title='Attempts by Difficulty')
        st.plotly_chart(fig, use_container_width=True)

def show_integrated_analysis(enrollment_df, performance_df):
    """Tab 4: Integrated Analysis"""
    st.header("🔗 Integrated Analysis")
    
    # Merge data
    merged_df = pd.merge(
        enrollment_df[['StudentName', 'CourseTitle', 'MembershipType', 'ProgressPercentage', 'CompletionStatus']],
        performance_df.groupby(['StudentName', 'CourseTitle'])['ScorePercentage'].mean().reset_index(),
        on=['StudentName', 'CourseTitle'],
        how='inner'
    )
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(merged_df, x='ProgressPercentage', y='ScorePercentage', 
                        color='MembershipType', title='Progress vs Performance')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        success_rates = merged_df.groupby('MembershipType').agg(
            SuccessRate=('ScorePercentage', lambda x: (x >= 70).mean() * 100)
            ).reset_index()
        fig = px.bar(success_rates, x='MembershipType', y='SuccessRate', title='Success Rate by Membership')
        st.plotly_chart(fig, use_container_width=True)

def show_schema_diagram():
    """Tab 5: Display the fact constellation schema diagram"""
    st.header("🏗️ Fact Constellation Schema Diagram")
    
    # Try to load the image
    try:
        st.image("Fact constellation diagram.png", use_container_width=True)
    except:
        st.error("Could not load fact_constellation.png. Please make sure the file exists in the same directory.")

def main():
    # Main title
    st.markdown("<h1 class='main-header'>🎓 EduSkillUp Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("**Fact Constellation Analytics | Business Intelligence & Educational Quality Assurance**")
    
    # Load data
    if not st.session_state.data_loaded:
        with st.spinner("Loading data..."):
            raw_data = load_raw_data_from_csv()
            
            if raw_data:
                enrollment_df, performance_df = process_data_for_analysis(raw_data)
                if enrollment_df is None:
                    st.warning("Using sample data due to processing issues")
                    enrollment_df, performance_df = create_sample_data()
            else:
                st.warning("Using sample data due to loading issues")
                enrollment_df, performance_df = create_sample_data()
                raw_data = {}  # Empty raw data for sample case
            
            # Initialize all session state variables
            st.session_state.raw_data = raw_data
            st.session_state.enrollment_df = enrollment_df
            st.session_state.performance_df = performance_df
            st.session_state.data_loaded = True
    
    # Safe access to session state variables with default values
    raw_data = st.session_state.get('raw_data', {})
    enrollment_df = st.session_state.get('enrollment_df', pd.DataFrame())
    performance_df = st.session_state.get('performance_df', pd.DataFrame())
    
    # Data summary in sidebar
    st.sidebar.header("📊 Data Summary")
    st.sidebar.info(f"""
    - 📚 Enrollments: {len(enrollment_df):,}
    - 🎯 Assessments: {len(performance_df):,}
    - 👥 Students: {enrollment_df['StudentName'].nunique() if not enrollment_df.empty else 0:,}
    - 🏫 Courses: {enrollment_df['CourseTitle'].nunique() if not enrollment_df.empty else 0:,}
    - 📈 Categories: {enrollment_df['CategoryName'].nunique() if not enrollment_df.empty else 0:,}
    """)
    
    # Rest of your main function remains the same...    
    # Create filters
    date_range, categories, membership_types = create_sidebar_filters(enrollment_df, performance_df)
    
    # Apply filters
    filtered_enrollment = filter_data(enrollment_df, 'EnrollmentDate', date_range, categories, membership_types)
    filtered_performance = filter_data(performance_df, 'SubmissionDate', date_range, categories, membership_types)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Data Explorer", 
        "📈 Enrollment Dashboard", 
        "🎓 Performance Dashboard", 
        "🔗 Integrated Analysis",
        "🏗️ Schema Diagram"  # New tab
    ])
    
    with tab1:
        show_data_explorer_tab(raw_data, filtered_enrollment, filtered_performance)
    
    with tab2:
        show_enrollment_dashboard(filtered_enrollment)
    
    with tab3:
        show_performance_dashboard(filtered_performance)
    
    with tab4:
        show_integrated_analysis(filtered_enrollment, filtered_performance)

    with tab5:
        show_schema_diagram()
    
    # Footer
    st.markdown("---")
    st.markdown("**EduSkillUp Fact Constellation Dashboard** | TMV6014 Advanced Databases Project")

if __name__ == "__main__":
    main()
