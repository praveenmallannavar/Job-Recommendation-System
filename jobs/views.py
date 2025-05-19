import pandas as pd
import re
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import ResumeForm

# Load the CSV files globally
jobs_df = pd.read_csv(settings.BASE_DIR / 'jobs.csv')
job_search_df = pd.read_csv(settings.BASE_DIR / 'job_details (2) (5).csv')

def extract_skills(resume_text):
    skills_section = re.search(r'Skills(.*?)(Experience|Education|$)', resume_text, re.DOTALL)
    if skills_section:
        skills_text = skills_section.group(1)
        skills_list = re.split(r',|\n', skills_text)
        skills = [skill.strip().lower() for skill in skills_list if skill.strip()]
        return set(skills)
    return set()

def recommend_job(resume_skills, jobs_df):
    jobs_df['Key Skills'] = jobs_df['Key Skills'].apply(lambda x: set(skill.strip().lower() for skill in x.split('|')))
    jobs_df['Match Score'] = jobs_df['Key Skills'].apply(lambda job_skills: len(resume_skills & job_skills))
    best_match = jobs_df.loc[jobs_df['Match Score'].idxmax()]
    return best_match['Job Title'], best_match['Match Score']

def index(request):
    return render(request, 'jobs/index.html')

def upload_resume(request):
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            file_path = form.instance.file.path
            with open(file_path, 'r') as file:
                resume_text = file.read()
            resume_skills = extract_skills(resume_text)
            recommended_job_title, match_score = recommend_job(resume_skills, jobs_df)
            matching_jobs = job_search_df[job_search_df['Job Title'] == recommended_job_title]

            # Convert dictionary keys to dot-notation friendly keys
            matching_jobs = matching_jobs.rename(columns=lambda x: x.replace(' ', '_'))

            context = {
                'jobs': matching_jobs.to_dict(orient='records'),
                'recommended_job_title': recommended_job_title,
                'match_score': match_score
            }
            return render(request, 'jobs/upload.html', context)
    else:
        form = ResumeForm()
    return render(request, 'jobs/upload.html', {'form': form})
