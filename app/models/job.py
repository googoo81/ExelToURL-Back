import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

class JobManager:
    """Manages job tracking for asynchronous URL validation and analysis tasks"""
    
    def __init__(self):
        self.jobs = {}
    
    def create_job(self, job_id, urls, job_type="standard"):
        """Initialize a new job with the given parameters"""
        job_data = {
            'status': 'in_progress',
            'total': len(urls),
            'completed': 0,
            'results': [],
            'urls': urls,
            'created_at': time.time(),
            'job_type': job_type
        }
        
        # Add specific counters for XML analysis jobs
        if job_type == "xml_analysis":
            job_data['type_counts'] = Counter()
            job_data['style_counts'] = Counter()
            job_data['tag_counts'] = {
                'course_code': Counter(),
                'grade': Counter(),
                'session': Counter(),
                'unit': Counter(),
                'period': Counter(),
                'order': Counter(),
                'study': Counter()
            }
            
        self.jobs[job_id] = job_data
        return job_data
    
    def get_job(self, job_id):
        """Retrieve job data by ID"""
        return self.jobs.get(job_id)
    
    def update_job_progress(self, job_id, result):
        """Update job progress with a new result"""
        if job_id not in self.jobs:
            return False
            
        self.jobs[job_id]['results'].append(result)
        self.jobs[job_id]['completed'] += 1
        
        return True
    
    def update_type_counts(self, job_id, type_value):
        """Update type counts for XML analysis jobs"""
        if job_id in self.jobs and 'type_counts' in self.jobs[job_id] and type_value:
            self.jobs[job_id]['type_counts'][type_value] += 1
            return True
        return False
    
    def update_style_counts(self, job_id, style_content):
        """Update style counts for XML analysis jobs"""
        if job_id in self.jobs and 'style_counts' in self.jobs[job_id] and style_content:
            self.jobs[job_id]['style_counts'][style_content] += 1
            return True
        return False
    
    def update_tag_counts(self, job_id, tag_name, tag_value):
        """Update counts for specific XML tags"""
        if (job_id in self.jobs and 
            'tag_counts' in self.jobs[job_id] and 
            tag_name in self.jobs[job_id]['tag_counts'] and 
            tag_value):
            self.jobs[job_id]['tag_counts'][tag_name][tag_value] += 1
            return True
        return False
    
    def complete_job(self, job_id):
        """Mark a job as completed"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'completed'
            return True
        return False
    
    def cleanup_old_jobs(self, hours):
        """Remove jobs older than the specified number of hours"""
        current_time = time.time()
        expired_jobs = []
        
        for job_id, job_data in self.jobs.items():
            if current_time - job_data.get('created_at', 0) > (hours * 3600):
                expired_jobs.append(job_id)
                
        for job_id in expired_jobs:
            del self.jobs[job_id]
            
        return len(expired_jobs)

# Singleton instance
job_manager = JobManager()